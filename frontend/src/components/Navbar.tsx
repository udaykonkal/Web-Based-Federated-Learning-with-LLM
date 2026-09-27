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
    <nav className="border-b border-slate-200 bg-white sticky top-0 z-50 px-6 py-2.5 shadow-xs">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand (Kaggle / Linear Minimal Style) */}
        <div 
          onClick={() => navigate('/')} 
          className="flex items-center space-x-3 cursor-pointer group select-none"
        >
          <div className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center text-white shadow-xs group-hover:bg-sky-600 transition-colors">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-base text-slate-900 tracking-tight group-hover:text-sky-600 transition-colors">
                FedHealth
              </span>
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">
                FL Platform
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium">Healthcare Federated Learning Workbench</p>
          </div>
        </div>

        {/* User context & actions */}
        {isAuthenticated ? (
          <div className="flex items-center space-x-3 text-xs">
            {role === 'admin' ? (
              <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 font-medium shadow-xs">
                <Server className="w-3.5 h-3.5 text-indigo-600" />
                <span className="font-semibold">Central Coordinator</span>
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              </div>
            ) : (
              <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-700 font-medium shadow-xs">
                <Building2 className="w-3.5 h-3.5 text-sky-600" />
                <span className="font-semibold">{institutionName || clientId}</span>
                <div className="flex items-center space-x-1 pl-1 text-[11px] text-emerald-700 border-l border-slate-200 font-semibold">
                  <Lock className="w-3 h-3 text-emerald-600" />
                  <span>Isolated Node</span>
                </div>
              </div>
            )}

            <div className="text-right hidden md:block">
              <p className="text-xs font-semibold text-slate-800">{email}</p>
              <p className="text-[10px] text-slate-400 uppercase font-mono font-medium">{role} context</p>
            </div>

            {/* Quick Switch Portal */}
            {role === 'client' ? (
              <button
                onClick={() => {
                  logout();
                  navigate('/admin/login');
                }}
                className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors cursor-pointer font-medium"
                title="Switch to Admin Coordinator Portal"
              >
                <ArrowRightLeft className="w-3 h-3 text-slate-500" />
                <span>Switch to Admin</span>
              </button>
            ) : (
              <button
                onClick={() => {
                  logout();
                  navigate('/client/login');
                }}
                className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors cursor-pointer font-medium"
                title="Switch to Healthcare Client Portal"
              >
                <ArrowRightLeft className="w-3 h-3 text-slate-500" />
                <span>Switch to Client</span>
              </button>
            )}

            <button
              onClick={handleLogout}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-white hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200 border border-slate-200 text-slate-600 transition-colors cursor-pointer font-medium shadow-xs"
              title="Sign out of platform"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Logout</span>
            </button>
          </div>
        ) : (
          <div className="flex items-center space-x-2 text-xs">
            <button
              onClick={() => navigate('/client/login')}
              className="px-3.5 py-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold transition-colors cursor-pointer shadow-xs"
            >
              Client Node Access
            </button>
            <button
              onClick={() => navigate('/admin/login')}
              className="px-3.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-semibold transition-colors shadow-xs cursor-pointer"
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
