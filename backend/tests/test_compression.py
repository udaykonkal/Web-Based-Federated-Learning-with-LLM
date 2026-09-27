import pytest
import torch
from httpx import AsyncClient
from app.services.compression_service import (
    top_k_sparsify,
    quantize_8bit,
    compress_and_benchmark
)

def test_top_k_sparsification():
    """
    Test Section 31 top-k sparsification maintains only top k% parameter magnitudes.
    """
    weights = {"layer1": torch.linspace(-1.0, 1.0, 100)}
    sparse_w, meta = top_k_sparsify(weights, k_percent=20.0)

    tensor = sparse_w["layer1"]
    non_zero = (tensor != 0.0).sum().item()

    assert non_zero == 20
    assert meta["sparsity_ratio"] == 0.80
    assert meta["savings_percent"] > 60.0

def test_8bit_quantization():
    """
    Test Section 31 8-bit uniform quantization and server-side reconstruction fidelity.
    """
    weights = {"layer1": torch.sin(torch.linspace(0, 3.14, 1000))}
    recon_w, meta = quantize_8bit(weights)

    tensor = weights["layer1"]
    recon = recon_w["layer1"]

    mse = torch.mean((tensor - recon) ** 2).item()
    assert mse < 0.001
    assert meta["compression_ratio"] >= 3.0
    assert meta["savings_percent"] >= 70.0

def test_combined_compression():
    """
    Test Section 31 combined top-k sparsification and 8-bit quantization.
    """
    weights = {"fc": torch.randn(50, 50)}  # 2500 parameters
    compressed_w, meta = compress_and_benchmark(weights, method="combined", k_percent=15.0)

    assert meta["method"] == "combined_compression"
    assert meta["compression_ratio"] > 4.0
    assert meta["savings_percent"] > 80.0

@pytest.mark.asyncio
async def test_communication_stats_and_benchmark_api(async_client: AsyncClient):
    """
    Test Admin Communication REST endpoints for bandwidth stats and live benchmark.
    """
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flplatform.org", "password": "admin123"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # 1. Bandwidth stats
    stats_res = await async_client.get("/api/v1/admin/communication/stats", headers=admin_headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_original_mb" in stats
    assert "bandwidth_reduction_percent" in stats
    assert "client_breakdown" in stats

    # 2. Live benchmark
    bench_res = await async_client.post(
        "/api/v1/admin/communication/benchmark-compression",
        json={"method": "combined", "k_percent": 20.0, "task": "diabetes_prediction"},
        headers=admin_headers
    )
    assert bench_res.status_code == 200
    bench = bench_res.json()
    assert bench["compression_ratio"] > 1.0
    assert bench["savings_percent"] > 50.0
