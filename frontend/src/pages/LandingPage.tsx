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
  Layers
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-[#202124] flex flex-col">
      {/* Top Header */}
      <header className="border-b border-gray-200 bg-white px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center text-white font-bold">
              <Shield className="w-4 h-4" />
            </div>
            <span className="font-bold text-base text-gray-900 tracking-tight">FedHealth Platform</span>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <button
              onClick={() => navigate('/client/login')}
              className="px-3.5 py-1.5 rounded-md bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium transition-colors cursor-pointer"
            >
              Client Login
            </button>
            <button
              onClick={() => navigate('/admin/login')}
              className="px-3.5 py-1.5 rounded-md bg-sky-600 hover:bg-sky-500 text-white font-semibold transition-colors shadow-xs cursor-pointer"
            >
              Coordinator Portal
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-5xl mx-auto px-6 py-16 flex flex-col items-center justify-center text-center">
        {/* Subtle pill */}
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-50 border border-sky-200 text-sky-700 text-xs font-semibold uppercase tracking-wider mb-6 font-mono">
          <Shield className="w-3.5 h-3.5" />
          <span>Decentralized Federated Learning Engine</span>
        </div>

        {/* Title */}
        <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-gray-900 max-w-3xl leading-tight">
          Collaborative Machine Learning with Complete Data Privacy
        </h1>
        <p className="mt-4 text-sm md:text-base text-gray-600 max-w-2xl leading-relaxed">
          Train and improve medical machine learning models collaboratively across isolated hospital nodes.
          Only mathematical weight deltas are aggregated — raw patient records never leave the local client.
        </p>

        {/* Role Portal Action Cards (Kaggle Minimal Style) */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl text-left">
          {/* Side A: Admin Coordinator */}
          <div className="bg-white p-6 rounded-xl border border-gray-200 hover:border-gray-300 transition-all shadow-xs flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600">
                  <Server className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-gray-900">Side A: Central Server</h2>
                  <p className="text-xs text-indigo-700 font-medium">Coordinator & Aggregator Portal</p>
                </div>
              </div>

              <ul className="space-y-2 text-xs text-gray-600 mb-6">
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                  <span>Publishes & controls available healthcare models</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                  <span>Performs FedAvg aggregation & client selection</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                  <span>Monitors security anomalies & LLM reasoning</span>
                </li>
                <li className="flex items-center space-x-2 text-amber-700 font-medium">
                  <Lock className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                  <span>Strict Rule: Coordinator never trains locally</span>
                </li>
              </ul>
            </div>

            <div className="space-y-3">
              <div className="p-2.5 rounded-lg bg-gray-50 border border-gray-200 text-[11px] text-gray-700 font-mono flex items-center justify-between">
                <div>
                  <span className="text-gray-400">Demo User: </span>admin@flplatform.org
                </div>
                <span className="px-1.5 py-0.5 rounded bg-white text-indigo-700 font-semibold border border-gray-200">admin123</span>
              </div>

              <button
                onClick={() => navigate('/admin/login')}
                className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center justify-center space-x-2 transition-colors cursor-pointer shadow-xs"
              >
                <span>Enter Admin Coordinator Portal</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Side B: Healthcare Clients */}
          <div className="bg-white p-6 rounded-xl border border-gray-200 hover:border-gray-300 transition-all shadow-xs flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
                  <Building2 className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-gray-900">Side B: Clinical Nodes</h2>
                  <p className="text-xs text-emerald-700 font-medium">Hospital A, Hospital B, Hospital C</p>
                </div>
              </div>

              <ul className="space-y-2 text-xs text-gray-600 mb-6">
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>Isolated private non-IID healthcare datasets</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>Executes PyTorch local training privately</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>Transmits weight deltas only (zero raw records)</span>
                </li>
                <li className="flex items-center space-x-2 text-sky-700 font-medium">
                  <Lock className="w-3.5 h-3.5 text-sky-600 shrink-0" />
                  <span>Strict Rule: Zero raw patient record leakage</span>
                </li>
              </ul>
            </div>

            <div className="space-y-3">
              <div className="p-2.5 rounded-lg bg-gray-50 border border-gray-200 text-[11px] text-gray-700 font-mono flex items-center justify-between">
                <div>
                  <span className="text-gray-400">Demo User: </span>hospital_a@flplatform.org
                </div>
                <span className="px-1.5 py-0.5 rounded bg-white text-emerald-700 font-semibold border border-gray-200">client1pass</span>
              </div>

              <button
                onClick={() => navigate('/client/login')}
                className="w-full py-2.5 px-4 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs flex items-center justify-center space-x-2 transition-colors cursor-pointer shadow-xs"
              >
                <span>Enter Clinical Client Portal</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Minimal Feature Summary */}
        <div className="mt-14 pt-8 border-t border-gray-200 grid grid-cols-1 sm:grid-cols-3 gap-6 w-full max-w-3xl text-left text-xs text-gray-600">
          <div className="p-4 rounded-lg bg-white border border-gray-200 shadow-xs space-y-1">
            <Cpu className="w-4 h-4 text-sky-600" />
            <span className="font-bold text-gray-900 block">PyTorch FL Engine</span>
            <p className="text-[11px] text-gray-500">Authentic backpropagation and genuine parameter delta computation.</p>
          </div>
          <div className="p-4 rounded-lg bg-white border border-gray-200 shadow-xs space-y-1">
            <Lock className="w-4 h-4 text-emerald-600" />
            <span className="font-bold text-gray-900 block">Privacy Preserving</span>
            <p className="text-[11px] text-gray-500">Non-IID physical isolation ensuring raw patient rows never transmit.</p>
          </div>
          <div className="p-4 rounded-lg bg-white border border-gray-200 shadow-xs space-y-1">
            <Layers className="w-4 h-4 text-purple-600" />
            <span className="font-bold text-gray-900 block">Kaggle-Style Workbench</span>
            <p className="text-[11px] text-gray-500">Named stage execution, hyperparameter forms, and streaming logs.</p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LandingPage;
