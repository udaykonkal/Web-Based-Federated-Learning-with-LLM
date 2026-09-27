import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { 
  FlaskConical, 
  Plus, 
  Play, 
  FastForward, 
  CheckCircle2, 
  AlertCircle, 
  Layers, 
  TrendingUp, 
  Building2,
  X,
  RotateCcw,
  Users,
  Trash2
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

interface FLRound {
  id: number;
  experiment_id: number;
  round_number: number;
  status: string;
  global_loss: number | null;
  global_accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  participating_clients: string[];
  aggregation_metrics: {
    total_samples?: number;
    num_participating_clients?: number;
    client_weights?: Record<string, number>;
    aggregated_l2_norm?: number;
    aggregation_strategy?: string;
  };
  started_at: string;
  completed_at: string | null;
}

interface Experiment {
  id: number;
  name: string;
  healthcare_task: string;
  model_id: number;
  model_name: string | null;
  status: string;
  current_round: number;
  total_rounds: number;
  strategy: string;
  local_epochs: number;
  learning_rate: number;
  batch_size: number;
  final_accuracy: number | null;
  final_loss: number | null;
  created_at: string;
  rounds: FLRound[];
}

interface PublishedModel {
  id: number;
  name: string;
  healthcare_task: string;
  status: string;
}

interface ClientContribution {
  client_id: string;
  institution_name: string;
  is_selected: boolean;
  training_status: string;
  local_sample_count: number;
  local_epochs: number;
  local_accuracy: number | null;
  local_loss: number | null;
  training_time_ms: number | null;
  update_size_bytes: number;
  selection_score: number;
  update_verified: boolean;
  is_accepted: boolean;
  rejection_reason: string | null;
  aggregation_weight: number;
}

interface RoundContribution {
  round_number: number;
  round_id: number;
  status: string;
  global_accuracy: number | null;
  global_loss: number | null;
  selected_clients: string[];
  accepted_updates_count: number;
  rejected_updates_count: number;
  aggregation_metrics: Record<string, any>;
  contributions: ClientContribution[];
}

export const AdminExperiments: React.FC = () => {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [publishedModels, setPublishedModels] = useState<PublishedModel[]>([]);
  const [selectedExp, setSelectedExp] = useState<Experiment | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [filterTab, setFilterTab] = useState<'active' | 'all'>('active');

  // Contributions data
  const [contributions, setContributions] = useState<RoundContribution[]>([]);

  // New Experiment Form State
  const [expName, setExpName] = useState('');
  const [selectedTask, setSelectedTask] = useState('diabetes_prediction');
  const [selectedModelId, setSelectedModelId] = useState<number | ''>('');
  const [clientSelectionMode, setClientSelectionMode] = useState<'adaptive' | 'random'>('adaptive');
  const [totalRounds, setTotalRounds] = useState(3);
  const [localEpochs, setLocalEpochs] = useState(3);
  const [learningRate, setLearningRate] = useState(0.01);
  const [clientScores, setClientScores] = useState<Record<string, any> | null>(null);

  const fetchClientScores = (id: number) => {
    api.get<Record<string, any>>(`/admin/experiments/${id}/client-scores`)
        .then(res => setClientScores(res.data))
        .catch(err => console.error('Failed to load client selection scores:', err));
  };

  const fetchContributions = (id: number) => {
    api.get<RoundContribution[]>(`/admin/experiments/${id}/contributions`)
        .then(res => setContributions(res.data))
        .catch(err => console.error('Failed to load contributions:', err));
  };

  useEffect(() => {
    if (selectedExp) {
      fetchClientScores(selectedExp.id);
      fetchContributions(selectedExp.id);
    }
  }, [selectedExp?.id, selectedExp?.current_round]);

  const fetchExperimentsAndModels = async () => {
    try {
      const [expRes, modelsRes] = await Promise.all([
        api.get<Experiment[]>('/admin/experiments'),
        api.get<PublishedModel[]>('/admin/models')
      ]);
      setExperiments(expRes.data);
      
      const availableModels = modelsRes.data.filter(
        m => m.status === 'published' || m.status === 'active'
      );
      setPublishedModels(availableModels);
      
      if (availableModels.length > 0 && selectedModelId === '') {
        const defaultModel = availableModels.find(m => m.healthcare_task === selectedTask) || availableModels[0];
        setSelectedModelId(defaultModel.id);
      }

      if (expRes.data.length > 0) {
        if (!selectedExp) {
          const activeExp = expRes.data.find(e => e.status !== 'completed') || expRes.data[0];
          setSelectedExp(activeExp);
        } else {
          const updated = expRes.data.find(e => e.id === selectedExp.id);
          if (updated) setSelectedExp(updated);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch experiment data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExperimentsAndModels();
  }, []);

  const handleCreateExperiment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModelId) return;
    setActionLoading(true);
    setError(null);

    try {
      const res = await api.post<Experiment>('/admin/experiments', {
        name: expName.trim() || `${selectedTask === 'diabetes_prediction' ? 'Diabetes' : 'Heart Disease'} FedAvg Trial`,
        healthcare_task: selectedTask,
        model_id: Number(selectedModelId),
        total_rounds: totalRounds,
        strategy: 'FedAvg',
        client_selection_mode: clientSelectionMode,
        local_epochs: localEpochs,
        learning_rate: learningRate,
        batch_size: 16
      });
      setIsModalOpen(false);
      setExpName('');
      await fetchExperimentsAndModels();
      setSelectedExp(res.data);
      setFilterTab('active');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create experiment.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStepRound = async () => {
    if (!selectedExp) return;
    setActionLoading(true);
    setError(null);

    try {
      await api.post(`/admin/experiments/${selectedExp.id}/step`);
      await fetchExperimentsAndModels();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to execute FL round.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRunAllRounds = async () => {
    if (!selectedExp) return;
    setActionLoading(true);
    setError(null);

    try {
      await api.post(`/admin/experiments/${selectedExp.id}/run`);
      await fetchExperimentsAndModels();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to run full experiment.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddRound = async () => {
    if (!selectedExp) return;
    setActionLoading(true);
    setError(null);
    try {
      await api.post(`/admin/experiments/${selectedExp.id}/add-round`);
      await fetchExperimentsAndModels();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add round to experiment.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleResetExperiment = async () => {
    if (!selectedExp) return;
    if (!window.confirm(`Reset experiment "${selectedExp.name}" back to Round 0? This will clear previous rounds so you can re-run it live.`)) return;
    setActionLoading(true);
    setError(null);
    try {
      await api.post(`/admin/experiments/${selectedExp.id}/reset`);
      setContributions([]);
      await fetchExperimentsAndModels();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset experiment.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteExperiment = async (expId: number, expName: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!window.confirm(`Permanently delete experiment "${expName}"? This will remove all associated rounds, client contributions, and model update deltas.`)) return;
    setActionLoading(true);
    setError(null);
    try {
      await api.delete(`/admin/experiments/${expId}`);
      if (selectedExp?.id === expId) {
        setSelectedExp(null);
        setContributions([]);
      }
      await fetchExperimentsAndModels();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete experiment.');
    } finally {
      setActionLoading(false);
    }
  };

  // Prepare chart data from actual round metrics
  const chartData = selectedExp?.rounds
    .filter(r => r.global_accuracy !== null)
    .map(r => ({
      round: `Round ${r.round_number}`,
      accuracy: r.global_accuracy !== null ? +(r.global_accuracy * 100).toFixed(2) : null,
      loss: r.global_loss !== null ? +r.global_loss.toFixed(4) : null,
      f1: r.f1_score !== null ? +(r.f1_score * 100).toFixed(2) : null,
    })) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center p-16">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  // Get latest round's contributions for client status
  const latestContributions = contributions.length > 0 ? contributions[contributions.length - 1] : null;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="card p-6 bg-white border border-slate-200 rounded-xl shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-sky-700 text-xs font-semibold uppercase tracking-wider mb-1">
            <FlaskConical className="w-4 h-4 text-sky-600" />
            <span>Phase 6: Federated Learning Engine</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Multi-Round Federated Learning Experiments
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Orchestrating distributed training on 3 isolated hospital nodes and performing mathematical FedAvg parameter aggregation.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="btn-kaggle shadow-xs"
        >
          <Plus className="w-4 h-4" />
          <span>New FL Experiment</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700 cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Grid: Experiments List & Active Experiment Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Experiments Catalog */}
        <div className="lg:col-span-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-200">
            <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
              <Layers className="w-4 h-4 text-sky-600" />
              <span>FL Trials</span>
            </h2>
            <div className="flex items-center space-x-1 text-[11px] bg-slate-100 p-0.5 rounded-lg border border-slate-200">
              <button
                type="button"
                onClick={() => setFilterTab('active')}
                className={`px-2 py-0.5 rounded font-medium transition-all cursor-pointer ${
                  filterTab === 'active'
                    ? 'bg-white text-slate-900 font-semibold shadow-xs'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                In-Progress ({experiments.filter(e => e.status !== 'completed').length})
              </button>
              <button
                type="button"
                onClick={() => setFilterTab('all')}
                className={`px-2 py-0.5 rounded font-medium transition-all cursor-pointer ${
                  filterTab === 'all'
                    ? 'bg-white text-slate-900 font-semibold shadow-xs'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                All ({experiments.length})
              </button>
            </div>
          </div>

          {experiments.length === 0 ? (
            <div className="card p-6 bg-white border border-slate-200 rounded-xl text-center space-y-3 shadow-xs">
              <p className="text-xs text-slate-500">No federated learning experiments created yet.</p>
              <button
                onClick={() => setIsModalOpen(true)}
                className="btn-kaggle"
              >
                Create First Experiment
              </button>
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[750px] overflow-y-auto pr-1">
              {(filterTab === 'active' ? experiments.filter(e => e.status !== 'completed') : experiments).map((exp) => {
                const isSelected = selectedExp?.id === exp.id;
                return (
                  <div
                    key={exp.id}
                    onClick={() => setSelectedExp(exp)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-sky-50/70 border-sky-300 shadow-xs'
                        : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/60 shadow-xs'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                          {exp.healthcare_task === 'diabetes_prediction' ? 'Diabetes Task' : 'Cardiology Task'}
                        </span>
                        <h3 className="text-xs font-bold text-slate-900">{exp.name}</h3>
                        <p className="text-[11px] text-slate-500">
                          Base Model: <span className="text-slate-700 font-medium">{exp.model_name || `Model #${exp.model_id}`}</span>
                        </p>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                          exp.status === 'completed'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : exp.status === 'running'
                            ? 'bg-amber-50 text-amber-700 border border-amber-200 animate-pulse'
                            : 'bg-sky-50 text-sky-700 border border-sky-200'
                        }`}>
                          {exp.status.toUpperCase()}
                        </span>
                        <button
                          onClick={(e) => handleDeleteExperiment(exp.id, exp.name, e)}
                          className="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
                          title="Delete experiment"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>

                    <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                      <span>Rounds: <strong className="text-slate-800 font-mono">{exp.current_round} / {exp.total_rounds}</strong></span>
                      {exp.final_accuracy !== null && (
                        <span>Acc: <strong className="text-emerald-700 font-mono">{(exp.final_accuracy * 100).toFixed(1)}%</strong></span>
                      )}
                    </div>
                  </div>
                );
              })}
              {filterTab === 'active' && experiments.filter(e => e.status !== 'completed').length === 0 && (
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-2">
                  <p className="text-xs text-slate-500">All experiments are completed.</p>
                  <button
                    onClick={() => setIsModalOpen(true)}
                    className="btn-kaggle"
                  >
                    Create New FL Experiment
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Active Experiment Inspector */}
        <div className="lg:col-span-8">
          {selectedExp ? (
            <div className="card p-6 bg-white border border-slate-200 rounded-xl shadow-xs space-y-6">
              {/* Header & Controls */}
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="badge-sky font-mono">
                      EXP #{selectedExp.id}
                    </span>
                    <span className="text-xs font-semibold text-slate-500">
                      {selectedExp.healthcare_task === 'diabetes_prediction' ? 'Diabetes Prediction' : 'Heart Disease Prediction'}
                    </span>
                  </div>
                  <h2 className="text-lg font-bold text-slate-900 mt-1">{selectedExp.name}</h2>
                  <p className="text-xs text-slate-500">
                    Aggregating with <strong className="text-sky-700 font-mono">FedAvg</strong> across Hospital A, B, and C
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  {selectedExp.status !== 'completed' ? (
                    <>
                      <button
                        onClick={handleStepRound}
                        disabled={actionLoading}
                        className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:bg-slate-200 disabled:text-slate-400 text-white font-bold text-xs flex items-center space-x-2 cursor-pointer shadow-xs transition-all"
                        title={`Execute Round ${selectedExp.current_round + 1} of ${selectedExp.total_rounds}`}
                      >
                        {actionLoading ? (
                          <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        ) : (
                          <Play className="w-3.5 h-3.5 fill-current" />
                        )}
                        <span>Step Next FL Round (Round {selectedExp.current_round + 1} of {selectedExp.total_rounds})</span>
                      </button>

                      <button
                        onClick={handleRunAllRounds}
                        disabled={actionLoading}
                        className="px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-200 disabled:text-slate-400 text-white font-semibold text-xs flex items-center space-x-1.5 cursor-pointer shadow-xs transition-all"
                      >
                        <FastForward className="w-3.5 h-3.5 fill-current" />
                        <span>Run All Rounds</span>
                      </button>

                      <button
                        onClick={(e) => handleDeleteExperiment(selectedExp.id, selectedExp.name, e)}
                        disabled={actionLoading}
                        className="px-2.5 py-2 rounded-lg border border-slate-200 hover:border-rose-300 hover:bg-rose-50 text-slate-500 hover:text-rose-600 font-semibold text-xs flex items-center space-x-1 cursor-pointer transition-all shadow-xs"
                        title="Delete experiment"
                      >
                        <Trash2 className="w-3.5 h-3.5 text-rose-500" />
                        <span>Delete</span>
                      </button>
                    </>
                  ) : (
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="badge-emerald flex items-center space-x-1.5 px-3 py-1.5 rounded-lg">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        <span>All {selectedExp.total_rounds} Rounds Completed</span>
                      </div>

                      <button
                        onClick={handleAddRound}
                        disabled={actionLoading}
                        className="px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:bg-slate-200 text-white text-xs font-semibold flex items-center space-x-1 cursor-pointer transition-all shadow-xs"
                        title="Add 1 more round to keep training"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>+1 Round & Step</span>
                      </button>

                      <button
                        onClick={handleResetExperiment}
                        disabled={actionLoading}
                        className="btn-secondary"
                        title="Reset experiment back to Round 0"
                      >
                        <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
                        <span>Reset to Round 0</span>
                      </button>

                      <button
                        onClick={() => setIsModalOpen(true)}
                        className="btn-secondary"
                      >
                        <Plus className="w-3.5 h-3.5 text-slate-500" />
                        <span>New Trial</span>
                      </button>

                      <button
                        onClick={(e) => handleDeleteExperiment(selectedExp.id, selectedExp.name, e)}
                        disabled={actionLoading}
                        className="px-2.5 py-1.5 rounded-lg border border-slate-200 hover:border-rose-300 hover:bg-rose-50 text-slate-500 hover:text-rose-600 text-xs font-semibold flex items-center space-x-1 cursor-pointer transition-all shadow-xs"
                        title="Delete this experiment permanently"
                      >
                        <Trash2 className="w-3.5 h-3.5 text-rose-500" />
                        <span>Delete</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Active Guidance Banner */}
              {selectedExp.status !== 'completed' ? (
                <div className="p-3.5 rounded-xl bg-sky-50 border border-sky-200 flex items-center justify-between text-xs text-sky-900">
                  <div className="flex items-center space-x-2.5">
                    <Play className="w-4 h-4 text-sky-600 shrink-0 fill-current" />
                    <span>
                      Ready to execute <strong>Round {selectedExp.current_round + 1}</strong>: Click <strong>"Step Next FL Round"</strong> above to trigger local training across Hospital A, B, and C, verify updates, and aggregate with FedAvg.
                    </span>
                  </div>
                </div>
              ) : (
                <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-between text-xs text-emerald-900">
                  <div className="flex items-center space-x-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>
                      All <strong>{selectedExp.total_rounds} rounds</strong> completed. Click <strong>"+1 Round & Step"</strong> to continue stepping or <strong>"Reset to Round 0"</strong> to re-run live.
                    </span>
                  </div>
                </div>
              )}

              {/* Experiment Metadata Strip */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-[10px] uppercase font-semibold text-slate-500 block">Current Round</span>
                  <span className="text-base font-bold font-mono text-slate-900">
                    {selectedExp.current_round} / {selectedExp.total_rounds}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-[10px] uppercase font-semibold text-slate-500 block">Local Hyperparams</span>
                  <span className="text-xs font-mono text-slate-700">
                    {selectedExp.local_epochs} Epochs • lr={selectedExp.learning_rate}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-[10px] uppercase font-semibold text-slate-500 block">Global Benchmark Accuracy</span>
                  <span className="text-base font-bold font-mono text-emerald-700">
                    {selectedExp.final_accuracy !== null ? `${(selectedExp.final_accuracy * 100).toFixed(1)}%` : 'Not available yet'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-[10px] uppercase font-semibold text-slate-500 block">Global Loss</span>
                  <span className="text-base font-bold font-mono text-sky-700">
                    {selectedExp.final_loss !== null ? selectedExp.final_loss.toFixed(4) : 'Not available yet'}
                  </span>
                </div>
              </div>

              {/* Participating Client Nodes */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <span className="text-xs font-semibold text-slate-700 flex items-center space-x-2">
                  <Users className="w-3.5 h-3.5 text-sky-600" />
                  <span>Participating Client Hospital Nodes</span>
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {['client_1', 'client_2', 'client_3'].map((cid) => {
                    const clientLabel = cid === 'client_1' ? 'Hospital A' : cid === 'client_2' ? 'Hospital B' : 'Hospital C';
                    const iconColor = cid === 'client_1' ? 'text-emerald-600' : cid === 'client_2' ? 'text-indigo-600' : 'text-amber-600';
                    const contrib = latestContributions?.contributions.find(c => c.client_id === cid);
                    
                    return (
                      <div key={cid} className="p-2.5 rounded-lg bg-white border border-slate-200 flex items-center space-x-2.5 shadow-xs">
                        <Building2 className={`w-4 h-4 ${iconColor}`} />
                        <div>
                          <p className="text-xs font-semibold text-slate-900">{clientLabel} ({cid.replace('_', ' ')})</p>
                          <p className="text-[10px] text-slate-500 font-mono">
                            {contrib
                              ? `${contrib.local_sample_count} records (${(contrib.aggregation_weight * 100).toFixed(0)}% weight)`
                              : 'Not available yet'}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Adaptive Client Selection Matrix */}
              {clientScores && (
                <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-2 border-b border-slate-200">
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-sky-500"></span>
                      <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                        Adaptive Client Selection Matrix (Section 28 Multi-Factor Formula)
                      </h3>
                    </div>
                    <span className="text-[11px] font-mono text-sky-700 font-medium">
                      Formula: w₁Perf + w₂Samples + w₃Rel + w₄Qual - w₅Comm - w₆Risk + λFairness
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {Object.entries(clientScores).map(([cid, data]: [string, any]) => {
                      const factors = data.factors || {};
                      const clientLabel = cid === 'client_1' ? 'Hospital A' : cid === 'client_2' ? 'Hospital B' : 'Hospital C';
                      return (
                        <div key={cid} className="p-3 rounded-lg bg-white border border-slate-200 space-y-2 shadow-xs">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-slate-900">{clientLabel}</span>
                            <span className="badge-sky font-mono font-bold">
                              Score: {data.composite_score}
                            </span>
                          </div>

                          <div className="space-y-1 text-[11px] text-slate-600 font-mono">
                            <div className="flex justify-between">
                              <span>Performance (w₁=0.25):</span>
                              <strong className="text-emerald-600">+{factors.performance}</strong>
                            </div>
                            <div className="flex justify-between">
                              <span>Samples (w₂=0.20):</span>
                              <strong className="text-indigo-600">+{factors.sample_count}</strong>
                            </div>
                            <div className="flex justify-between">
                              <span>Reliability (w₃=0.15):</span>
                              <strong className="text-slate-800">+{factors.reliability}</strong>
                            </div>
                            <div className="flex justify-between">
                              <span>Data Quality (w₄=0.15):</span>
                              <strong className="text-sky-600">+{factors.data_quality}</strong>
                            </div>
                            <div className="flex justify-between">
                              <span>Comm Cost (-w₅=0.10):</span>
                              <strong className="text-amber-600">-{factors.comm_cost}</strong>
                            </div>
                            <div className="flex justify-between">
                              <span>Risk Penalty (-w₆=0.15):</span>
                              <strong className="text-rose-600">-{factors.risk}</strong>
                            </div>
                            <div className="flex justify-between">
                              <span>Fairness (λ=0.10):</span>
                              <strong className={factors.fairness_penalty < 0 ? 'text-amber-600' : 'text-slate-500'}>
                                {factors.fairness_penalty}
                              </strong>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Accuracy & Loss Charts */}
              {chartData.length > 0 && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs space-y-3">
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Global Accuracy vs FL Rounds</span>
                    </h3>
                    <div className="h-48">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                          <XAxis dataKey="round" tick={{ fill: '#64748B', fontSize: 10 }} />
                          <YAxis tick={{ fill: '#64748B', fontSize: 10 }} domain={[0, 100]} unit="%" />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '8px', fontSize: '11px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
                            labelStyle={{ color: '#0F172A', fontWeight: 'bold' }}
                          />
                          <Line type="monotone" dataKey="accuracy" stroke="#059669" strokeWidth={2.5} dot={{ fill: '#059669', r: 4 }} name="Accuracy %" />
                          <Line type="monotone" dataKey="f1" stroke="#6366F1" strokeWidth={1.5} dot={{ fill: '#6366F1', r: 3 }} name="F1 Score %" strokeDasharray="4 4" />
                          <Legend wrapperStyle={{ fontSize: '10px' }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs space-y-3">
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
                      <TrendingUp className="w-3.5 h-3.5 text-sky-600" />
                      <span>Global Loss vs FL Rounds</span>
                    </h3>
                    <div className="h-48">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                          <XAxis dataKey="round" tick={{ fill: '#64748B', fontSize: 10 }} />
                          <YAxis tick={{ fill: '#64748B', fontSize: 10 }} />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '8px', fontSize: '11px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
                            labelStyle={{ color: '#0F172A', fontWeight: 'bold' }}
                          />
                          <Line type="monotone" dataKey="loss" stroke="#0284C7" strokeWidth={2.5} dot={{ fill: '#0284C7', r: 4 }} name="Global Loss" />
                          <Legend wrapperStyle={{ fontSize: '10px' }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              )}

              {/* Per-Client Contribution Table */}
              {contributions.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-2">
                    <Users className="w-3.5 h-3.5 text-sky-600" />
                    <span>Per-Client Contribution Table ({contributions.length} Rounds)</span>
                  </h3>
                  
                  {contributions.map((rc) => (
                    <div key={rc.round_id} className="rounded-xl border border-slate-200 overflow-hidden shadow-xs bg-white">
                      <div className="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="w-6 h-6 rounded-full bg-sky-100 text-sky-700 border border-sky-200 flex items-center justify-center font-bold text-xs font-mono">
                            {rc.round_number}
                          </span>
                          <span className="text-xs font-bold text-slate-900">Round {rc.round_number}</span>
                          <span className="badge-emerald font-mono">
                            {rc.status}
                          </span>
                        </div>
                        <div className="flex items-center space-x-3 text-[11px] text-slate-600 font-mono">
                          <span>Acc: <strong className="text-emerald-700">{rc.global_accuracy !== null ? `${(rc.global_accuracy * 100).toFixed(1)}%` : '-'}</strong></span>
                          <span>Loss: <strong className="text-sky-700">{rc.global_loss !== null ? rc.global_loss.toFixed(4) : '-'}</strong></span>
                        </div>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-[11px]">
                          <thead className="bg-slate-50 text-slate-500 uppercase text-[9px] tracking-wider border-b border-slate-200">
                            <tr>
                              <th className="px-3 py-2 font-semibold">Client</th>
                              <th className="px-3 py-2 font-semibold">Selected</th>
                              <th className="px-3 py-2 font-semibold text-right">Samples</th>
                              <th className="px-3 py-2 font-semibold text-right">Local Accuracy</th>
                              <th className="px-3 py-2 font-semibold text-right">Local Loss</th>
                              <th className="px-3 py-2 font-semibold text-right">Training Time</th>
                              <th className="px-3 py-2 font-semibold text-right">Update Size</th>
                              <th className="px-3 py-2 font-semibold text-right">Security</th>
                              <th className="px-3 py-2 font-semibold">Status</th>
                              <th className="px-3 py-2 font-semibold text-right">Agg. Weight</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 text-slate-700">
                            {rc.contributions.map((c) => (
                              <tr key={c.client_id} className="hover:bg-slate-50/60 transition-colors">
                                <td className="px-3 py-2">
                                  <div>
                                    <span className="font-mono text-sky-700 font-medium">{c.client_id}</span>
                                    <p className="text-[9px] text-slate-500 truncate max-w-[120px]">{c.institution_name}</p>
                                  </div>
                                </td>
                                <td className="px-3 py-2">
                                  {c.is_selected ? (
                                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                                  ) : (
                                    <span className="text-slate-400">—</span>
                                  )}
                                </td>
                                <td className="px-3 py-2 text-right font-mono text-slate-900 font-medium">{c.local_sample_count}</td>
                                <td className="px-3 py-2 text-right font-mono text-emerald-700 font-medium">
                                  {c.local_accuracy !== null ? `${(c.local_accuracy * 100).toFixed(1)}%` : '-'}
                                </td>
                                <td className="px-3 py-2 text-right font-mono text-sky-700">
                                  {c.local_loss !== null ? c.local_loss.toFixed(4) : '-'}
                                </td>
                                <td className="px-3 py-2 text-right font-mono text-slate-600">
                                  {c.training_time_ms !== null ? `${c.training_time_ms}ms` : '-'}
                                </td>
                                <td className="px-3 py-2 text-right font-mono text-slate-600">
                                  {c.update_size_bytes > 0 ? `${(c.update_size_bytes / 1024).toFixed(1)} KB` : '-'}
                                </td>
                                <td className="px-3 py-2 text-right">
                                  {c.update_verified ? (
                                    <span className={`text-[10px] font-semibold ${c.is_accepted ? 'text-emerald-700' : 'text-rose-700'}`}>
                                      {c.is_accepted ? '✓ Passed' : '✗ Rejected'}
                                    </span>
                                  ) : (
                                    <span className="text-slate-400">-</span>
                                  )}
                                </td>
                                <td className="px-3 py-2">
                                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                                    c.training_status === 'accepted' || c.training_status === 'aggregated'
                                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                      : c.training_status === 'rejected'
                                      ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                      : c.training_status === 'waiting'
                                      ? 'bg-amber-50 text-amber-700 border border-amber-200'
                                      : 'bg-slate-100 text-slate-600'
                                  }`}>
                                    {c.training_status?.toUpperCase() || 'UNKNOWN'}
                                  </span>
                                </td>
                                <td className="px-3 py-2 text-right font-mono font-bold text-sky-700">
                                  {(c.aggregation_weight * 100).toFixed(1)}%
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Round History */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-2">
                  <TrendingUp className="w-3.5 h-3.5 text-sky-600" />
                  <span>Round History & Global Model Summary ({selectedExp.rounds.length})</span>
                </h3>

                {selectedExp.rounds.length === 0 ? (
                  <div className="p-8 rounded-xl bg-slate-50 border border-dashed border-slate-200 text-center space-y-2">
                    <p className="text-xs text-slate-500">No rounds executed yet. Click "Step Next FL Round" to broadcast parameters and start distributed local training.</p>
                  </div>
                ) : (
                  <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs">
                    <table className="w-full text-left text-[11px]">
                      <thead className="bg-slate-50 text-slate-500 uppercase text-[9px] tracking-wider border-b border-slate-200">
                        <tr>
                          <th className="px-3 py-2.5 font-semibold">Round</th>
                          <th className="px-3 py-2.5 font-semibold text-right">Global Accuracy</th>
                          <th className="px-3 py-2.5 font-semibold text-right">Global Loss</th>
                          <th className="px-3 py-2.5 font-semibold text-right">F1 Score</th>
                          <th className="px-3 py-2.5 font-semibold text-right">Total Samples</th>
                          <th className="px-3 py-2.5 font-semibold">Clients</th>
                          <th className="px-3 py-2.5 font-semibold text-right">Agg. Norm</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-700">
                        {selectedExp.rounds.map((round) => (
                          <tr key={round.id} className="hover:bg-slate-50/60 transition-colors">
                            <td className="px-3 py-2.5">
                              <span className="w-6 h-6 inline-flex items-center justify-center rounded-full bg-sky-50 text-sky-700 border border-sky-200 font-bold text-xs font-mono">
                                {round.round_number}
                              </span>
                            </td>
                            <td className="px-3 py-2.5 text-right font-bold text-emerald-700 font-mono">
                              {round.global_accuracy !== null ? `${(round.global_accuracy * 100).toFixed(1)}%` : '-'}
                            </td>
                            <td className="px-3 py-2.5 text-right font-bold text-sky-700 font-mono">
                              {round.global_loss !== null ? round.global_loss.toFixed(4) : '-'}
                            </td>
                            <td className="px-3 py-2.5 text-right font-mono text-slate-800">
                              {round.f1_score !== null ? `${(round.f1_score * 100).toFixed(1)}%` : '-'}
                            </td>
                            <td className="px-3 py-2.5 text-right font-mono text-indigo-700">
                              {round.aggregation_metrics.total_samples || '-'}
                            </td>
                            <td className="px-3 py-2.5 font-mono text-slate-500 text-[10px]">
                              {round.participating_clients.join(', ')}
                            </td>
                            <td className="px-3 py-2.5 text-right font-mono text-slate-600">
                              {round.aggregation_metrics.aggregated_l2_norm || 0}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card p-12 bg-white rounded-xl border border-slate-200 text-center space-y-2 shadow-xs">
              <p className="text-xs text-slate-500">Select an experiment on the left to inspect round-by-round parameters.</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Experiment Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white w-full max-w-lg p-6 rounded-2xl border border-slate-200 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
                <FlaskConical className="w-4 h-4 text-sky-600" />
                <span>Configure New FL Experiment</span>
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateExperiment} className="space-y-3.5 text-xs">
              <div>
                <label className="text-slate-700 font-semibold block mb-1">Experiment Name</label>
                <input
                  type="text"
                  value={expName}
                  onChange={(e) => setExpName(e.target.value)}
                  placeholder="e.g. Multi-Hospital FedAvg Benchmark Trial"
                  className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 focus:border-sky-500 focus:outline-hidden"
                  required
                />
              </div>

              <div>
                <label className="text-slate-700 font-semibold block mb-1">Healthcare Task</label>
                <select
                  value={selectedTask}
                  onChange={(e) => {
                    const newTask = e.target.value;
                    setSelectedTask(newTask);
                    const matchingModel = publishedModels.find(m => m.healthcare_task === newTask);
                    if (matchingModel) setSelectedModelId(matchingModel.id);
                  }}
                  className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 focus:border-sky-500 focus:outline-hidden"
                >
                  <option value="diabetes_prediction">Diabetes Prediction (Pima Indians Diagnostic)</option>
                  <option value="heart_disease_prediction">Heart Disease Prediction (Cleveland Cardiology)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-700 font-semibold block mb-1">Base Healthcare Model</label>
                <select
                  value={selectedModelId}
                  onChange={(e) => setSelectedModelId(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 font-mono focus:border-sky-500 focus:outline-hidden"
                  required
                >
                  {publishedModels
                    .filter(m => m.healthcare_task === selectedTask)
                    .map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name} (ID #{m.id})
                      </option>
                    ))}
                </select>
                {publishedModels.filter(m => m.healthcare_task === selectedTask).length === 0 && (
                  <p className="text-[11px] text-amber-700 mt-1">
                    No published/active models found for this task. Please publish and activate a model from Admin Models first.
                  </p>
                )}
              </div>

              <div>
                <label className="text-slate-700 font-semibold block mb-1">Client Selection Strategy (Section 28)</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setClientSelectionMode('adaptive')}
                    className={`p-2.5 rounded-lg border text-left transition-all cursor-pointer ${
                      clientSelectionMode === 'adaptive'
                        ? 'bg-sky-50 border-sky-300 text-sky-950 shadow-xs'
                        : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300'
                    }`}
                  >
                    <div className="text-xs font-bold flex items-center space-x-1.5">
                      <span className="w-2 h-2 rounded-full bg-sky-500"></span>
                      <span>Proposed: Adaptive</span>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-1">Multi-factor mathematical scoring with fairness penalty</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => setClientSelectionMode('random')}
                    className={`p-2.5 rounded-lg border text-left transition-all cursor-pointer ${
                      clientSelectionMode === 'random'
                        ? 'bg-sky-50 border-sky-300 text-sky-950 shadow-xs'
                        : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300'
                    }`}
                  >
                    <div className="text-xs font-bold flex items-center space-x-1.5">
                      <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                      <span>Baseline: Random</span>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-1">Standard FedAvg uniform random selection</p>
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 pt-1">
                <div>
                  <label className="text-slate-600 font-semibold block mb-1">Total Rounds</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={totalRounds}
                    onChange={(e) => setTotalRounds(Number(e.target.value))}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900 font-mono focus:border-sky-500 focus:outline-hidden"
                  />
                </div>
                <div>
                  <label className="text-slate-600 font-semibold block mb-1">Local Epochs</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={localEpochs}
                    onChange={(e) => setLocalEpochs(Number(e.target.value))}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900 font-mono focus:border-sky-500 focus:outline-hidden"
                  />
                </div>
                <div>
                  <label className="text-slate-600 font-semibold block mb-1">Learning Rate</label>
                  <input
                    type="number"
                    step="0.001"
                    min="0.001"
                    max="0.1"
                    value={learningRate}
                    onChange={(e) => setLearningRate(Number(e.target.value))}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900 font-mono focus:border-sky-500 focus:outline-hidden"
                  />
                </div>
              </div>

              <div className="p-3 rounded-lg bg-sky-50 border border-sky-200 text-[11px] text-sky-900">
                <span className="font-semibold text-sky-950">FedAvg Math:</span> Parameters will be aggregated as $W_{'{t+1}'} = W_t + \sum (n_k / N) \Delta W_k$ across Clients 1, 2, and 3.
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading || publishedModels.filter(m => m.healthcare_task === selectedTask).length === 0}
                  className="btn-kaggle"
                >
                  {actionLoading ? 'Creating...' : 'Initialize FL Experiment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
