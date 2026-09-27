import React from 'react';
import { Layers, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface PhasePlaceholderProps {
  title: string;
  targetPhase: string;
  description: string;
}

export const PhasePlaceholder: React.FC<PhasePlaceholderProps> = ({ title, targetPhase, description }) => {
  const navigate = useNavigate();

  return (
    <div className="glass-panel p-8 rounded-2xl border border-slate-800 max-w-2xl mx-auto my-12 text-center space-y-4">
      <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-700/50 flex items-center justify-center text-slate-400 mx-auto">
        <Layers className="w-6 h-6 text-indigo-400" />
      </div>

      <div className="space-y-1">
        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold">
          {targetPhase}
        </span>
        <h2 className="text-xl font-bold text-white tracking-tight">{title}</h2>
        <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
          {description}
        </p>
      </div>

      <div className="pt-4">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return</span>
        </button>
      </div>
    </div>
  );
};
