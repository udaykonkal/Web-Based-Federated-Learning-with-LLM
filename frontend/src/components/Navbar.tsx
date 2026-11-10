import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, LogOut, Server, Building2, Lock, ArrowRightLeft } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { isAuthenticated, role, email, clientId, institutionName, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur-xl border-b border-slate-100 shadow-sm">
      <div className="max-w-[1600px] mx-auto px-6 py-3 flex items-center justify-between">

        {/* Brand */}
        <div
          onClick={() => navigate('/')}
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <div className="w-9 h-9 rounded-xl gradient-brand flex items-center justify-center shadow-md shadow-indigo-200 group-hover:shadow-lg group-hover:shadow-indigo-300 transition-all duration-200">
            <Shield className="w-4 h-4 text-white" strokeWidth={2.5} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-slate-900 tracking-tight group-hover:text-indigo-600 transition-colors">
                FedHealth
              </span>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-600 border border-indigo-100">
                FL Platform
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium leading-none mt-0.5">
              Healthcare Federated Learning Workbench
            </p>
          </div>
        </div>

        {/* Right Actions */}
        {isAuthenticated ? (
          <div className="flex items-center gap-3">

            {/* Role badge */}
            {role === 'admin' ? (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold">
                <Server className="w-3.5 h-3.5 text-indigo-500" />
                <span>Central Coordinator</span>
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-sky-50 border border-sky-100 text-sky-700 text-xs font-semibold">
                <Building2 className="w-3.5 h-3.5 text-sky-500" />
                <span>{institutionName || clientId}</span>
                <div className="flex items-center gap-1 pl-2 border-l border-sky-200 text-emerald-600 font-semibold text-[10px]">
                  <Lock className="w-3 h-3" />
                  <span>Isolated</span>
                </div>
              </div>
            )}

            {/* Email */}
            <div className="hidden md:block text-right">
              <p className="text-xs font-semibold text-slate-800">{email}</p>
              <p className="text-[10px] text-slate-400 font-mono uppercase font-medium">{role} context</p>
            </div>

            {/* Switch portal */}
            {role === 'client' ? (
              <button
                onClick={() => { logout(); navigate('/admin/login'); }}
                className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 text-xs font-semibold transition-all cursor-pointer hover:border-slate-300"
                title="Switch to Admin Coordinator Portal"
              >
                <ArrowRightLeft className="w-3 h-3 text-slate-400" />
                <span>Switch to Admin</span>
              </button>
            ) : (
              <button
                onClick={() => { logout(); navigate('/client/login'); }}
                className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 text-xs font-semibold transition-all cursor-pointer hover:border-slate-300"
                title="Switch to Healthcare Client Portal"
              >
                <ArrowRightLeft className="w-3 h-3 text-slate-400" />
                <span>Switch to Client</span>
              </button>
            )}

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 border border-slate-200 text-slate-500 text-xs font-semibold transition-all cursor-pointer"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Logout</span>
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => navigate('/client/login')}
              className="btn-secondary text-xs py-2 px-4"
            >
              Client Node Access
            </button>
            <button
              onClick={() => navigate('/admin/login')}
              className="btn-primary text-xs py-2 px-4"
            >
              Coordinator Portal
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};
export default Navbar;
