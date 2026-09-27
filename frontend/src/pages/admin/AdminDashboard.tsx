import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import type { Client, AdminHealthStats } from '../../types';
import { 
  Server, 
  Users, 
  Database, 
  Cpu, 
  FlaskConical, 
  AlertTriangle,
  Lock,
  ArrowRight
} from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<AdminHealthStats | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAdminData = async () => {
      try {
        const [healthRes, clientsRes] = await Promise.all([
          api.get<AdminHealthStats>('/admin/health'),
          api.get<Client[]>('/admin/clients'),
        ]);
        setStats(healthRes.data);
        setClients(clientsRes.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to fetch coordinator status.');
      } finally {
        setLoading(false);
      }
    };

    fetchAdminData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-16">
        <div className="w-8 h-8 border-3 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="card p-6 bg-white border border-slate-200 rounded-xl shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-sky-700 text-xs font-semibold uppercase tracking-wider mb-1">
            <Server className="w-4 h-4 text-sky-600" />
            <span>Central Server Coordinator</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Federated Learning Control Center
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Managing global model aggregation, mathematical security verification, and 3 clinical client nodes.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="badge-emerald flex items-center space-x-2 px-3 py-1.5 rounded-lg shadow-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>FedAvg Coordinator Online</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
          {error.includes("Administrative privileges required") && (
            <button
              onClick={() => {
                logout();
                navigate('/admin/login');
              }}
              className="px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs transition-colors shrink-0 cursor-pointer shadow-xs"
            >
              Sign In with Admin Account (admin@flplatform.org)
            </button>
          )}
        </div>
      )}

      {/* Top-Level Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="card p-5 bg-white border border-slate-200 rounded-xl shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500 font-medium">Active Clinical Clients</span>
            <div className="w-9 h-9 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-600 flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline">
            <span className="text-2xl font-extrabold text-slate-900">{stats?.active_clients || 3}</span>
            <span className="text-xs text-emerald-600 ml-2 font-semibold">100% Online</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Hospitals A, B, and C connected</p>
        </div>

        {/* Metric 2: Healthcare Datasets */}
        <div 
          onClick={() => navigate('/admin/datasets')}
          className="card p-5 bg-white border border-slate-200 hover:border-sky-300 hover:shadow-card-hover cursor-pointer transition-all rounded-xl shadow-xs group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500 font-medium group-hover:text-sky-700 transition-colors">Healthcare Datasets</span>
            <div className="w-9 h-9 rounded-lg bg-sky-50 border border-sky-200 text-sky-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Database className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-2xl font-extrabold text-slate-900">{stats?.datasets_count || 0}</span>
              <span className="text-xs text-slate-500 ml-2 font-medium">Admin Managed</span>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-sky-600 group-hover:translate-x-0.5 transition-all" />
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Diabetes & Heart Disease benchmarks</p>
        </div>

        {/* Metric 3: Published Models */}
        <div 
          onClick={() => navigate('/admin/models')}
          className="card p-5 bg-white border border-slate-200 hover:border-purple-300 hover:shadow-card-hover cursor-pointer transition-all rounded-xl shadow-xs group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500 font-medium group-hover:text-purple-700 transition-colors">Published Models</span>
            <div className="w-9 h-9 rounded-lg bg-purple-50 border border-purple-200 text-purple-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Cpu className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-2xl font-extrabold text-slate-900">{stats?.models_count || 0}</span>
              <span className="text-xs text-purple-600 ml-2 font-semibold">Availability Controller</span>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-purple-600 group-hover:translate-x-0.5 transition-all" />
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Publish to unlock client training (Rule 10)</p>
        </div>

        {/* Metric 4 */}
        <div 
          onClick={() => navigate('/admin/experiments')}
          className="card p-5 bg-white border border-slate-200 hover:border-indigo-300 hover:shadow-card-hover cursor-pointer transition-all rounded-xl shadow-xs group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500 font-medium group-hover:text-indigo-700 transition-colors">FL Experiments</span>
            <div className="w-9 h-9 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <FlaskConical className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-2xl font-extrabold text-slate-900">{stats?.experiments_count || 0}</span>
              <span className="text-xs text-indigo-600 ml-2 font-semibold">Federation Engine</span>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all" />
          </div>
          <p className="text-[11px] text-slate-400 mt-1">FedAvg round orchestration</p>
        </div>
      </div>

      {/* Three Clinical Clients Status Table (Rule 15 & 16) */}
      <div className="card bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
              <Users className="w-4 h-4 text-sky-600" />
              <span>Participating Healthcare Client Institutions</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Three isolated institutions participating in decentralized training runs.
            </p>
          </div>
          <div className="flex items-center space-x-1.5 text-xs text-emerald-800 font-medium px-3 py-1 rounded-lg bg-emerald-50 border border-emerald-200 w-fit">
            <Lock className="w-3.5 h-3.5 text-emerald-600" />
            <span>Zero Raw Patient Data Transfer Enforced</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-5 py-3 font-semibold">Client ID</th>
                <th className="px-5 py-3 font-semibold">Institution Name</th>
                <th className="px-5 py-3 font-semibold">Type</th>
                <th className="px-5 py-3 font-semibold">Location</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                <th className="px-5 py-3 font-semibold">Privacy Boundary</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-slate-700">
              {clients.map((client) => (
                <tr key={client.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-5 py-3.5 font-mono text-sky-700 font-medium">
                    {client.id}
                  </td>
                  <td className="px-5 py-3.5 font-semibold text-slate-900">
                    {client.name}
                  </td>
                  <td className="px-5 py-3.5 text-slate-500">
                    {client.institution_type}
                  </td>
                  <td className="px-5 py-3.5 text-slate-500">
                    {client.location || 'Local Secure Network'}
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="badge-emerald inline-flex items-center space-x-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                      <span>Active</span>
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="badge-sky inline-flex items-center space-x-1 font-mono">
                      <Lock className="w-3 h-3 text-sky-600" />
                      <span>Isolated Local Data</span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model Availability Control Rule Callout */}
      <div className="p-5 rounded-xl bg-indigo-50/70 border border-indigo-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start space-x-3.5">
          <div className="w-9 h-9 rounded-lg bg-white border border-indigo-200 text-indigo-600 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-xs">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-indigo-950">
              Model Availability State Machine (Rule 10 & 17)
            </h3>
            <p className="text-xs text-indigo-900/80 mt-0.5 leading-relaxed">
              Global model availability directly controls client access. Clients logging in will see the published benchmark tasks:
              <span className="font-semibold text-indigo-950"> Diabetes Risk Classifier</span> and 
              <span className="font-semibold text-indigo-950"> Heart Disease Risk Classifier</span>. 
              Client nodes train locally with isolated institutional data and contribute mathematical parameter updates.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 flex-shrink-0">
          <span className="badge-indigo font-mono">
            Phase 1–15 Active
          </span>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
