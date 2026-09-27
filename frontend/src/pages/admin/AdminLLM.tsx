import React, { useState } from 'react';
import { api } from '../../services/api';
import { 
  Bot, 
  Sparkles, 
  ShieldAlert, 
  Sliders, 
  Users, 
  Play, 
  Building2,
  AlertTriangle,
  ArrowRight
} from 'lucide-react';

interface SelectionAdvisory {
  selected_clients: string[];
  rationale: string;
  predicted_convergence_impact: string;
  risk_assessment: Record<string, string>;
  confidence: number;
  generated_by: string;
}

interface ThreatAdvisory {
  threat_level: string;
  flagged_clients: string[];
  recommended_actions: Record<string, string>;
  confidence: number;
  clinical_explanation: string;
  generated_by: string;
}

interface HyperparameterAdvisory {
  recommended_lr: number;
  recommended_epochs: number;
  early_stopping: boolean;
  rationale: string;
  confidence: number;
  generated_by: string;
}

export const AdminLLM: React.FC = () => {
  // 1. Selection Advisor State
  const [task, setTask] = useState('diabetes_prediction');
  const [selectionLoading, setSelectionLoading] = useState(false);
  const [selectionAdvisory, setSelectionAdvisory] = useState<SelectionAdvisory | null>(null);

  // 2. Threat Advisor State
  const [threatLoading, setThreatLoading] = useState(false);
  const [threatAdvisory, setThreatAdvisory] = useState<ThreatAdvisory | null>(null);

  // 3. Hyperparameter Advisor State
  const [currentLr, setCurrentLr] = useState(0.01);
  const [currentEpochs, setCurrentEpochs] = useState(3);
  const [hyperLoading, setHyperLoading] = useState(false);
  const [hyperAdvisory, setHyperAdvisory] = useState<HyperparameterAdvisory | null>(null);

  const [error, setError] = useState<string | null>(null);

  const handleGetSelectionAdvisory = async () => {
    setSelectionLoading(true);
    setError(null);
    try {
      const res = await api.post<SelectionAdvisory>('/admin/llm/client-selection-advisor', {
        healthcare_task: task
      });
      setSelectionAdvisory(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate client selection advisory.');
    } finally {
      setSelectionLoading(false);
    }
  };

  const handleGetThreatAdvisory = async () => {
    setThreatLoading(true);
    setError(null);
    try {
      const res = await api.post<ThreatAdvisory>('/admin/llm/security-threat-advisor', {});
      setThreatAdvisory(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate threat intelligence advisory.');
    } finally {
      setThreatLoading(false);
    }
  };

  const handleGetHyperAdvisory = async () => {
    setHyperLoading(true);
    setError(null);
    try {
      const res = await api.post<HyperparameterAdvisory>('/admin/llm/hyperparameter-advisor', {
        learning_rate: currentLr,
        local_epochs: currentEpochs
      });
      setHyperAdvisory(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate hyperparameter advisory.');
    } finally {
      setHyperLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="card p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-l-4 border-l-indigo-600">
        <div>
          <div className="flex items-center space-x-2 text-indigo-700 text-xs font-semibold uppercase tracking-wider mb-1">
            <Bot className="w-4 h-4" />
            <span>AI Reasoning & Automation</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Autonomous Healthcare Federated Intelligence Coordinator
          </h1>
          <p className="text-sm text-slate-600 mt-1 max-w-3xl">
            Combines large language model cognitive reasoning with deterministic fallback guarantees to supervise client selection, intercept attacks, and optimize convergence trajectory.
          </p>
        </div>

        <div className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-800 text-xs font-medium shrink-0">
          <Sparkles className="w-4 h-4 text-indigo-600" />
          <span>Engine: Hybrid LLM / Fallback Active</span>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Module 1: Client Selection & Risk Advisor */}
      <div className="card p-6 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200">
          <div className="flex items-center space-x-2">
            <Users className="w-4 h-4 text-sky-600" />
            <h2 className="text-base font-semibold text-slate-900">
              1. Automated Client Selection & Institutional Risk Advisor
            </h2>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            Evaluates statistical non-IID bias, sample volume, and network latency
          </span>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <select
            value={task}
            onChange={(e) => setTask(e.target.value)}
            className="px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 text-xs font-medium focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
          >
            <option value="diabetes_prediction">Diabetes Mellitus Diagnostic Model (Pima Indian)</option>
            <option value="heart_disease_prediction">Cardiovascular Disease Model (UCI Cleveland)</option>
            <option value="icu_sepsis_prediction">ICU Sepsis Multicenter Clinical Model (PhysioNet)</option>
          </select>

          <button
            onClick={handleGetSelectionAdvisory}
            disabled={selectionLoading}
            className="btn-kaggle flex items-center justify-center space-x-1.5 cursor-pointer"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{selectionLoading ? 'Reasoning...' : 'Generate Selection Advisory'}</span>
          </button>
        </div>

        {selectionAdvisory && (
          <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-200">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-slate-700">Selected Clinical Nodes:</span>
                {selectionAdvisory.selected_clients.map((c) => (
                  <span key={c} className="badge-sky font-mono font-bold">
                    {c === 'client_1' ? 'Hospital A' : c === 'client_2' ? 'Hospital B' : 'Hospital C'}
                  </span>
                ))}
              </div>
              <div className="flex items-center space-x-2 text-xs font-mono">
                <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  Confidence: {(selectionAdvisory.confidence * 100).toFixed(0)}%
                </span>
                <span className="px-2 py-0.5 rounded bg-white text-slate-600 border border-slate-200">
                  {selectionAdvisory.generated_by}
                </span>
              </div>
            </div>

            <div className="text-xs text-slate-700 leading-relaxed space-y-1">
              <strong className="text-slate-900 font-semibold block text-sm">Clinical Rationale:</strong>
              <p>{selectionAdvisory.rationale}</p>
            </div>

            <div className="p-3.5 rounded-lg bg-white border border-slate-200 text-xs">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Convergence Projection:</span>
              <span className="text-slate-800 font-medium flex items-center space-x-1">
                <ArrowRight className="w-3.5 h-3.5 text-sky-600 shrink-0" />
                <span>{selectionAdvisory.predicted_convergence_impact}</span>
              </span>
            </div>

            {/* Risk Assessment Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
              {Object.entries(selectionAdvisory.risk_assessment).map(([hosp, risk]) => (
                <div key={hosp} className="p-3.5 rounded-lg bg-white border border-slate-200 text-xs space-y-1 shadow-xs">
                  <div className="flex items-center space-x-1.5 font-bold text-slate-900">
                    <Building2 className="w-3.5 h-3.5 text-sky-600" />
                    <span>{hosp}</span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-normal">{risk}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Module 2: Security & Threat Intelligence Advisor */}
      <div className="card p-6 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-rose-600" />
            <h2 className="text-base font-semibold text-slate-900">
              2. Autonomous Security & Adversarial Threat Intelligence Advisor
            </h2>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            Analyzes multi-round parameter vectors for gradient poisoning attacks
          </span>
        </div>

        <button
          onClick={handleGetThreatAdvisory}
          disabled={threatLoading}
          className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-700 disabled:bg-slate-300 text-white font-medium text-xs flex items-center justify-center space-x-1.5 shadow-xs cursor-pointer transition-colors"
        >
          <Play className="w-3.5 h-3.5" />
          <span>{threatLoading ? 'Analyzing Threat Matrix...' : 'Run Threat Intelligence Audit'}</span>
        </button>

        {threatAdvisory && (
          <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-200">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-slate-700">Adversarial Threat Level:</span>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold ${
                  threatAdvisory.threat_level === 'LOW' 
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-300' 
                    : 'bg-rose-50 text-rose-700 border border-rose-300'
                }`}>
                  {threatAdvisory.threat_level}
                </span>
              </div>
              <div className="flex items-center space-x-2 text-xs font-mono">
                <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  Confidence: {(threatAdvisory.confidence * 100).toFixed(0)}%
                </span>
                <span className="px-2 py-0.5 rounded bg-white text-slate-600 border border-slate-200">
                  {threatAdvisory.generated_by}
                </span>
              </div>
            </div>

            <div className="text-xs text-slate-700 leading-relaxed space-y-1">
              <strong className="text-slate-900 font-semibold block text-sm">Intelligence Diagnosis:</strong>
              <p>{threatAdvisory.clinical_explanation}</p>
            </div>

            <div className="space-y-2 pt-1">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Node-Level Directives:</span>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
                {Object.entries(threatAdvisory.recommended_actions).map(([hosp, action]) => (
                  <div key={hosp} className="p-3 rounded-lg bg-white border border-slate-200 space-y-1 shadow-xs">
                    <span className="font-bold text-slate-900 block">{hosp}</span>
                    <span className={`text-xs font-mono font-semibold ${action.startsWith('REJECT') ? 'text-rose-600' : 'text-emerald-700'}`}>
                      {action}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Module 3: Hyperparameter & Convergence Advisor */}
      <div className="card p-6 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200">
          <div className="flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-emerald-600" />
            <h2 className="text-base font-semibold text-slate-900">
              3. Dynamic Hyperparameter & Convergence Trajectory Advisor
            </h2>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            Analyzes loss surface gradient to recommend learning rate and early stopping
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="text-slate-700 font-medium block text-xs mb-1">Current Learning Rate (lr)</label>
            <input
              type="number"
              step="0.001"
              value={currentLr}
              onChange={(e) => setCurrentLr(parseFloat(e.target.value))}
              className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 text-xs font-mono focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
            />
          </div>

          <div>
            <label className="text-slate-700 font-medium block text-xs mb-1">Current Local Epochs (E)</label>
            <input
              type="number"
              min="1"
              max="10"
              value={currentEpochs}
              onChange={(e) => setCurrentEpochs(parseInt(e.target.value))}
              className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 text-xs font-mono focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={handleGetHyperAdvisory}
              disabled={hyperLoading}
              className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white font-medium text-xs flex items-center justify-center space-x-1.5 shadow-xs cursor-pointer transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{hyperLoading ? 'Analyzing...' : 'Analyze Convergence Trajectory'}</span>
            </button>
          </div>
        </div>

        {hyperAdvisory && (
          <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-200">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold text-slate-700">Recommended Policy:</span>
                <span className="badge-indigo font-mono">
                  Target LR: {hyperAdvisory.recommended_lr}
                </span>
                <span className="badge-indigo font-mono">
                  Epochs: {hyperAdvisory.recommended_epochs}
                </span>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold ${
                  hyperAdvisory.early_stopping
                    ? 'bg-amber-50 text-amber-800 border border-amber-300'
                    : 'bg-emerald-50 text-emerald-700 border border-emerald-300'
                }`}>
                  Early Stopping: {hyperAdvisory.early_stopping ? 'RECOMMENDED (PLATEAU)' : 'CONTINUE ROUNDS'}
                </span>
              </div>
              <div className="flex items-center space-x-2 text-xs font-mono">
                <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  Confidence: {(hyperAdvisory.confidence * 100).toFixed(0)}%
                </span>
                <span className="px-2 py-0.5 rounded bg-white text-slate-600 border border-slate-200">
                  {hyperAdvisory.generated_by}
                </span>
              </div>
            </div>

            <div className="text-xs text-slate-700 leading-relaxed space-y-1">
              <strong className="text-slate-900 font-semibold block text-sm">Convergence Analysis:</strong>
              <p>{hyperAdvisory.rationale}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
