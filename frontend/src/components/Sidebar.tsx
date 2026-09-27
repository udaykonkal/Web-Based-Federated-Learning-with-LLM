import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Database, 
  Cpu, 
  FlaskConical, 
  Radio, 
  ShieldAlert, 
  BarChart3, 
  Bot, 
  Users, 
  Network,
  ShieldCheck
} from 'lucide-react';

interface NavSection {
  title: string;
  items: {
    label: string;
    path: string;
    icon: React.ReactNode;
    badge?: string;
    badgeColor?: string;
  }[];
}

export const Sidebar: React.FC = () => {
  const sections: NavSection[] = [
    {
      title: 'Federation Management',
      items: [
        { label: 'Control Center', path: '/admin/dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
        { label: 'Clinical Clients', path: '/admin/clients', icon: <Users className="w-4 h-4" />, badge: '3 Nodes', badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
        { label: 'Healthcare Datasets', path: '/admin/datasets', icon: <Database className="w-4 h-4" /> },
        { label: 'Healthcare Models', path: '/admin/models', icon: <Cpu className="w-4 h-4" /> },
        { label: 'FL Experiments', path: '/admin/experiments', icon: <FlaskConical className="w-4 h-4" /> },
      ],
    },
    {
      title: 'Real-Time & Security',
      items: [
        { label: 'Live Telemetry', path: '/admin/telemetry', icon: <Radio className="w-4 h-4" />, badge: 'Live', badgeColor: 'bg-sky-50 text-sky-700 border-sky-200' },
        { label: 'Security & Anomalies', path: '/admin/security', icon: <ShieldAlert className="w-4 h-4" /> },
        { label: 'Bandwidth & Comp.', path: '/admin/communication', icon: <Network className="w-4 h-4" /> },
      ],
    },
    {
      title: 'Intelligence & Reporting',
      items: [
        { label: 'Analytics & Baseline', path: '/admin/analytics', icon: <BarChart3 className="w-4 h-4" /> },
        { label: 'LLM Automation', path: '/admin/llm', icon: <Bot className="w-4 h-4" />, badge: 'AI', badgeColor: 'bg-indigo-50 text-indigo-700 border-indigo-200' },
      ],
    },
  ];

  return (
    <aside className="w-64 shrink-0 border-r border-slate-200 bg-white flex flex-col justify-between p-4 min-h-[calc(100vh-57px)] select-none">
      <div className="space-y-6">
        {sections.map((section) => (
          <div key={section.title}>
            <p className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2 font-mono">
              {section.title}
            </p>
            <nav className="space-y-0.5">
              {section.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-sky-50 text-sky-800 font-bold border border-sky-200 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                    }`
                  }
                >
                  <div className="flex items-center space-x-2.5">
                    <span className="text-slate-500">{item.icon}</span>
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded border font-semibold ${item.badgeColor || 'bg-slate-100 text-slate-600 border-slate-200'}`}>
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              ))}
            </nav>
          </div>
        ))}

        {/* Rule 6 Architectural Notice */}
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs">
          <div className="flex items-center space-x-1.5 text-amber-800 font-semibold mb-1">
            <ShieldCheck className="w-3.5 h-3.5 text-amber-600" />
            <span className="font-mono text-[11px] uppercase">Rule 6 Enforced</span>
          </div>
          <p className="text-[11px] text-slate-600 leading-relaxed">
            Central server aggregates model weights only. Local PyTorch training is isolated to clinical clients.
          </p>
        </div>
      </div>

      {/* Footer System Status */}
      <div className="pt-3 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-500">
        <div>
          <p className="font-bold text-slate-700 font-mono">FedHealth v1.0</p>
          <p className="text-[10px] text-slate-400">FedAvg Protocol</p>
        </div>
        <div className="flex items-center space-x-1 font-mono text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Online</span>
        </div>
      </div>
    </aside>
  );
};
export default Sidebar;
