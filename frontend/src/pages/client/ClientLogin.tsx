import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import {
  Building2, Lock, Mail, AlertCircle, ArrowLeft,
  ShieldCheck, Heart, Activity
} from 'lucide-react';
import type { TokenResponse } from '../../types';

const CLIENTS = [
  { id: 'hospital_a', label: 'Hospital A', email: 'hospital_a@flplatform.org', pass: 'client1pass' },
  { id: 'hospital_b', label: 'Hospital B', email: 'hospital_b@flplatform.org', pass: 'client2pass' },
  { id: 'hospital_c', label: 'Hospital C', email: 'hospital_c@flplatform.org', pass: 'client3pass' },
];

export const ClientLogin: React.FC = () => {
  const [email, setEmail] = useState(CLIENTS[0].email);
  const [password, setPassword] = useState(CLIENTS[0].pass);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSelectClient = (cEmail: string, cPass: string) => {
    setEmail(cEmail);
    setPassword(cPass);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await api.post<TokenResponse>('/auth/login', {
        email: email.trim(),
        password,
      });

      if (response.data.role !== 'client') {
        setError('Unauthorized: Please use the Admin portal for coordinator credentials.');
        setLoading(false);
        return;
      }

      login(response.data);
      navigate('/client/models');
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Authentication failed. Please verify institutional credentials.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-stretch">

      {/* Left Panel – Branding */}
      <div className="hidden lg:flex lg:w-[45%] relative overflow-hidden flex-col justify-between p-10">
        <div className="absolute inset-0 bg-gradient-to-br from-sky-500 via-cyan-500 to-teal-500" />
        <div className="absolute inset-0 opacity-[0.08]" style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(to right, rgba(255,255,255,1) 1px, transparent 1px)',
          backgroundSize: '32px 32px'
        }} />
        <div className="absolute bottom-0 right-0 w-72 h-72 bg-white/10 rounded-full blur-3xl animate-float" />
        <div className="absolute top-1/3 -left-16 w-56 h-56 bg-cyan-300/20 rounded-full blur-3xl animate-float-delayed" />

        <div className="relative z-10">
          <Link to="/" className="inline-flex items-center gap-2 text-white/70 hover:text-white text-xs font-medium transition-colors mb-10">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Home
          </Link>
          <div className="w-14 h-14 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center mb-6 border border-white/30 shadow-lg">
            <Building2 className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-3xl font-black text-white leading-tight tracking-tight mb-3">
            Clinical Node<br />Workspace
          </h1>
          <p className="text-cyan-50/80 text-sm leading-relaxed max-w-xs">
            Train federated models locally using your institution's private dataset. Only weight deltas leave your secure environment.
          </p>
        </div>

        <div className="relative z-10 space-y-3">
          {[
            { icon: <Lock className="w-4 h-4" />, text: 'Isolated private non-IID datasets per hospital' },
            { icon: <Activity className="w-4 h-4" />, text: 'PyTorch local training — no data leaves node' },
            { icon: <ShieldCheck className="w-4 h-4" />, text: 'Cryptographic weight delta verification' },
            { icon: <Heart className="w-4 h-4" />, text: 'HIPAA-compliant privacy boundary enforced' },
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
          <Link
            to="/"
            className="lg:hidden inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-slate-700 mb-6 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Home
          </Link>

          <div className="mb-7">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-sky-200 mb-4">
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">Clinical Client Node</h2>
            <p className="text-slate-500 text-sm mt-1">Healthcare Institution FL Login</p>
          </div>

          {/* Hospital Quick Selector */}
          <div className="mb-5">
            <p className="text-[11px] font-bold font-mono text-slate-400 uppercase tracking-widest mb-2.5">
              Select Institution
            </p>
            <div className="grid grid-cols-3 gap-2">
              {CLIENTS.map((client) => {
                const isActive = email === client.email;
                return (
                  <button
                    key={client.id}
                    type="button"
                    onClick={() => handleSelectClient(client.email, client.pass)}
                    className={`relative px-2 py-2.5 rounded-xl text-center border transition-all text-xs font-semibold cursor-pointer ${
                      isActive
                        ? 'bg-sky-50 border-sky-300 text-sky-700 shadow-sm shadow-sky-100'
                        : 'bg-white border-slate-200 text-slate-600 hover:border-sky-200 hover:bg-sky-50/40'
                    }`}
                  >
                    {isActive && (
                      <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-sky-500 border-2 border-white flex items-center justify-center">
                        <span className="w-1 h-1 rounded-full bg-white" />
                      </span>
                    )}
                    <div className="font-bold">{client.label}</div>
                    <div className="text-[9px] font-mono text-slate-400 mt-0.5">{client.id}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Privacy notice */}
          <div className="flex items-start gap-2.5 p-3 rounded-xl bg-emerald-50 border border-emerald-100 text-emerald-700 text-xs mb-5">
            <ShieldCheck className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-px" />
            <p>Patient records remain strictly inside this client environment. Only weight updates are transmitted.</p>
          </div>

          {error && (
            <div className="flex items-center gap-3 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs mb-4">
              <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Institutional Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-field pl-10"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Client Key / Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pl-10"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-sky-500 to-cyan-500 hover:from-sky-400 hover:to-cyan-400 disabled:opacity-60 text-white font-bold text-sm shadow-lg shadow-sky-200 transition-all duration-200 hover:-translate-y-0.5 cursor-pointer mt-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                'Access Clinical Node Workspace'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
export default ClientLogin;
