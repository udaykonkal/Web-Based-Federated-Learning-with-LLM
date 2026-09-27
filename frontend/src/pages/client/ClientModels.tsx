import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import type { MLModel, ClientPrivateProfile } from '../../types';
import { 
  Lock, 
  Building2, 
  ArrowRight, 
  Clock, 
  AlertCircle,
  Layers,
  ShieldCheck,
  Download
} from 'lucide-react';

export const ClientModels: React.FC = () => {
  const { clientId, institutionName } = useAuth();
  const [models, setModels] = useState<MLModel[]>([]);
  const [clientMeta, setClientMeta] = useState<ClientPrivateProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAvailableModels = async () => {
      try {
        const [modelsRes, profileRes] = await Promise.all([
          api.get<MLModel[]>('/client/models'),
          clientId ? api.get<ClientPrivateProfile>(`/client/${clientId}/profile`) : Promise.resolve({ data: null }),
        ]);
        setModels(modelsRes.data);
        if (profileRes.data) {
          setClientMeta(profileRes.data);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to fetch available healthcare models.');
      } finally {
        setLoading(false);
      }
    };

    fetchAvailableModels();
  }, [clientId]);

  const handleDownloadBundle = async (mId: number, task: string) => {
    try {
      const res = await api.get(`/client/models/${mId}/export-package`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/zip' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `fl_client_kit_${task}_${clientId}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err: any) {
      alert('Failed to download starter kit: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-20 min-h-[60vh]">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-500 text-xs font-mono">Querying Central Coordinator Model Registry...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 p-4 sm:p-6 text-gray-900">
      {/* Node Header Strip (Kaggle Minimal Style) */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-xs">
        <div>
          <div className="flex items-center space-x-2 text-sky-600 text-xs font-bold uppercase tracking-wider mb-1 font-mono">
            <Building2 className="w-4 h-4" />
            <span>Clinical Node Workspace • {clientId?.toUpperCase()}</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 tracking-tight">
            {institutionName || 'Healthcare Institution Client Node'}
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            Browse and train federated models published by the Central Coordinator.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-gray-50 border border-gray-200 text-gray-700 text-xs font-mono">
            <Lock className="w-3.5 h-3.5 text-sky-600" />
            <span>Local Storage Isolated</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Section: Available Healthcare Models */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-gray-200 pb-3">
          <div>
            <h2 className="text-base font-bold text-gray-900 tracking-tight flex items-center space-x-2">
              <Layers className="w-4 h-4 text-sky-600" />
              <span>Available Federated Tasks</span>
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Coordinator-governed training access (Model State Machine Rule 47)
            </p>
          </div>

          <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-gray-100 text-gray-700 border border-gray-200">
            {models.length} Task{models.length !== 1 ? 's' : ''} Open
          </span>
        </div>

        {/* Empty State When No Model Published */}
        {models.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-xl p-12 text-center flex flex-col items-center justify-center space-y-4 shadow-xs">
            <div className="w-14 h-14 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600">
              <Clock className="w-7 h-7 animate-pulse" />
            </div>

            <div className="max-w-md space-y-2">
              <h3 className="text-base font-bold text-gray-900">
                No federated models are currently active.
              </h3>
              <p className="text-xs text-gray-500 leading-relaxed">
                Please wait for the Coordinator to activate a model. In accordance with platform lifecycle rules,
                local client training and federated round participation remain
                locked until the Coordinator activates a task.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-gray-50 border border-gray-200 text-[11px] text-gray-600 max-w-lg text-left space-y-1.5 mt-2 font-mono">
              <div className="flex items-center space-x-2 text-amber-700 font-semibold">
                <Lock className="w-3.5 h-3.5" />
                <span>Enforced Availability Guards:</span>
              </div>
              <p>• Local PyTorch training pipeline: <span className="text-rose-600 font-bold">LOCKED</span></p>
              <p>• Model update generator & FedAvg uplink: <span className="text-rose-600 font-bold">LOCKED</span></p>
              <p>• Client contribution workspace: <span className="text-rose-600 font-bold">AWAITING PUBLICATION</span></p>
            </div>
          </div>
        ) : (
          /* KAGGLE-INSPIRED COMPETITION MODEL CARDS */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {models.map((model) => (
              <div 
                key={model.id}
                className="bg-white border border-gray-200 hover:border-sky-300 hover:shadow-md rounded-xl p-5 transition-all flex flex-col justify-between space-y-4 group"
              >
                <div>
                  <div className="flex items-center justify-between mb-2.5">
                    <div className="flex items-center space-x-2">
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200 font-semibold">
                        {model.version}
                      </span>
                      <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-gray-100 text-gray-700 border border-gray-200">
                        {model.healthcare_task === 'diabetes_prediction' ? 'Metabolic Health' : 'Cardiovascular Health'}
                      </span>
                    </div>
                    <span className="inline-flex items-center space-x-1.5 text-[11px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-medium">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      <span>ACTIVE</span>
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-gray-900 group-hover:text-sky-600 transition-colors">
                    {model.name}
                  </h3>
                  <p className="text-xs text-gray-600 mt-1.5 line-clamp-2 leading-relaxed">
                    {model.description || 'Supervised tabular healthcare classification task for federated clinical prediction.'}
                  </p>

                  <div className="mt-4 pt-3 border-t border-gray-100 grid grid-cols-2 gap-3 text-xs font-mono">
                    <div className="bg-gray-50 p-2 rounded border border-gray-200">
                      <span className="text-gray-400 text-[10px] uppercase block">Architecture</span>
                      <span className="text-gray-800 text-xs font-semibold">{model.architecture}</span>
                    </div>
                    <div className="bg-gray-50 p-2 rounded border border-gray-200">
                      <span className="text-gray-400 text-[10px] uppercase block">Target Variable</span>
                      <span className="text-sky-700 text-xs font-semibold">{model.target_variable}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-2 flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => navigate(`/client/models/${model.id}`)}
                    className="flex-1 py-2 px-3 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs flex items-center justify-center space-x-1.5 transition-colors cursor-pointer shadow-xs"
                  >
                    <span>Open Workspace</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDownloadBundle(model.id, model.healthcare_task)}
                    title="Download complete standalone Python training starter kit (.zip)"
                    className="py-2 px-3 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 font-semibold text-xs flex items-center space-x-1 transition-colors cursor-pointer border border-slate-200 shadow-xs"
                  >
                    <Download className="w-3.5 h-3.5 text-sky-600" />
                    <span>Starter Kit (.zip)</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Client Local Metadata & Privacy Guarantee */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3 shadow-xs">
        <div className="flex items-center justify-between border-b border-gray-200 pb-2.5">
          <h3 className="text-xs font-bold text-gray-800 flex items-center space-x-2 font-mono uppercase">
            <Lock className="w-3.5 h-3.5 text-sky-600" />
            <span>Private Node Metadata & Storage Status</span>
          </h3>
          <span className="text-[10px] font-mono text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200 font-semibold">
            Node: {clientId}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
          <div className="p-2.5 rounded bg-gray-50 border border-gray-200">
            <span className="text-gray-400 text-[10px] uppercase block">Local Partition Path</span>
            <p className="text-gray-700 text-[11px] mt-0.5 truncate">data/clients/{clientId}/</p>
          </div>
          <div className="p-2.5 rounded bg-gray-50 border border-gray-200">
            <span className="text-gray-400 text-[10px] uppercase block">Isolation Boundary</span>
            <p className="text-emerald-700 text-[11px] mt-0.5 flex items-center space-x-1 font-semibold">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>{clientMeta?.privacy_status || 'Zero Central Leakage'}</span>
            </p>
          </div>
          <div className="p-2.5 rounded bg-gray-50 border border-gray-200">
            <span className="text-gray-400 text-[10px] uppercase block">Coordinator Inspection</span>
            <p className="text-gray-700 text-[11px] mt-0.5">Updates Only (Zero Raw Records)</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClientModels;
