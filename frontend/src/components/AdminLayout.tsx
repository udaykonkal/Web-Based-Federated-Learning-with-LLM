import React from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { AlertTriangle, ArrowRight } from 'lucide-react';

export const AdminLayout: React.FC = () => {
  const { role, email, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col antialiased">
      <Navbar />

      {/* Role Context Mismatch Banner */}
      {role === 'client' && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-200 px-6 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-amber-900">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-amber-100 border border-amber-200 flex items-center justify-center flex-shrink-0">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            </div>
            <span>
              You are currently logged in with a <strong>Clinical Client Node account</strong> ({email}).
              Coordinator endpoints require Administrative privileges.
            </span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => { logout(); navigate('/admin/login'); }}
              className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg font-semibold text-xs transition-colors flex items-center gap-1.5 cursor-pointer shadow-sm"
            >
              <span>Sign In as Admin</span>
              <ArrowRight className="w-3 h-3" />
            </button>
            <button
              onClick={() => navigate('/client/models')}
              className="px-3 py-1.5 bg-white border border-amber-200 hover:bg-amber-50 text-amber-800 rounded-lg text-xs font-medium transition-colors cursor-pointer"
            >
              Go to Clinical Node
            </button>
          </div>
        </div>
      )}

      <div className="flex flex-1 w-full">
        <Sidebar />
        <main className="flex-1 p-6 lg:p-8 overflow-x-hidden min-h-0">
          <div className="max-w-[1400px] mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
