import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { 
  Network, 
  ArrowDownCircle, 
  Cpu, 
  Play, 
  Building2, 
  Gauge
} from 'lucide-react';

interface ClientCommStats {
  name: string;
  original_kb: number;
  compressed_kb: number;
  saved_kb: number;
  savings_percent: number;
}

interface CommunicationStats {
  total_updates_transmitted: number;
  total_original_mb: number;
  total_compressed_mb: number;
  bandwidth_saved_mb: number;
  bandwidth_reduction_percent: number;
  average_compression_ratio: number;
  supported_techniques: string[];
  client_breakdown: Record<string, ClientCommStats>;
}

interface BenchmarkResult {
  method: string;
  k_percent?: number;
  total_parameters: number;
  transmitted_parameters?: number;
  sparsity_ratio?: number;
  reconstruction_mse?: number;
  original_bytes: number;
  compressed_bytes: number;
  compression_ratio: number;
  savings_percent: number;
}

export const AdminCommunication: React.FC = () => {
  const [stats, setStats] = useState<CommunicationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Benchmark controls
  const [method, setMethod] = useState<'combined' | 'top_k' | 'quantize_8bit'>('combined');
  const [kPercent, setKPercent] = useState(20.0);
  const [task] = useState('diabetes_prediction');
  const [benchmarking, setBenchmarking] = useState(false);
  const [benchmarkResult, setBenchmarkResult] = useState<BenchmarkResult | null>(null);

  const fetchStats = async () => {
    try {
      const res = await api.get<CommunicationStats>('/admin/communication/stats');
      setStats(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch communication stats.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleRunBenchmark = async () => {
    setBenchmarking(true);
    setError(null);
    try {
      const res = await api.post<BenchmarkResult>('/admin/communication/benchmark-compression', {
        method,
        k_percent: kPercent,
        task
      });
      setBenchmarkResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to benchmark compression.');
    } finally {
      setBenchmarking(false);
    }
  };

  const getMethodTitle = (m: string) => {
    switch (m) {
      case 'top_k': return 'Top-k Magnitude Sparsification';
      case 'quantize_8bit': return '8-Bit Uniform Quantization';
      case 'combined': return 'Combined Sparsification & 8-Bit Quantization';
      default: return m;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-16">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="card p-6 bg-white border border-slate-200 rounded-xl shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-sky-700 text-xs font-semibold uppercase tracking-wider mb-1">
            <Network className="w-4 h-4 text-sky-600" />
            <span>Phase 10: Communication Optimization</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Network Compression & Bandwidth Optimization
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Reduces distributed communication overhead via Top-k gradient sparsification and 8-bit quantization with minimal loss in global model accuracy.
          </p>
        </div>

        <div className="badge-sky flex items-center space-x-2 px-3 py-1.5 rounded-lg shadow-xs">
          <Gauge className="w-4 h-4 text-sky-600" />
          <span>Active Policy: Combined Compression</span>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
          {error}
        </div>
      )}

      {/* Top KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase">Uncompressed Baseline</span>
          <p className="text-2xl font-bold font-mono text-slate-700">
            {stats ? `${stats.total_original_mb.toFixed(2)} MB` : '0.00 MB'}
          </p>
          <span className="text-[10px] text-slate-400">32-bit Float Parameters</span>
        </div>

        <div className="card p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase">Compressed Network Footprint</span>
          <p className="text-2xl font-bold font-mono text-sky-700">
            {stats ? `${stats.total_compressed_mb.toFixed(2)} MB` : '0.00 MB'}
          </p>
          <span className="text-[10px] text-sky-600">Actual transmitted bytes</span>
        </div>

        <div className="card p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase">Bandwidth Saved</span>
          <p className="text-2xl font-bold font-mono text-emerald-700">
            {stats ? `${stats.bandwidth_saved_mb.toFixed(2)} MB` : '0.00 MB'}
          </p>
          <span className="text-[10px] text-emerald-600">Conserved clinical network capacity</span>
        </div>

        <div className="card p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase">Overall Compression Ratio</span>
          <p className="text-2xl font-bold font-mono text-indigo-700">
            {stats ? `${stats.average_compression_ratio}x` : '1.0x'}
          </p>
          <span className="text-[10px] text-slate-500 font-mono">
            {stats ? `${stats.bandwidth_reduction_percent.toFixed(1)}% reduction` : '0%'}
          </span>
        </div>
      </div>

      {/* Interactive Compression Benchmarking Laboratory */}
      <div className="card p-6 bg-white rounded-xl border border-slate-200 shadow-xs space-y-6">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div className="flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-sky-600" />
            <h2 className="text-sm font-bold text-slate-900">
              Interactive Compression Benchmarking Laboratory (Section 31)
            </h2>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            Test real PyTorch tensor compression algorithms on authentic gradient updates
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-slate-600 font-semibold block text-xs mb-1.5">Compression Technique</label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value as any)}
              className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 text-xs font-mono focus:border-sky-500 focus:outline-hidden"
            >
              <option value="combined">Combined (Top-k + Quantization)</option>
              <option value="top_k">Top-k Sparsification</option>
              <option value="quantize_8bit">8-Bit Uniform Quantization</option>
            </select>
          </div>

          <div>
            <label className="text-slate-600 font-semibold block text-xs mb-1.5">
              Sparsity Ratio (k = {kPercent}%)
            </label>
            <input
              type="range"
              min="5"
              max="80"
              step="5"
              disabled={method === 'quantize_8bit'}
              value={kPercent}
              onChange={(e) => setKPercent(parseFloat(e.target.value))}
              className="w-full mt-2 disabled:opacity-40"
            />
          </div>

          <div className="flex items-center text-xs text-slate-500 pt-3">
            <span>
              {method === 'quantize_8bit' && 'Quantizes 32-bit floats into 8-bit integers (75% theoretical reduction).'}
              {method === 'top_k' && `Transmits only top ${kPercent}% largest magnitude coordinates.`}
              {method === 'combined' && `Retains top ${kPercent}% weights, then quantizes non-zeros to 8-bit.`}
            </span>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleRunBenchmark}
              disabled={benchmarking}
              className="btn-kaggle w-full justify-center shadow-xs"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{benchmarking ? 'Compressing Tensors...' : 'Run Compression Benchmark'}</span>
            </button>
          </div>
        </div>

        {/* Live Benchmark Visualizer */}
        {benchmarkResult && (
          <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200">
              <div className="flex items-center space-x-2">
                <ArrowDownCircle className="w-5 h-5 text-emerald-600" />
                <div>
                  <h3 className="text-xs font-bold text-slate-900">
                    Benchmark Results: {getMethodTitle(benchmarkResult.method)}
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    Evaluated across <strong className="text-slate-900 font-mono">{benchmarkResult.total_parameters}</strong> PyTorch model parameters
                  </p>
                </div>
              </div>

              <span className="badge-emerald font-mono text-xs">
                SAVINGS: {benchmarkResult.savings_percent}% ({benchmarkResult.compression_ratio}x Reduction)
              </span>
            </div>

            {/* Payload Size Bar Comparison */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-500">Uncompressed (Float32):</span>
                <span className="text-slate-700">{(benchmarkResult.original_bytes / 1024).toFixed(2)} KB</span>
              </div>
              <div className="w-full bg-slate-200 h-3 rounded-full overflow-hidden">
                <div className="bg-slate-400 h-full w-full rounded-full"></div>
              </div>

              <div className="flex justify-between text-xs font-mono pt-1">
                <span className="text-sky-700 font-semibold">Optimized Transmission:</span>
                <span className="text-sky-700 font-bold">{(benchmarkResult.compressed_bytes / 1024).toFixed(2)} KB</span>
              </div>
              <div className="w-full bg-slate-200 h-3 rounded-full overflow-hidden">
                <div 
                  className="bg-sky-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.max(5, 100 - benchmarkResult.savings_percent)}%` }}
                ></div>
              </div>
            </div>

            {/* Diagnostics Matrix */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs font-mono">
              <div className="p-3 rounded-lg bg-white border border-slate-200 shadow-xs">
                <span className="text-[10px] text-slate-500 uppercase block">Compression Ratio</span>
                <span className="text-sm font-bold text-slate-900">{benchmarkResult.compression_ratio}x</span>
              </div>
              <div className="p-3 rounded-lg bg-white border border-slate-200 shadow-xs">
                <span className="text-[10px] text-slate-500 uppercase block">Bandwidth Saved</span>
                <span className="text-sm font-bold text-emerald-700">{benchmarkResult.savings_percent}%</span>
              </div>
              <div className="p-3 rounded-lg bg-white border border-slate-200 shadow-xs">
                <span className="text-[10px] text-slate-500 uppercase block">Sparsity Ratio</span>
                <span className="text-sm font-bold text-sky-700">
                  {benchmarkResult.sparsity_ratio !== undefined ? `${(benchmarkResult.sparsity_ratio * 100).toFixed(0)}%` : '0%'}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-white border border-slate-200 shadow-xs">
                <span className="text-[10px] text-slate-500 uppercase block">Reconstruction MSE</span>
                <span className="text-sm font-bold text-indigo-700">
                  {benchmarkResult.reconstruction_mse !== undefined ? benchmarkResult.reconstruction_mse.toFixed(6) : '0.000000'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Hospital Network Transmission Savings Table */}
      <div className="card p-6 bg-white rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div className="flex items-center space-x-2">
            <Building2 className="w-4 h-4 text-sky-600" />
            <h2 className="text-sm font-bold text-slate-900">
              Participating Hospital Node Bandwidth Savings (Zero Raw Record Leakage)
            </h2>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            Optimized payload per clinical endpoint
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 text-[11px]">
                <th className="p-2.5 font-semibold">Clinical Client Node</th>
                <th className="p-2.5 font-semibold">Raw Float32 Volume</th>
                <th className="p-2.5 font-semibold">Compressed Volume</th>
                <th className="p-2.5 font-semibold">Data Volume Conserved</th>
                <th className="p-2.5 text-right font-semibold">Bandwidth Reduction</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {stats && Object.entries(stats.client_breakdown).map(([cid, client]) => (
                <tr key={cid} className="hover:bg-slate-50/50 transition-colors">
                  <td className="p-2.5 flex items-center space-x-2">
                    <Building2 className="w-3.5 h-3.5 text-sky-600" />
                    <div>
                      <span className="font-bold text-slate-900 block">{client.name}</span>
                      <span className="text-[10px] text-slate-400 font-normal">{cid.toUpperCase()}</span>
                    </div>
                  </td>
                  <td className="p-2.5 text-slate-600">
                    {client.original_kb.toFixed(1)} KB
                  </td>
                  <td className="p-2.5 text-sky-700 font-bold">
                    {client.compressed_kb.toFixed(1)} KB
                  </td>
                  <td className="p-2.5 text-emerald-700 font-bold">
                    {client.saved_kb.toFixed(1)} KB
                  </td>
                  <td className="p-2.5 text-right">
                    <span className="badge-emerald font-bold">
                      {client.savings_percent.toFixed(1)}% Saved
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

