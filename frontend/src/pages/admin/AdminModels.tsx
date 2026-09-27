import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import type { MLModel } from '../../types';
import { 
  Cpu, 
  RefreshCw, 
  Globe, 
  Power, 
  Archive, 
  FileEdit, 
  AlertCircle, 
  Info, 
  Sparkles,
  UploadCloud
} from 'lucide-react';

export const AdminModels: React.FC = () => {
  const [models, setModels] = useState<MLModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const fetchModels = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<MLModel[]>('/admin/models');
      setModels(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch healthcare models.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleInitializeDefaults = async () => {
    setLoading(true);
    try {
      await api.post('/admin/models/initialize-defaults');
      await fetchModels();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initialize default models.');
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (modelId: number, newStatus: string) => {
    setUpdatingId(modelId);
    try {
      const res = await api.patch<MLModel>(`/admin/models/${modelId}/status`, {
        status: newStatus,
      });
      setModels(prev => prev.map(m => m.id === modelId ? res.data : m));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update model status.');
    } finally {
      setUpdatingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return (
          <span className="badge-emerald inline-flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Active (Visible to Clients)</span>
          </span>
        );
      case 'published':
        return (
          <span className="badge-sky inline-flex items-center space-x-1.5">
            <Globe className="w-3 h-3" />
            <span>Published (Pending Activation)</span>
          </span>
        );
      case 'uploaded':
        return (
          <span className="badge-indigo inline-flex items-center space-x-1.5">
            <UploadCloud className="w-3 h-3" />
            <span>Uploaded (Hidden)</span>
          </span>
        );
      case 'draft':
        return (
          <span className="badge-slate inline-flex items-center space-x-1.5">
            <FileEdit className="w-3 h-3" />
            <span>Draft (Hidden)</span>
          </span>
        );
      case 'inactive':
        return (
          <span className="badge-amber inline-flex items-center space-x-1.5">
            <Power className="w-3 h-3" />
            <span>Inactive (Hidden)</span>
          </span>
        );
      case 'archived':
        return (
          <span className="badge-rose inline-flex items-center space-x-1.5">
            <Archive className="w-3 h-3" />
            <span>Archived</span>
          </span>
        );
      default:
        return (
          <span className="badge-slate font-mono capitalize">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="card p-6 bg-white border border-slate-200 rounded-xl shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-sky-700 text-xs font-semibold uppercase tracking-wider mb-1">
            <Cpu className="w-4 h-4 text-sky-600" />
            <span>Model Availability Engine (Side A)</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Healthcare Model & Publishing Control
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Configure PyTorch architectures and control model availability states (Rules 7, 10, 16 & 17).
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleInitializeDefaults}
            className="btn-secondary"
            title="Seed default Diabetes & Heart Disease models"
          >
            <RefreshCw className="w-3.5 h-3.5 text-sky-600" />
            <span>Init Default Models</span>
          </button>
        </div>
      </div>

      {/* Model Availability State Rule Callout */}
      <div className="p-4 rounded-xl bg-sky-50 border border-sky-200 text-xs text-sky-950 flex items-start space-x-3">
        <Info className="w-4 h-4 text-sky-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <span className="font-semibold text-sky-950">Central Authority Rule:</span>
          <p className="text-[11px] text-sky-900/80 leading-relaxed">
            Clinical clients cannot view or train on a model until you transition it to <strong className="text-sky-800 font-semibold">'Active'</strong> status. The required workflow is: <strong className="text-slate-800">Draft → Uploaded → Published → Active</strong>. Only Active models appear on the Client "Available Models" page.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Models Grid */}
      {loading ? (
        <div className="flex items-center justify-center p-16">
          <div className="w-8 h-8 border-3 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : models.length === 0 ? (
        <div className="card p-12 bg-white rounded-xl border border-slate-200 text-center space-y-4 shadow-xs">
          <div className="w-14 h-14 rounded-2xl bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600 mx-auto">
            <Cpu className="w-7 h-7" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-900">No Healthcare Models Configured</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Initialize the default Diabetes Prediction and Heart Disease Prediction PyTorch models to begin managing availability.
            </p>
          </div>
          <button
            onClick={handleInitializeDefaults}
            className="btn-kaggle"
          >
            <Sparkles className="w-4 h-4" />
            <span>Generate Default PyTorch Healthcare Models</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {models.map((model) => (
            <div
              key={model.id}
              className="card p-6 bg-white rounded-xl border border-slate-200 hover:border-sky-300 hover:shadow-card-hover transition-all flex flex-col justify-between shadow-xs"
            >
              <div>
                {/* Status and Task Badges */}
                <div className="flex items-center justify-between mb-3">
                  <span className="badge-sky uppercase font-mono">
                    {model.healthcare_task === 'diabetes_prediction' ? 'Task 1 • Diabetes' : 'Task 2 • Heart Disease'}
                  </span>
                  {getStatusBadge(model.status)}
                </div>

                {/* Title & Description */}
                <h3 className="text-lg font-bold text-slate-900 tracking-tight">
                  {model.name}
                </h3>
                <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                  {model.description}
                </p>

                {/* Architecture & Specs */}
                <div className="mt-4 grid grid-cols-3 gap-2 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                  <div>
                    <span className="text-slate-500 text-[10px] uppercase font-semibold">Architecture</span>
                    <p className="font-mono text-sky-700 text-xs mt-0.5 truncate">{model.architecture}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[10px] uppercase font-semibold">Version</span>
                    <p className="font-mono text-slate-900 text-xs mt-0.5">{model.version}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[10px] uppercase font-semibold">Target</span>
                    <p className="font-mono text-emerald-700 text-xs mt-0.5 truncate">{model.target_variable}</p>
                  </div>
                </div>

                {/* Client Accessibility Banner */}
                <div className="mt-4 p-3 rounded-lg bg-slate-50 border border-slate-200 text-[11px]">
                  <span className="text-slate-500 font-medium">Client Access Status: </span>
                  {model.status === 'active' ? (
                    <span className="text-emerald-700 font-semibold">
                      Unlocked — Visible on Client "Available Models" page & Ready for Training
                    </span>
                  ) : model.status === 'published' ? (
                    <span className="text-amber-700 font-semibold">
                      Published — Still hidden from clients until Activated (Rule 1)
                    </span>
                  ) : model.status === 'uploaded' ? (
                    <span className="text-indigo-700 font-semibold">
                      Uploaded — Hidden from clients until Published & Activated
                    </span>
                  ) : (
                    <span className="text-slate-500 font-semibold">
                      Locked — Client sees "No healthcare models are currently available"
                    </span>
                  )}
                </div>
              </div>

              {/* State Machine Transition Controls */}
              <div className="mt-6 pt-4 border-t border-slate-100 space-y-2">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                  Model Lifecycle Controls (Draft → Uploaded → Published → Active):
                </span>
                <div className="flex flex-wrap items-center gap-2">
                  {/* DRAFT → UPLOADED / PUBLISHED */}
                  {model.status === 'draft' && (
                    <>
                      <button
                        disabled={updatingId === model.id}
                        onClick={() => handleUpdateStatus(model.id, 'uploaded')}
                        className="btn-secondary"
                      >
                        <UploadCloud className="w-3.5 h-3.5 text-indigo-600" />
                        <span>Upload (Draft → Uploaded)</span>
                      </button>
                      <button
                        disabled={updatingId === model.id}
                        onClick={() => handleUpdateStatus(model.id, 'published')}
                        className="btn-kaggle"
                      >
                        <Globe className="w-3.5 h-3.5" />
                        <span>Publish (Draft → Published)</span>
                      </button>
                    </>
                  )}

                  {/* UPLOADED → PUBLISHED */}
                  {model.status === 'uploaded' && (
                    <button
                      disabled={updatingId === model.id}
                      onClick={() => handleUpdateStatus(model.id, 'published')}
                      className="btn-kaggle"
                    >
                      <Globe className="w-3.5 h-3.5" />
                      <span>Publish (Uploaded → Published)</span>
                    </button>
                  )}

                  {/* PUBLISHED → ACTIVE */}
                  {model.status === 'published' && (
                    <button
                      disabled={updatingId === model.id}
                      onClick={() => handleUpdateStatus(model.id, 'active')}
                      className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-xs transition-all cursor-pointer"
                    >
                      <Power className="w-3.5 h-3.5" />
                      <span>Activate (Published → Active)</span>
                    </button>
                  )}

                  {/* ACTIVE → INACTIVE */}
                  {model.status === 'active' && (
                    <button
                      disabled={updatingId === model.id}
                      onClick={() => handleUpdateStatus(model.id, 'inactive')}
                      className="btn-secondary text-amber-700 border-amber-200 hover:bg-amber-50"
                    >
                      <Power className="w-3.5 h-3.5 text-amber-600" />
                      <span>Deactivate (Active → Inactive)</span>
                    </button>
                  )}

                  {/* INACTIVE → ACTIVE (Re-activate) */}
                  {model.status === 'inactive' && (
                    <button
                      disabled={updatingId === model.id}
                      onClick={() => handleUpdateStatus(model.id, 'active')}
                      className="btn-kaggle"
                    >
                      <Power className="w-3.5 h-3.5" />
                      <span>Re-Activate</span>
                    </button>
                  )}

                  {/* Archive */}
                  {model.status !== 'archived' && model.status !== 'draft' && (
                    <button
                      disabled={updatingId === model.id}
                      onClick={() => handleUpdateStatus(model.id, 'archived')}
                      className="btn-secondary"
                    >
                      <Archive className="w-3.5 h-3.5 text-slate-400" />
                      <span>Archive</span>
                    </button>
                  )}

                  {/* Revert to Draft */}
                  {model.status !== 'draft' && (
                    <button
                      disabled={updatingId === model.id}
                      onClick={() => handleUpdateStatus(model.id, 'draft')}
                      className="btn-secondary"
                    >
                      <span>Set Draft (Hide)</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminModels;
