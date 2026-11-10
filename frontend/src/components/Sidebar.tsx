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

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  badge?: string;
  badgeClass?: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

export const Sidebar: React.FC = () => {
  const sections: NavSection[] = [
    {
      title: 'Federation',
      items: [
        { label: 'Control Center', path: '/admin/dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
        { label: 'Clinical Clients', path: '/admin/clients', icon: <Users className="w-4 h-4" />, badge: '3 Nodes', badgeClass: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
        { label: 'Datasets', path: '/admin/datasets', icon: <Database className="w-4 h-4" /> },
        { label: 'Models', path: '/admin/models', icon: <Cpu className="w-4 h-4" /> },
        { label: 'FL Experiments', path: '/admin/experiments', icon: <FlaskConical className="w-4 h-4" /> },
      ],
    },
    {
      title: 'Real-Time',
      items: [
        { label: 'Live Telemetry', path: '/admin/telemetry', icon: <Radio className="w-4 h-4" />, badge: 'Live', badgeClass: 'bg-sky-100 text-sky-600 border-sky-200' },
        { label: 'Security & Anomalies', path: '/admin/security', icon: <ShieldAlert className="w-4 h-4" /> },
        { label: 'Bandwidth & Comp.', path: '/admin/communication', icon: <Network className="w-4 h-4" /> },
      ],
    },
    {
      title: 'Intelligence',
      items: [
        { label: 'Analytics & Baseline', path: '/admin/analytics', icon: <BarChart3 className="w-4 h-4" /> },
        { label: 'LLM Automation', path: '/admin/llm', icon: <Bot className="w-4 h-4" />, badge: 'AI', badgeClass: 'bg-violet-100 text-violet-600 border-violet-200' },
      ],
    },
  ];

  return (
    <aside className="w-60 shrink-0 border-r border-slate-100 bg-white flex flex-col min-h-[calc(100vh-57px)] select-none">

      {/* Nav Sections */}
      <div className="flex-1 py-4 px-3 space-y-5">
        {sections.map((section) => (
          <div key={section.title}>
            <p className="section-header mb-2">{section.title}</p>
            <nav className="space-y-0.5">
              {section.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `nav-item ${isActive ? 'active' : ''}`
                  }
                >
                  <div className="flex items-center gap-2.5">
                    <span className="opacity-80">{item.icon}</span>
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border font-bold ${item.badgeClass}`}>
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              ))}
            </nav>
          </div>
        ))}
      </div>

      {/* Architecture Notice */}
      <div className="px-3 pb-2">
        <div className="p-3 rounded-xl bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-100">
          <div className="flex items-center gap-1.5 text-amber-700 font-bold text-[10px] font-mono uppercase tracking-wide mb-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-amber-500" />
            Rule 6 Enforced
          </div>
          <p className="text-[11px] text-amber-800/80 leading-relaxed">
            Central server aggregates model weights only. Local PyTorch training is isolated to clinical clients.
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="px-3 pb-4 pt-3 border-t border-slate-100 flex items-center justify-between">
        <div>
          <p className="text-xs font-bold text-slate-700 font-mono">FedHealth v1.0</p>
          <p className="text-[10px] text-slate-400 font-mono">FedAvg Protocol</p>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] font-mono font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-lg border border-emerald-100">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          Online
        </div>
      </div>
    </aside>
  );
};
export default Sidebar;
