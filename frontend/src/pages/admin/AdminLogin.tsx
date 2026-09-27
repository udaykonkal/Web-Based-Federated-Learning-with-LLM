import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { Server, Lock, Mail, AlertCircle, ArrowLeft, ShieldCheck } from 'lucide-react';
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
    <div className="min-h-[calc(100vh-61px)] flex items-center justify-center p-6 bg-[#F8F9FA] text-[#202124]">
      <div className="w-full max-w-md">
        <Link 
          to="/" 
          className="inline-flex items-center space-x-1.5 text-xs font-medium text-gray-500 hover:text-gray-800 mb-6 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Home</span>
        </Link>

        <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm relative">
          {/* Header */}
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900 tracking-tight">Admin Portal</h1>
              <p className="text-xs text-indigo-700 font-medium">Central FL Coordinator Login</p>
            </div>
          </div>

          {/* Architectural Rule 6 Reminder */}
          <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-200 text-[11px] text-indigo-800 flex items-start space-x-2 mb-6">
            <ShieldCheck className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
            <p>
              Coordinator authority: You manage healthcare models, verify client updates, and run FedAvg. Central server performs zero local training.
            </p>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2 mb-4">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                Admin Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-white border border-gray-300 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg pl-9 pr-3 py-2 text-xs text-gray-900 placeholder-gray-400 outline-none transition-all"
                  placeholder="admin@flplatform.org"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                Master Security Key
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white border border-gray-300 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg pl-9 pr-3 py-2 text-xs text-gray-900 placeholder-gray-400 outline-none transition-all"
                  placeholder="admin123"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-xs flex items-center justify-center space-x-2 transition-colors cursor-pointer shadow-xs mt-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <span>Authenticate Central Coordinator</span>
              )}
            </button>
          </form>

          {/* Quick Credential Helper */}
          <div className="mt-6 pt-4 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-500 font-mono">
            <span>Pre-seeded Credential:</span>
            <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-700 font-bold">admin123</span>
          </div>
        </div>
      </div>
    </div>
  );
};
export default AdminLogin;
