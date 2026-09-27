import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import type { Dataset } from '../../types';
import {
  Database,
  Upload,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Info,
  Sparkles,
  BarChart2,
  Table,
  X,
  Send,
  XCircle,
  Users,
} from 'lucide-react';

export const AdminDatasets: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [distributingId, setDistributingId] = useState<number | null>(null);

  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadName, setUploadName] = useState('');
  const [uploadTask, setUploadTask] = useState<'diabetes_prediction' | 'heart_disease_prediction'>('diabetes_prediction');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const fetchDatasets = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<Dataset[]>('/admin/datasets');
      setDatasets(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch healthcare datasets.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDatasets(); }, []);

  const handleInitializeBenchmarks = async () => {
    setLoading(true);
    try {
      await api.post('/admin/datasets/initialize-benchmarks');
      await fetchDatasets();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initialize benchmark datasets.');
      setLoading(false);
    }
  };

  const handleToggleStatus = async (dataset: Dataset) => {
    const nextStatus = dataset.status === 'active' ? 'inactive' : 'active';
    try {
      const res = await api.patch<Dataset>(`/admin/datasets/${dataset.id}/status`, { status: nextStatus });
      setDatasets(prev => prev.map(d => d.id === dataset.id ? res.data : d));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update dataset status.');
    }
  };

  const handleDistribute = async (dataset: Dataset) => {
    setDistributingId(dataset.id);
    try {
      const endpoint = dataset.is_distributed
        ? `/admin/datasets/${dataset.id}/recall`
        : `/admin/datasets/${dataset.id}/distribute`;
      const res = await api.post<Dataset>(endpoint);
      setDatasets(prev => prev.map(d => d.id === dataset.id ? res.data : d));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update distribution status.');
    } finally {
      setDistributingId(null);
    }
  };

  const handleInspectDataset = async (datasetId: number) => {
    try {
      const res = await api.get<Dataset>(`/admin/datasets/${datasetId}`);
      setSelectedDataset(res.data);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to load dataset details.');
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) { setUploadError('Please select a valid CSV file.'); return; }
    setUploading(true); setUploadError(null); setUploadSuccess(null);
    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('name', uploadName.trim());
    formData.append('healthcare_task', uploadTask);
    try {
      const res = await api.post('/admin/datasets/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadSuccess(res.data.message);
      setUploadFile(null); setUploadName('');
      setTimeout(() => { setShowUploadModal(false); setUploadSuccess(null); }, 1500);
      await fetchDatasets();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to upload and validate dataset.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="card p-6 bg-white border border-slate-200 rounded-xl shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-sky-700 text-xs font-semibold uppercase tracking-wider mb-1">
            <Database className="w-4 h-4 text-sky-600" />
            <span>Healthcare Data Repository (Coordinator Side)</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Healthcare Dataset Management</h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage, validate, and <strong className="text-sky-700">distribute datasets to client nodes</strong> for manual local training.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button onClick={handleInitializeBenchmarks} className="btn-secondary" title="Generate benchmark datasets">
            <RefreshCw className="w-3.5 h-3.5 text-sky-600" /><span>Init Benchmarks</span>
          </button>
          <button onClick={() => setShowUploadModal(true)} className="btn-kaggle">
            <Upload className="w-3.5 h-3.5" /><span>Upload Dataset</span>
          </button>
        </div>
      </div>

      {/* Manual Training Workflow Callout */}
      <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-950 flex items-start space-x-3">
        <Users className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-emerald-900">Manual Training Workflow:</span>
          <p className="text-[11px] text-emerald-800 leading-relaxed mt-0.5">
            Click <strong>"Distribute to Clients"</strong> on any active dataset to publish it to all client nodes.
            Clients will see it in their workspace, download the CSV, train locally on their own machine using the provided
            Python script (<code className="bg-white px-1 py-0.5 rounded border border-emerald-300 font-mono">train_local.py</code>),
            and upload the generated{' '}
            <code className="bg-white px-1 py-0.5 rounded border border-emerald-300 font-mono">client_update.json</code> back.
          </p>
        </div>
      </div>

      {/* Clinical Disclaimer */}
      <div className="p-4 rounded-xl bg-sky-50 border border-sky-200 text-xs text-sky-950 flex items-start space-x-3">
        <Info className="w-4 h-4 text-sky-600 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-sky-950">Clinical Experimentation Notice:</span>
          <p className="text-[11px] text-sky-900/80 leading-relaxed mt-0.5">
            Datasets follow authentic Pima Indians and Cleveland Heart Disease schemas for FL experimentation.
            The central server never accesses raw hospital records during federated rounds.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600" /><span>{error}</span>
        </div>
      )}

      {/* Dataset Cards */}
      {loading ? (
        <div className="flex items-center justify-center p-16">
          <div className="w-8 h-8 border-3 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : datasets.length === 0 ? (
        <div className="card p-12 bg-white rounded-xl border border-slate-200 text-center space-y-4 shadow-xs">
          <div className="w-14 h-14 rounded-2xl bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600 mx-auto">
            <Database className="w-7 h-7" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-900">No Healthcare Datasets Registered</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">Initialize the standard benchmark datasets or upload your own CSV dataset.</p>
          </div>
          <button onClick={handleInitializeBenchmarks} className="btn-kaggle">
            <Sparkles className="w-4 h-4" /><span>Generate Diabetes &amp; Heart Disease Datasets</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {datasets.map((dataset) => {
            const class0 = dataset.class_distribution['0'] || 0;
            const class1 = dataset.class_distribution['1'] || 0;
            const total = class0 + class1 || 1;
            const pct0 = Math.round((class0 / total) * 100);
            const pct1 = 100 - pct0;
            const isDistributing = distributingId === dataset.id;

            return (
              <div
                key={dataset.id}
                className={`card p-6 bg-white rounded-xl border hover:shadow-card-hover transition-all flex flex-col justify-between shadow-xs ${
                  dataset.is_distributed ? 'border-emerald-300 bg-emerald-50/20' : 'border-slate-200 hover:border-sky-300'
                }`}
              >
                <div>
                  {/* Top Badges */}
                  <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                    <span className="badge-sky uppercase font-mono">
                      {dataset.healthcare_task === 'diabetes_prediction' ? 'Metabolic Diagnostic' : 'Cardiovascular Diagnostic'}
                    </span>
                    <div className="flex items-center space-x-2">
                      {dataset.is_distributed && (
                        <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                          <span>DISTRIBUTED TO CLIENTS</span>
                        </span>
                      )}
                      <button
                        onClick={() => handleToggleStatus(dataset)}
                        className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium transition-colors cursor-pointer ${
                          dataset.status === 'active' ? 'badge-emerald' : 'badge-slate'
                        }`}
                        title="Click to toggle active/inactive"
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${dataset.status === 'active' ? 'bg-emerald-500' : 'bg-slate-400'}`}></span>
                        <span className="capitalize">{dataset.status}</span>
                      </button>
                    </div>
                  </div>

                  {/* Title */}
                  <h3 className="text-lg font-bold text-slate-900 tracking-tight">{dataset.name}</h3>
                  <p className="text-xs text-slate-500 font-mono mt-1">File: <span className="text-slate-700">{dataset.filename}</span></p>
                  {dataset.is_distributed && dataset.distributed_at && (
                    <p className="text-[11px] text-emerald-700 font-mono mt-1 flex items-center space-x-1">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Distributed on {new Date(dataset.distributed_at).toLocaleString()}</span>
                    </p>
                  )}

                  {/* Metadata Grid */}
                  <div className="mt-4 grid grid-cols-3 gap-3 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                    <div>
                      <span className="text-slate-500 text-[10px] uppercase font-semibold">Records</span>
                      <p className="font-bold text-slate-900 text-sm mt-0.5">{dataset.record_count.toLocaleString()}</p>
                    </div>
                    <div>
                      <span className="text-slate-500 text-[10px] uppercase font-semibold">Features</span>
                      <p className="font-bold text-sky-700 text-sm mt-0.5">{dataset.feature_count} Inputs</p>
                    </div>
                    <div>
                      <span className="text-slate-500 text-[10px] uppercase font-semibold">Target</span>
                      <p className="font-mono text-emerald-700 text-sm mt-0.5 truncate">{dataset.target_variable}</p>
                    </div>
                  </div>

                  {/* Class Distribution */}
                  <div className="mt-4 space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-600 text-[11px] font-medium flex items-center space-x-1">
                        <BarChart2 className="w-3 h-3 text-sky-600" /><span>Class Distribution:</span>
                      </span>
                      <div className="space-x-3 text-[11px]">
                        <span className="text-slate-600">Negative: <strong className="text-slate-900">{class0} ({pct0}%)</strong></span>
                        <span className="text-slate-600">Positive: <strong className="text-emerald-700">{class1} ({pct1}%)</strong></span>
                      </div>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden flex">
                      <div style={{ width: `${pct0}%` }} className="bg-slate-300 h-full"></div>
                      <div style={{ width: `${pct1}%` }} className="bg-emerald-500 h-full"></div>
                    </div>
                  </div>
                </div>

                {/* Footer Actions */}
                <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between gap-2 flex-wrap">
                  <button onClick={() => handleInspectDataset(dataset.id)} className="btn-secondary">
                    <Table className="w-3.5 h-3.5 text-sky-600" /><span>Feature Dictionary</span>
                  </button>

                  {/* Distribute / Recall Button */}
                  <button
                    onClick={() => handleDistribute(dataset)}
                    disabled={isDistributing || (dataset.status !== 'active' && !dataset.is_distributed)}
                    title={
                      dataset.is_distributed
                        ? 'Recall this dataset from clients'
                        : dataset.status !== 'active'
                        ? 'Dataset must be active to distribute'
                        : 'Distribute to all client nodes for manual training'
                    }
                    className={`inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer shadow-xs disabled:opacity-50 disabled:cursor-not-allowed ${
                      dataset.is_distributed
                        ? 'bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200'
                        : 'bg-emerald-600 hover:bg-emerald-500 text-white'
                    }`}
                  >
                    {isDistributing ? (
                      <><div className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin"></div><span>Processing...</span></>
                    ) : dataset.is_distributed ? (
                      <><XCircle className="w-3.5 h-3.5" /><span>Recall from Clients</span></>
                    ) : (
                      <><Send className="w-3.5 h-3.5" /><span>Distribute to Clients</span></>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Feature Dictionary Modal */}
      {selectedDataset && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 w-full max-w-2xl max-h-[85vh] overflow-y-auto space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <Database className="w-4 h-4 text-sky-600" /><span>{selectedDataset.name} - Feature Dictionary</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">{selectedDataset.feature_count} features total</p>
              </div>
              <button onClick={() => setSelectedDataset(null)} className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] tracking-wider border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-2.5 font-semibold">Feature Name</th>
                    <th className="px-4 py-2.5 font-semibold">Mean</th>
                    <th className="px-4 py-2.5 font-semibold">Std</th>
                    <th className="px-4 py-2.5 font-semibold">Min</th>
                    <th className="px-4 py-2.5 font-semibold">Max</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700 font-mono">
                  {selectedDataset.feature_names.map((feat) => {
                    const stats = selectedDataset.summary_stats?.[feat];
                    return (
                      <tr key={feat} className="hover:bg-slate-50/60 transition-colors">
                        <td className="px-4 py-2.5 font-semibold text-slate-900">{feat}</td>
                        <td className="px-4 py-2.5 text-sky-700">{stats ? stats.mean : '—'}</td>
                        <td className="px-4 py-2.5 text-slate-600">{stats ? stats.std : '—'}</td>
                        <td className="px-4 py-2.5 text-slate-600">{stats ? stats.min : '—'}</td>
                        <td className="px-4 py-2.5 text-slate-600">{stats ? stats.max : '—'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="pt-2 flex justify-end">
              <button onClick={() => setSelectedDataset(null)} className="btn-secondary">Close Dictionary</button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Dataset Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 w-full max-w-md space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center space-x-2">
                <Upload className="w-5 h-5 text-sky-600" />
                <h3 className="text-base font-bold text-slate-900">Upload Healthcare Dataset</h3>
              </div>
              <button onClick={() => setShowUploadModal(false)} className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>
            {uploadError && (
              <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600" /><span>{uploadError}</span>
              </div>
            )}
            {uploadSuccess && (
              <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-600" /><span>{uploadSuccess}</span>
              </div>
            )}
            <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1.5">Dataset Display Name</label>
                <input type="text" required value={uploadName} onChange={(e) => setUploadName(e.target.value)}
                  placeholder="e.g., Clinical Diabetes Cohort 2026"
                  className="w-full bg-white border border-slate-300 focus:border-sky-500 rounded-lg px-3.5 py-2 text-slate-900 outline-none" />
              </div>
              <div>
                <label className="block text-slate-700 font-semibold mb-1.5">Associated Healthcare Task</label>
                <select value={uploadTask} onChange={(e) => setUploadTask(e.target.value as any)}
                  className="w-full bg-white border border-slate-300 focus:border-sky-500 rounded-lg px-3.5 py-2 text-slate-900 outline-none">
                  <option value="diabetes_prediction">Diabetes Prediction (Pima Schema)</option>
                  <option value="heart_disease_prediction">Heart Disease Prediction (Cleveland Schema)</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-700 font-semibold mb-1.5">Select CSV File</label>
                <input type="file" accept=".csv" required onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-700 file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-sky-600 file:text-white hover:file:bg-sky-500 cursor-pointer" />
              </div>
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-600">
                <span className="font-semibold text-slate-800">Validation:</span> File must contain the exact clinical feature columns and binary target variable.
              </div>
              <div className="pt-2 flex items-center justify-end space-x-2">
                <button type="button" onClick={() => setShowUploadModal(false)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={uploading} className="btn-kaggle">
                  {uploading ? <span>Validating Schema...</span> : <><Upload className="w-3.5 h-3.5" /><span>Upload &amp; Validate</span></>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
