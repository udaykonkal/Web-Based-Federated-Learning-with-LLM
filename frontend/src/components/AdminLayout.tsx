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
    <div className="min-h-screen bg-canvas text-slate-900 flex flex-col antialiased">
      <Navbar />

      {/* Role Context Mismatch Banner */}
      {role === 'client' && (
        <div className="bg-amber-50 border-b border-amber-200 px-6 py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-amber-900">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              You are currently logged in with a <strong>Clinical Client Node account</strong> ({email}). Coordinator endpoints require Administrative privileges.
            </span>
          </div>
          <div className="flex items-center space-x-2 shrink-0">
            <button
              onClick={() => {
                logout();
                navigate('/admin/login');
              }}
              className="px-3 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded font-semibold text-xs transition-colors flex items-center space-x-1 cursor-pointer"
            >
              <span>Sign In as Admin</span>
              <ArrowRight className="w-3 h-3" />
            </button>
            <button
              onClick={() => navigate('/client/models')}
              className="px-3 py-1 bg-white border border-amber-300 hover:bg-amber-50 text-amber-800 rounded text-xs transition-colors cursor-pointer"
            >
              Go to Clinical Node
            </button>
          </div>
        </div>
      )}

      <div className="flex flex-1 w-full">
        <Sidebar />
        <main className="flex-1 p-6 lg:p-8 max-w-[1536px] mx-auto w-full overflow-x-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
