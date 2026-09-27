from typing import Dict, Any, Tuple
import torch
import numpy as np

def top_k_sparsify(
    weights_dict: Dict[str, torch.Tensor],
    k_percent: float = 20.0
) -> Tuple[Dict[str, torch.Tensor], Dict[str, Any]]:
    """
    Top-k Gradient Sparsification (Section 31):
      Keeps only the top k% largest magnitude weight updates and sets the remaining (100 - k)% to 0.
    """
    sparsified: Dict[str, torch.Tensor] = {}
    total_elements = 0
    kept_elements = 0

    for key, val in weights_dict.items():
        if not val.is_floating_point():
            sparsified[key] = val.clone()
            continue

        tensor = val.clone().float()
        numel = tensor.numel()
        total_elements += numel

        k = max(1, int(numel * (k_percent / 100.0)))
        kept_elements += k

        # Flatten and find top-k threshold
        flat = tensor.abs().view(-1)
        if k < numel:
            topk_vals, _ = torch.topk(flat, k)
            threshold = topk_vals[-1]
            mask = tensor.abs() >= threshold
            sparsified[key] = tensor * mask.float()
        else:
            sparsified[key] = tensor

    sparsity_ratio = round(1.0 - (kept_elements / max(1, total_elements)), 4)
    # Original: 4 bytes per float32. Sparse: 4 bytes value + 2 bytes index per non-zero
    original_bytes = total_elements * 4
    compressed_bytes = int(kept_elements * 6)

    return sparsified, {
        "method": "top_k_sparsification",
        "k_percent": k_percent,
        "total_parameters": total_elements,
        "transmitted_parameters": kept_elements,
        "sparsity_ratio": sparsity_ratio,
        "original_bytes": original_bytes,
        "compressed_bytes": compressed_bytes,
        "compression_ratio": round(original_bytes / max(1, compressed_bytes), 2),
        "savings_percent": round((1.0 - compressed_bytes / max(1, original_bytes)) * 100.0, 2)
    }

def quantize_8bit(
    weights_dict: Dict[str, torch.Tensor]
) -> Tuple[Dict[str, torch.Tensor], Dict[str, Any]]:
    """
    8-Bit Linear Quantization (Section 31):
      Quantizes 32-bit floats to 8-bit unsigned integers:
        q = round((x - min) / (max - min) * 255)
      Reconstructs on server: x_hat = min + (q / 255) * (max - min)
    """
    quantized_and_reconstructed: Dict[str, torch.Tensor] = {}
    total_elements = 0
    total_squared_error = 0.0

    for key, val in weights_dict.items():
        if not val.is_floating_point():
            quantized_and_reconstructed[key] = val.clone()
            continue

        tensor = val.clone().float()
        total_elements += tensor.numel()

        min_val = tensor.min().item()
        max_val = tensor.max().item()
        scale = max_val - min_val

        if scale < 1e-7:
            quantized_and_reconstructed[key] = tensor
            continue

        # Quantize to 8-bit [0, 255]
        q = torch.clamp(torch.round((tensor - min_val) / scale * 255.0), 0, 255)
        # Dequantize back to float32
        recon = min_val + (q / 255.0) * scale

        error = torch.sum((tensor - recon) ** 2).item()
        total_squared_error += error
        quantized_and_reconstructed[key] = recon

    mse = round(total_squared_error / max(1, total_elements), 6)
    # 32 bits (4 bytes) -> 8 bits (1 byte) + 8 bytes min/max metadata
    original_bytes = total_elements * 4
    compressed_bytes = total_elements * 1 + 64  # 1 byte per weight + small header

    return quantized_and_reconstructed, {
        "method": "8bit_quantization",
        "total_parameters": total_elements,
        "bits_per_parameter": 8,
        "reconstruction_mse": mse,
        "original_bytes": original_bytes,
        "compressed_bytes": compressed_bytes,
        "compression_ratio": round(original_bytes / max(1, compressed_bytes), 2),
        "savings_percent": round((1.0 - compressed_bytes / max(1, original_bytes)) * 100.0, 2)
    }

def compress_and_benchmark(
    weights_dict: Dict[str, torch.Tensor],
    method: str = "combined",
    k_percent: float = 20.0
) -> Tuple[Dict[str, torch.Tensor], Dict[str, Any]]:
    """
    Compress model update weights using selected optimization method (Section 31):
      - 'none': Raw 32-bit floating point transmission
      - 'top_k': Top-k magnitude sparsification
      - 'quantize_8bit': 8-bit uniform quantization
      - 'combined': Top-k sparsification followed by 8-bit quantization
    """
    if method == "top_k":
        return top_k_sparsify(weights_dict, k_percent=k_percent)

    elif method == "quantize_8bit":
        return quantize_8bit(weights_dict)

    elif method == "combined":
        # 1. Sparsify first
        sparse_w, s_meta = top_k_sparsify(weights_dict, k_percent=k_percent)
        # 2. Quantize non-zero weights (1 byte value + 2 bytes index = 3 bytes per transmitted weight)
        recon_w, q_meta = quantize_8bit(sparse_w)

        total_elements = s_meta["total_parameters"]
        kept = s_meta["transmitted_parameters"]
        original_bytes = total_elements * 4
        compressed_bytes = int(kept * 3 + 64)

        return recon_w, {
            "method": "combined_compression",
            "k_percent": k_percent,
            "total_parameters": total_elements,
            "transmitted_parameters": kept,
            "sparsity_ratio": s_meta["sparsity_ratio"],
            "reconstruction_mse": q_meta["reconstruction_mse"],
            "original_bytes": original_bytes,
            "compressed_bytes": compressed_bytes,
            "compression_ratio": round(original_bytes / max(1, compressed_bytes), 2),
            "savings_percent": round((1.0 - compressed_bytes / max(1, original_bytes)) * 100.0, 2)
        }

    else:
        # None: baseline transmission
        total_elements = sum(v.numel() for v in weights_dict.values() if v.is_floating_point())
        b = total_elements * 4
        return weights_dict, {
            "method": "none",
            "total_parameters": total_elements,
            "original_bytes": b,
            "compressed_bytes": b,
            "compression_ratio": 1.0,
            "savings_percent": 0.0
        }
