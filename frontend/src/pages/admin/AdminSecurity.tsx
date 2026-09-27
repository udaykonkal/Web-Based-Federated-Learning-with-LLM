import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { 
  ShieldAlert, 
  ShieldCheck, 
  Play, 
  Building2, 
  Sliders, 
  Info 
} from 'lucide-react';

interface SecurityOverview {
  total_screened_updates: number;
  total_rejected_updates: number;
  total_accepted_updates: number;
  rejection_rate_percent: number;
  defense_policy: string;
  thresholds: {
    norm_threshold: number;
    cosine_threshold: number;
    anomaly_threshold: number;
  };
  recent_screened_updates: Array<{
    id: number;
    round_id: number;
    client_id: string;
    update_norm: number;
    anomaly_score: number;
    is_rejected: boolean;
    created_at: string;
  }>;
}

interface ScreenedNode {
  client_id: string;
  update_norm: number;
  cosine_similarity: number;
  distance_to_median: number;
  anomaly_score: number;
  is_rejected: boolean;
  rejection_reason: string | null;
  security_action: string;
}

interface SimulationResult {
  simulated_attack: {
    attacker_client: string;
    attack_type: string;
    severity: number;
    detected: boolean;
    action_taken: string;
    anomaly_score: number;
    rejection_reason: string | null;
  };
  all_screened_nodes: ScreenedNode[];
}

export const AdminSecurity: React.FC = () => {
  const [overview, setOverview] = useState<SecurityOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Attack simulation controls
  const [targetClient, setTargetClient] = useState('client_3');
  const [attackType, setAttackType] = useState('sign_flipping');
  const [severity, setSeverity] = useState(1.0);
  const [task] = useState('diabetes_prediction');
  const [simulating, setSimulating] = useState(false);
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);

  const fetchOverview = async () => {
    try {
      const res = await api.get<SecurityOverview>('/admin/security/overview');
      setOverview(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch security overview.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const handleSimulateAttack = async () => {
    setSimulating(true);
    setError(null);
    try {
      const res = await api.post<SimulationResult>('/admin/security/simulate-attack', {
        client_id: targetClient,
        attack_type: attackType,
        severity: severity,
        task: task
      });
      setSimulationResult(res.data);
      await fetchOverview();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to simulate adversarial attack.');
    } finally {
      setSimulating(false);
    }
  };

  const getAttackName = (type: string) => {
    switch (type) {
      case 'sign_flipping': return 'Sign-Flipping (Gradient Inversion)';
      case 'gaussian_noise': return 'Gaussian Noise Injection';
      case 'scaling': return 'Extreme Magnitude Scaling';
      case 'free_rider': return 'Free-Rider (Zero Delta)';
      default: return type;
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
          <div className="flex items-center space-x-2 text-rose-700 text-xs font-semibold uppercase tracking-wider mb-1">
            <ShieldAlert className="w-4 h-4 text-rose-600" />
            <span>Phase 9: Security & Anomaly Detection</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Adversarial Defense & Update Verification Engine
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time mathematical screening defending central FedAvg aggregation against sign-flipping, Gaussian noise, and poisoned client gradients.
          </p>
        </div>

        <div className="badge-emerald flex items-center space-x-2 px-3 py-1.5 rounded-lg shadow-xs">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Active Defense: Mathematical Screening</span>
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
          <span className="text-[10px] font-semibold text-slate-500 uppercase">Total Updates Screened</span>
          <p className="text-2xl font-bold font-mono text-slate-900">
            {overview?.total_screened_updates || 0}
          </p>
          <span className="text-[10px] text-slate-400">Across all FL rounds</span>
        </div>

        <div className="card p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase">Accepted Updates</span>
          <p className="text-2xl font-bold font-mono text-emerald-700">
            {overview?.total_accepted_updates || 0}
          </p>
          <span className="text-[10px] text-emerald-600">Aggregated via FedAvg</span>
        </div>

        <div className="card p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase">Blocked / Rejected Updates</span>
          <p className="text-2xl font-bold font-mono text-rose-700">
            {overview?.total_rejected_updates || 0}
          </p>
          <span className="text-[10px] text-rose-600">Zero poisoned parameters accepted</span>
        </div>

        <div className="card p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase">Rejection Rate</span>
          <p className="text-2xl font-bold font-mono text-indigo-700">
            {overview?.rejection_rate_percent.toFixed(1)}%
          </p>
          <span className="text-[10px] text-slate-400">Anomaly filtering ratio</span>
        </div>
      </div>

      {/* Interactive Adversarial Attack Simulator */}
      <div className="card p-6 bg-white rounded-xl border border-slate-200 shadow-xs space-y-6">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div className="flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-sky-600" />
            <h2 className="text-sm font-bold text-slate-900">
              Interactive Attack Simulation & Defense Demonstrator (Section 30)
            </h2>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            Simulate real poisoned updates to verify automated defense
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-slate-600 font-semibold block text-xs mb-1.5">Designated Adversary Node</label>
            <select
              value={targetClient}
              onChange={(e) => setTargetClient(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 text-xs font-mono focus:border-sky-500 focus:outline-hidden"
            >
              <option value="client_3">Hospital C (Client 3) - Adversary</option>
              <option value="client_2">Hospital B (Client 2) - Adversary</option>
              <option value="client_1">Hospital A (Client 1) - Adversary</option>
            </select>
          </div>

          <div>
            <label className="text-slate-600 font-semibold block text-xs mb-1.5">Attack Vector</label>
            <select
              value={attackType}
              onChange={(e) => setAttackType(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 text-xs font-mono focus:border-sky-500 focus:outline-hidden"
            >
              <option value="sign_flipping">Sign-Flipping (-γ · ΔW)</option>
              <option value="gaussian_noise">Gaussian Noise (N(0, σ²))</option>
              <option value="scaling">Extreme Scaling (β · ΔW)</option>
              <option value="free_rider">Free-Rider (0 · ΔW)</option>
            </select>
          </div>

          <div>
            <label className="text-slate-600 font-semibold block text-xs mb-1.5">
              Severity / Magnitude ({severity}x)
            </label>
            <input
              type="range"
              min="0.5"
              max="3.0"
              step="0.5"
              value={severity}
              onChange={(e) => setSeverity(parseFloat(e.target.value))}
              className="w-full mt-2"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={handleSimulateAttack}
              disabled={simulating}
              className="w-full py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 disabled:bg-slate-200 text-white font-semibold text-xs flex items-center justify-center space-x-1.5 shadow-xs cursor-pointer transition-all"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{simulating ? 'Simulating & Screening...' : 'Launch Attack Simulation'}</span>
            </button>
          </div>
        </div>

        {/* Live Simulation Response */}
        {simulationResult && (
          <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200">
              <div className="flex items-center space-x-2">
                {simulationResult.simulated_attack.detected ? (
                  <ShieldAlert className="w-5 h-5 text-rose-600" />
                ) : (
                  <ShieldCheck className="w-5 h-5 text-emerald-600" />
                )}
                <div>
                  <h3 className="text-xs font-bold text-slate-900">
                    Simulation Defense Verdict: {simulationResult.simulated_attack.detected ? 'ATTACK DETECTED & INTERCEPTED' : 'CLEAN UPDATE ACCEPTED'}
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    Vector: <strong className="text-slate-900">{getAttackName(simulationResult.simulated_attack.attack_type)}</strong> on <span className="font-mono text-sky-700 font-semibold">{simulationResult.simulated_attack.attacker_client}</span>
                  </p>
                </div>
              </div>

              <span className={`text-xs font-bold font-mono px-3 py-1 rounded-full ${
                simulationResult.simulated_attack.action_taken === 'REJECTED'
                  ? 'bg-rose-50 text-rose-700 border border-rose-200'
                  : simulationResult.simulated_attack.action_taken === 'DOWN_WEIGHTED'
                  ? 'bg-amber-50 text-amber-700 border border-amber-200'
                  : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              }`}>
                ACTION: {simulationResult.simulated_attack.action_taken}
              </span>
            </div>

            {simulationResult.simulated_attack.rejection_reason && (
              <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start space-x-2">
                <Info className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
                <span>{simulationResult.simulated_attack.rejection_reason}</span>
              </div>
            )}

            {/* Screened Nodes Breakdown Table */}
            <div className="overflow-x-auto bg-white rounded-lg border border-slate-200 shadow-xs">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 text-[11px]">
                    <th className="p-2.5 font-semibold">Client Hospital</th>
                    <th className="p-2.5 font-semibold">L₂ Update Norm (||ΔW||₂)</th>
                    <th className="p-2.5 font-semibold">Cosine Sim (cos(ΔW, ΔW_med))</th>
                    <th className="p-2.5 font-semibold">Dist to Median (d_k)</th>
                    <th className="p-2.5 font-semibold">Anomaly Score (α_k)</th>
                    <th className="p-2.5 text-right font-semibold">Defense Verdict</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {simulationResult.all_screened_nodes.map((node) => {
                    const isAttacker = node.client_id === simulationResult.simulated_attack.attacker_client;
                    return (
                      <tr key={node.client_id} className={isAttacker ? 'bg-rose-50/50' : 'hover:bg-slate-50/50'}>
                        <td className="p-2.5 flex items-center space-x-2">
                          <Building2 className={`w-3.5 h-3.5 ${isAttacker ? 'text-rose-600' : 'text-sky-600'}`} />
                          <span className={`font-bold ${isAttacker ? 'text-rose-900' : 'text-slate-900'}`}>
                            {node.client_id === 'client_1' ? 'Hospital A' : node.client_id === 'client_2' ? 'Hospital B' : 'Hospital C'}
                            {isAttacker && ' (Simulated Poison)'}
                          </span>
                        </td>
                        <td className="p-2.5 text-slate-700">
                          {node.update_norm.toFixed(4)}
                        </td>
                        <td className="p-2.5">
                          <span className={node.cosine_similarity < 0 ? 'text-rose-600 font-bold' : 'text-slate-700'}>
                            {node.cosine_similarity.toFixed(4)}
                          </span>
                        </td>
                        <td className="p-2.5 text-slate-700">
                          {node.distance_to_median.toFixed(4)}
                        </td>
                        <td className="p-2.5">
                          <span className={node.anomaly_score > 0.55 ? 'text-rose-600 font-bold' : 'text-emerald-700'}>
                            {node.anomaly_score.toFixed(4)}
                          </span>
                        </td>
                        <td className="p-2.5 text-right">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            node.security_action === 'REJECTED'
                              ? 'badge-rose'
                              : node.security_action === 'DOWN_WEIGHTED'
                              ? 'badge-amber'
                              : 'badge-emerald'
                          }`}>
                            {node.security_action}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Security Screening Parameters & Thresholds */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-1.5 text-xs">
          <span className="text-[10px] font-bold text-slate-500 uppercase">1. L₂ Update Norm Bound</span>
          <p className="text-slate-900 font-mono text-sm font-bold">||ΔW_k||₂ ≤ 5.0</p>
          <p className="text-slate-500 text-[11px] leading-relaxed">
            Rejects updates with extreme gradient magnitudes to prevent gradient explosion and free-rider scaling attacks.
          </p>
        </div>

        <div className="card p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-1.5 text-xs">
          <span className="text-[10px] font-bold text-slate-500 uppercase">2. Directional Cosine Similarity</span>
          <p className="text-slate-900 font-mono text-sm font-bold">cos(ΔW_k, ΔW_med) ≥ -0.10</p>
          <p className="text-slate-500 text-[11px] leading-relaxed">
            Screens angle against coordinate-wise median update; automatically flags and blocks sign-flipping and opposite direction updates.
          </p>
        </div>

        <div className="card p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-1.5 text-xs">
          <span className="text-[10px] font-bold text-slate-500 uppercase">3. Composite Anomaly Threshold</span>
          <p className="text-slate-900 font-mono text-sm font-bold">α_k ≤ 0.55</p>
          <p className="text-slate-500 text-[11px] leading-relaxed">
            Weighs norm ratio (35%), inverted cosine similarity (40%), and Euclidean distance to median (25%). Updates above 0.55 are rejected.
          </p>
        </div>
      </div>
    </div>
  );
};

