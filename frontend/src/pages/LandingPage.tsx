import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield,
  Server,
  Building2,
  Lock,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Activity,
  Globe
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white text-slate-900 flex flex-col overflow-x-hidden">

      {/* ── Navbar ────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl gradient-brand flex items-center justify-center shadow-md shadow-indigo-200">
              <Shield className="w-4.5 h-4.5 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <span className="font-bold text-sm text-slate-900 tracking-tight">FedHealth</span>
              <span className="ml-2 text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-600 border border-indigo-100">
                FL Platform
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={() => navigate('/client/login')}
              className="btn-secondary text-xs py-2 px-4"
            >
              Client Login
            </button>
            <button
              onClick={() => navigate('/admin/login')}
              className="btn-primary text-xs py-2 px-4"
            >
              Coordinator Portal
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </header>

      {/* ── Hero ──────────────────────────────────── */}
      <section className="relative flex-1 flex flex-col items-center justify-center text-center px-6 py-20 overflow-hidden">

        {/* Background decorative orbs */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute -top-24 -left-24 w-96 h-96 bg-indigo-100/60 rounded-full blur-3xl animate-float" />
          <div className="absolute -bottom-16 -right-16 w-80 h-80 bg-sky-100/60 rounded-full blur-3xl animate-float-delayed" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-gradient-to-r from-indigo-50 via-sky-50 to-emerald-50 rounded-full blur-3xl opacity-60" />
          {/* Grid pattern */}
          <div className="absolute inset-0 opacity-[0.025]" style={{
            backgroundImage: 'linear-gradient(#6366F1 1px, transparent 1px), linear-gradient(to right, #6366F1 1px, transparent 1px)',
            backgroundSize: '40px 40px'
          }} />
        </div>

        <div className="relative max-w-4xl mx-auto animate-fade-in-up">
          {/* Pill badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-indigo-50 to-sky-50 border border-indigo-100 text-indigo-600 text-xs font-semibold tracking-wide mb-8 shadow-sm">
            <div className="relative">
              <span className="w-2 h-2 rounded-full bg-indigo-500 block" />
              <span className="w-2 h-2 rounded-full bg-indigo-400 block absolute top-0 left-0 animate-ping-slow" />
            </div>
            Decentralized Federated Learning Engine
            <Globe className="w-3.5 h-3.5 text-sky-500" />
          </div>

          {/* Headline */}
          <h1 className="text-4xl md:text-6xl font-black tracking-tight leading-[1.1] mb-6">
            Collaborative ML with{' '}
            <span className="gradient-text">Complete Data Privacy</span>
          </h1>
          <p className="text-slate-500 text-base md:text-lg max-w-2xl mx-auto leading-relaxed mb-10">
            Train and improve medical machine learning models collaboratively across isolated hospital nodes.
            Only mathematical weight deltas are aggregated —{' '}
            <span className="text-slate-700 font-semibold">raw patient records never leave the local client.</span>
          </p>

          {/* Quick action buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center mb-16">
            <button
              onClick={() => navigate('/admin/login')}
              className="btn-primary text-sm py-3 px-6 shadow-lg shadow-indigo-200/60"
            >
              <Server className="w-4 h-4" />
              Enter Coordinator Portal
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate('/client/login')}
              className="btn-secondary text-sm py-3 px-6"
            >
              <Building2 className="w-4 h-4 text-sky-500" />
              Clinical Client Access
            </button>
          </div>

          {/* Stats Strip */}
          <div className="flex flex-wrap justify-center gap-8 text-center mb-4">
            {[
              { value: '3', label: 'Isolated Hospital Nodes' },
              { value: '0%', label: 'Raw Data Leakage' },
              { value: 'FedAvg', label: 'Aggregation Protocol' },
            ].map(stat => (
              <div key={stat.label}>
                <div className="text-2xl font-black gradient-text">{stat.value}</div>
                <div className="text-xs text-slate-500 font-medium mt-0.5">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Role Cards ────────────────────────────── */}
      <section className="bg-gradient-to-b from-white to-slate-50 px-6 pb-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10">
            <p className="text-xs font-mono font-bold text-slate-400 uppercase tracking-widest mb-2">Access Portals</p>
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">Choose Your Role</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

            {/* Admin Card */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col gap-5 shadow-sm hover-glow-indigo transition-all duration-300 group">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-200 flex-shrink-0">
                  <Server className="w-5.5 h-5.5 text-white" />
                </div>
                <div>
                  <div className="text-[10px] font-mono font-bold text-indigo-500 uppercase tracking-widest mb-1">Side A · Central Server</div>
                  <h3 className="text-lg font-bold text-slate-900 tracking-tight">Admin Coordinator</h3>
                  <p className="text-xs text-slate-500 mt-0.5">Global aggregation & model governance</p>
                </div>
              </div>

              <ul className="space-y-2.5">
                {[
                  'Publishes & controls available healthcare models',
                  'Performs FedAvg aggregation & client selection',
                  'Monitors security anomalies & LLM reasoning',
                ].map(item => (
                  <li key={item} className="flex items-start gap-2.5 text-xs text-slate-600">
                    <CheckCircle2 className="w-4 h-4 text-indigo-500 flex-shrink-0 mt-px" />
                    {item}
                  </li>
                ))}
                <li className="flex items-center gap-2.5 text-xs text-amber-700 font-semibold bg-amber-50 rounded-lg px-3 py-2 border border-amber-100">
                  <Lock className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                  Coordinator never trains locally · Rule 6
                </li>
              </ul>

              {/* Demo credentials */}
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 font-mono text-[11px] text-slate-600 flex items-center justify-between">
                <span><span className="text-slate-400">Demo: </span>admin@flplatform.org</span>
                <span className="px-2 py-1 rounded-md bg-white border border-slate-200 text-indigo-600 font-bold text-[10px]">admin123</span>
              </div>

              <button
                onClick={() => navigate('/admin/login')}
                className="w-full btn-primary justify-center text-sm py-2.5"
              >
                <span>Enter Admin Coordinator Portal</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* Client Card */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col gap-5 shadow-sm hover-glow-sky transition-all duration-300 group">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-sky-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-sky-200 flex-shrink-0">
                  <Building2 className="w-5.5 h-5.5 text-white" />
                </div>
                <div>
                  <div className="text-[10px] font-mono font-bold text-sky-500 uppercase tracking-widest mb-1">Side B · Clinical Nodes</div>
                  <h3 className="text-lg font-bold text-slate-900 tracking-tight">Hospital Clients</h3>
                  <p className="text-xs text-slate-500 mt-0.5">Hospital A, Hospital B, Hospital C</p>
                </div>
              </div>

              <ul className="space-y-2.5">
                {[
                  'Isolated private non-IID healthcare datasets',
                  'Executes PyTorch local training privately',
                  'Transmits weight deltas only (zero raw records)',
                ].map(item => (
                  <li key={item} className="flex items-start gap-2.5 text-xs text-slate-600">
                    <CheckCircle2 className="w-4 h-4 text-sky-500 flex-shrink-0 mt-px" />
                    {item}
                  </li>
                ))}
                <li className="flex items-center gap-2.5 text-xs text-emerald-700 font-semibold bg-emerald-50 rounded-lg px-3 py-2 border border-emerald-100">
                  <Lock className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                  Zero raw patient record leakage enforced
                </li>
              </ul>

              {/* Demo credentials */}
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 font-mono text-[11px] text-slate-600 flex items-center justify-between">
                <span><span className="text-slate-400">Demo: </span>hospital_a@flplatform.org</span>
                <span className="px-2 py-1 rounded-md bg-white border border-slate-200 text-sky-600 font-bold text-[10px]">client1pass</span>
              </div>

              <button
                onClick={() => navigate('/client/login')}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-gradient-to-r from-sky-500 to-cyan-500 hover:from-sky-400 hover:to-cyan-400 text-white font-semibold text-sm shadow-md shadow-sky-200 transition-all duration-200 hover:-translate-y-0.5 cursor-pointer"
              >
                <span>Enter Clinical Client Portal</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── Feature Strip ─────────────────────────── */}
      <section className="bg-slate-50 border-t border-slate-100 px-6 py-12">
        <div className="max-w-4xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-5">
          {[
            {
              icon: <Cpu className="w-5 h-5 text-white" />,
              iconBg: 'from-blue-500 to-indigo-500',
              shadowColor: 'shadow-blue-200',
              title: 'PyTorch FL Engine',
              desc: 'Authentic backpropagation and genuine parameter delta computation across all clinical nodes.',
            },
            {
              icon: <Lock className="w-5 h-5 text-white" />,
              iconBg: 'from-emerald-500 to-teal-500',
              shadowColor: 'shadow-emerald-200',
              title: 'Privacy Preserving',
              desc: 'Non-IID physical isolation ensuring raw patient rows never transmit to the central server.',
            },
            {
              icon: <Activity className="w-5 h-5 text-white" />,
              iconBg: 'from-violet-500 to-purple-500',
              shadowColor: 'shadow-violet-200',
              title: 'Live Monitoring',
              desc: 'Real-time telemetry, security anomaly detection, and LLM-powered decision reasoning.',
            },
          ].map(feat => (
            <div
              key={feat.title}
              className="bg-white rounded-2xl border border-slate-200 p-5 flex flex-col gap-3 shadow-sm hover:-translate-y-1 transition-all duration-300 hover:shadow-md hover:border-slate-300"
            >
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${feat.iconBg} flex items-center justify-center shadow-lg ${feat.shadowColor}`}>
                {feat.icon}
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-900 mb-1">{feat.title}</h4>
                <p className="text-xs text-slate-500 leading-relaxed">{feat.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ────────────────────────────────── */}
      <footer className="bg-white border-t border-slate-100 px-6 py-5">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg gradient-brand flex items-center justify-center">
              <Shield className="w-3 h-3 text-white" />
            </div>
            <span className="font-semibold text-slate-600">FedHealth Platform</span>
            <span className="font-mono">v1.0</span>
          </div>
          <div className="flex items-center gap-2 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-emerald-600 font-semibold">System Online</span>
            <span className="text-slate-300">·</span>
            <span>FedAvg Protocol Active</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
