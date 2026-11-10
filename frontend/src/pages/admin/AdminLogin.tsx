import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import {
  Server, Lock, Mail, AlertCircle, ArrowLeft,
  ShieldCheck, CheckCircle2, Activity, Database
} from 'lucide-react';
import type { TokenResponse } from '../../types';

export const AdminLogin: React.FC = () => {
  const [email, setEmail] = useState('admin@flplatform.org');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await api.post<TokenResponse>('/auth/login', {
        email: email.trim(),
        password,
      });

      if (response.data.role !== 'admin') {
        setError('Unauthorized: This portal is strictly for the Central FL Coordinator/Admin.');
        setLoading(false);
        return;
      }

      login(response.data);
      navigate('/admin/dashboard');
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Authentication failed. Please verify credentials.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-stretch">

      {/* Left Panel – Branding */}
      <div className="hidden lg:flex lg:w-[45%] relative overflow-hidden flex-col justify-between p-10">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-600 via-indigo-500 to-blue-500" />
        <div className="absolute inset-0 opacity-20" style={{
          backgroundImage: 'radial-gradient(circle at 25% 25%, rgba(255,255,255,0.2) 0%, transparent 50%), radial-gradient(circle at 75% 75%, rgba(255,255,255,0.1) 0%, transparent 50%)',
        }} />
        {/* Grid pattern */}
        <div className="absolute inset-0 opacity-[0.08]" style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(to right, rgba(255,255,255,1) 1px, transparent 1px)',
          backgroundSize: '32px 32px'
        }} />
        {/* Decorative orbs */}
        <div className="absolute bottom-1/4 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl animate-float" />
        <div className="absolute top-1/4 -left-12 w-48 h-48 bg-blue-300/20 rounded-full blur-3xl animate-float-delayed" />

        <div className="relative z-10">
          <Link to="/" className="inline-flex items-center gap-2 text-white/70 hover:text-white text-xs font-medium transition-colors mb-10">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Home
          </Link>
          <div className="w-14 h-14 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center mb-6 border border-white/30 shadow-lg">
            <Server className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-3xl font-black text-white leading-tight tracking-tight mb-3">
            Coordinator<br />Command Center
          </h1>
          <p className="text-indigo-100/80 text-sm leading-relaxed max-w-xs">
            Manage the federated learning lifecycle across all clinical hospital nodes from one secure dashboard.
          </p>
        </div>

        <div className="relative z-10 space-y-3">
          {[
            { icon: <ShieldCheck className="w-4 h-4" />, text: 'FedAvg aggregation & model governance' },
            { icon: <Activity className="w-4 h-4" />, text: 'Live telemetry & security anomaly detection' },
            { icon: <Database className="w-4 h-4" />, text: 'Healthcare dataset & model management' },
            { icon: <CheckCircle2 className="w-4 h-4" />, text: 'Zero local training (Rule 6 enforced)' },
          ].map(item => (
            <div key={item.text} className="flex items-center gap-3 text-white/80 text-xs">
              <div className="w-8 h-8 rounded-lg bg-white/15 flex items-center justify-center flex-shrink-0 text-white/90">
                {item.icon}
              </div>
              {item.text}
            </div>
          ))}
        </div>
      </div>

      {/* Right Panel – Form */}
      <div className="flex-1 flex flex-col items-center justify-center p-8 animate-fade-in-up">
        <div className="w-full max-w-sm">
          {/* Mobile back link */}
          <Link
            to="/"
            className="lg:hidden inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-slate-700 mb-6 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Home
          </Link>

          <div className="mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center shadow-lg shadow-indigo-200 mb-4">
              <Server className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">Admin Portal</h2>
            <p className="text-slate-500 text-sm mt-1">Central FL Coordinator Login</p>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="flex items-center gap-3 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs mb-5">
              <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Admin Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-field pl-10"
                  placeholder="admin@flplatform.org"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Master Security Key
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pl-10"
                  placeholder="admin123"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary justify-center py-3 text-sm mt-2 shadow-lg shadow-indigo-200"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                'Authenticate Central Coordinator'
              )}
            </button>
          </form>

          {/* Quick credential helper */}
          <div className="mt-6 p-3.5 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-between">
            <div className="text-[11px] text-indigo-600/70 font-mono">
              <span className="font-semibold text-indigo-700">Demo credentials</span>
              <div className="mt-0.5 text-indigo-600">admin@flplatform.org</div>
            </div>
            <span className="px-2.5 py-1 rounded-lg bg-white border border-indigo-200 text-indigo-700 font-mono font-bold text-xs shadow-sm">
              admin123
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
export default AdminLogin;
