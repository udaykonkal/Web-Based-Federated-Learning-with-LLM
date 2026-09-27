import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { Building2, Lock, Mail, AlertCircle, ArrowLeft, ShieldCheck } from 'lucide-react';
import type { TokenResponse } from '../../types';

export const ClientLogin: React.FC = () => {
  const [email, setEmail] = useState('hospital_a@flplatform.org');
  const [password, setPassword] = useState('client1pass');
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
            <div className="w-10 h-10 rounded-lg bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900 tracking-tight">Clinical Client Node</h1>
              <p className="text-xs text-sky-700 font-medium">Healthcare Institution FL Login</p>
            </div>
          </div>

          {/* Quick Institutional Account Selector */}
          <div className="mb-6">
            <p className="text-[11px] font-semibold text-gray-500 mb-2 font-mono uppercase">Institutional Client Node:</p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleSelectClient('hospital_a@flplatform.org', 'client1pass')}
                className={`px-2 py-2 rounded-lg text-center border transition-all text-xs cursor-pointer ${
                  email.includes('hospital_a')
                    ? 'bg-sky-50 border-sky-300 text-sky-700 font-bold'
                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                <div className="font-bold text-xs">Hospital A</div>
                <div className="text-[10px] text-gray-400 font-mono">client_1</div>
              </button>

              <button
                type="button"
                onClick={() => handleSelectClient('hospital_b@flplatform.org', 'client2pass')}
                className={`px-2 py-2 rounded-lg text-center border transition-all text-xs cursor-pointer ${
                  email.includes('hospital_b')
                    ? 'bg-sky-50 border-sky-300 text-sky-700 font-bold'
                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                <div className="font-bold text-xs">Hospital B</div>
                <div className="text-[10px] text-gray-400 font-mono">client_2</div>
              </button>

              <button
                type="button"
                onClick={() => handleSelectClient('hospital_c@flplatform.org', 'client3pass')}
                className={`px-2 py-2 rounded-lg text-center border transition-all text-xs cursor-pointer ${
                  email.includes('hospital_c')
                    ? 'bg-sky-50 border-sky-300 text-sky-700 font-bold'
                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                <div className="font-bold text-xs">Hospital C</div>
                <div className="text-[10px] text-gray-400 font-mono">client_3</div>
              </button>
            </div>
          </div>

          {/* Privacy Guarantee */}
          <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-[11px] text-emerald-800 flex items-start space-x-2 mb-6">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <p>
              Local Privacy Enforced: Patient records remain strictly inside this client environment. You train PyTorch models locally and transmit only weight updates.
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
                Institutional Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-white border border-gray-300 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 rounded-lg pl-9 pr-3 py-2 text-xs text-gray-900 placeholder-gray-400 outline-none transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                Client Key / Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white border border-gray-300 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 rounded-lg pl-9 pr-3 py-2 text-xs text-gray-900 placeholder-gray-400 outline-none transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 px-4 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-semibold text-xs flex items-center justify-center space-x-2 transition-colors cursor-pointer shadow-xs mt-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <span>Access Clinical Node Workspace</span>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
export default ClientLogin;
