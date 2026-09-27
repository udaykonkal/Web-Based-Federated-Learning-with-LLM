import React, { useState, useEffect, useRef } from 'react';
import { Terminal, ChevronDown, ChevronUp, Trash2, Copy, Check, ArrowDownToLine } from 'lucide-react';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'STEP' | 'METRIC' | 'SECURITY' | 'ERROR';
  message: string;
}

interface TerminalLogsDrawerProps {
  logs: LogEntry[];
  onClearLogs: () => void;
  isRunning?: boolean;
}

export const TerminalLogsDrawer: React.FC<TerminalLogsDrawerProps> = ({
  logs,
  onClearLogs,
  isRunning = false,
}) => {
  const [isOpen, setIsOpen] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState<'ALL' | 'INFO' | 'STEP' | 'METRIC' | 'SECURITY'>('ALL');
  const [copied, setCopied] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && isOpen && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll, isOpen]);

  const filteredLogs = logs.filter((log) => {
    if (filter === 'ALL') return true;
    return log.level === filter;
  });

  const handleCopyLogs = () => {
    const text = logs
      .map((l) => `[${l.timestamp}] [${l.level}] ${l.message}`)
      .join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getLevelBadgeClass = (level: LogEntry['level']) => {
    switch (level) {
      case 'STEP':
        return 'text-sky-300 bg-sky-950/80 border-sky-800';
      case 'METRIC':
        return 'text-emerald-300 bg-emerald-950/80 border-emerald-800';
      case 'SECURITY':
        return 'text-purple-300 bg-purple-950/80 border-purple-800';
      case 'ERROR':
        return 'text-rose-300 bg-rose-950/80 border-rose-800';
      default:
        return 'text-slate-400 bg-slate-800 border-slate-700';
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs transition-all">
      {/* Terminal Title Bar */}
      <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-rose-400"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-amber-400"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400"></div>
          </div>
          <div className="flex items-center space-x-2 text-xs font-mono text-slate-700">
            <Terminal className="w-3.5 h-3.5 text-sky-600" />
            <span className="font-bold text-slate-800">PyTorch Local Step Console</span>
            {isRunning && (
              <span className="inline-flex items-center space-x-1 text-[10px] text-sky-700 font-mono px-2 py-0.5 rounded-full bg-sky-50 border border-sky-200 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-sky-500 animate-pulse"></span>
                <span>Active Execution</span>
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono">
          {/* Level Filter */}
          <div className="flex items-center space-x-1 bg-white p-0.5 rounded-lg border border-slate-200 text-[10px]">
            {(['ALL', 'STEP', 'METRIC', 'SECURITY'] as const).map((lvl) => (
              <button
                key={lvl}
                type="button"
                onClick={() => setFilter(lvl)}
                className={`px-2 py-0.5 rounded-md transition-colors cursor-pointer ${
                  filter === lvl
                    ? 'bg-sky-600 text-white font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>

          <button
            type="button"
            title="Toggle Auto-Scroll"
            onClick={() => setAutoScroll(!autoScroll)}
            className={`p-1 px-2 rounded-lg border text-[10px] flex items-center space-x-1 transition-colors cursor-pointer ${
              autoScroll
                ? 'bg-sky-50 border-sky-200 text-sky-700 font-semibold'
                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            <ArrowDownToLine className="w-3 h-3" />
            <span className="hidden sm:inline">Auto-Scroll</span>
          </button>

          <button
            type="button"
            title="Copy Logs"
            onClick={handleCopyLogs}
            className="p-1 px-2 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-900 text-[10px] flex items-center space-x-1 transition-colors cursor-pointer"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
            <span className="hidden sm:inline">{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <button
            type="button"
            title="Clear Console"
            onClick={onClearLogs}
            className="p-1 px-2 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 text-[10px] flex items-center space-x-1 transition-colors cursor-pointer"
          >
            <Trash2 className="w-3 h-3" />
            <span className="hidden sm:inline">Clear</span>
          </button>

          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="p-1 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 cursor-pointer"
          >
            {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Terminal Body */}
      {isOpen && (
        <div className="p-3.5 font-mono text-xs max-h-64 overflow-y-auto space-y-1 bg-[#090D16] select-text">
          {filteredLogs.length === 0 ? (
            <div className="text-slate-500 text-[11px] py-4 text-center">
              No console logs recorded yet. Configure parameters and click "Run Local Training Pipeline" to stream execution steps.
            </div>
          ) : (
            filteredLogs.map((entry) => (
              <div
                key={entry.id}
                className="flex items-start space-x-2 text-[11px] leading-relaxed py-0.5 hover:bg-slate-900/80 rounded px-1 transition-colors"
              >
                <span className="text-slate-500 shrink-0 select-none">{entry.timestamp}</span>
                <span
                  className={`px-1.5 py-0.2 rounded border text-[9px] font-semibold shrink-0 ${getLevelBadgeClass(
                    entry.level
                  )}`}
                >
                  {entry.level}
                </span>
                <span
                  className={`break-all ${
                    entry.level === 'ERROR'
                      ? 'text-rose-300 font-semibold'
                      : entry.level === 'METRIC'
                      ? 'text-emerald-300'
                      : entry.level === 'SECURITY'
                      ? 'text-purple-300'
                      : entry.level === 'STEP'
                      ? 'text-sky-300'
                      : 'text-slate-200'
                  }`}
                >
                  {entry.message}
                </span>
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
};
