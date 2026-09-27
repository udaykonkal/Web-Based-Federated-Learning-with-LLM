import React, { useState } from 'react';
import { 
  ChevronDown, 
  ChevronUp, 
  Code2, 
  Sliders, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Copy, 
  Check, 
  Play, 
  Terminal,
  Trash2
} from 'lucide-react';

export interface NotebookStageProps {
  stageNumber: number;
  stageTitle: string;
  stageSubtitle: string;
  isAdvancedMode: boolean;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'locked';
  executionOrder?: number | null;
  executionTimeMs?: number | null;
  onRunCell?: () => void;
  cellOutput?: string | null;
  onClearOutput?: () => void;
  beginnerContent: React.ReactNode;
  pythonCodeContent: string;
  defaultExpanded?: boolean;
}

// Token sets for Python syntax highlighting
const KEYWORDS = new Set([
  'import', 'from', 'as', 'def', 'class', 'return', 'for', 'in', 'range',
  'if', 'else', 'elif', 'while', 'with', 'try', 'except', 'finally',
  'raise', 'yield', 'pass', 'lambda', 'assert', 'global', 'True', 'False', 'None'
]);

const PYTORCH_CLASSES = new Set([
  'torch', 'nn', 'optim', 'DataLoader', 'TensorDataset', 'Sequential',
  'Linear', 'BatchNorm1d', 'ReLU', 'Dropout', 'Sigmoid', 'BCELoss',
  'Adam', 'SGD', 'StandardScaler', 'train_test_split', 'pd', 'np',
  'DiabetesMLP', 'HeartDiseaseMLP', 'Module', 'DataFrame', 'Tensor'
]);

const BUILTIN_METHODS = new Set([
  'print', 'len', 'float', 'int', 'str', 'super', 'items', 'state_dict',
  'cpu', 'sum', 'item', 'round', 'read_csv', 'drop', 'values', 'fit_transform',
  'transform', 'tensor', 'unsqueeze', 'zero_grad', 'backward', 'step', 'train',
  'eval', 'forward', '__init__'
]);

function highlightPythonLine(line: string, lineKey: string | number): React.ReactNode {
  if (!line.trim()) {
    return <span key={lineKey}>&nbsp;</span>;
  }

  // Check for indentation
  const indentMatch = line.match(/^(\s*)/);
  const indent = indentMatch ? indentMatch[1] : '';
  const content = line.slice(indent.length);

  // Check for comment
  const commentIdx = content.indexOf('#');
  let codePart = content;
  let commentPart = '';
  if (commentIdx !== -1) {
    // Ensure # isn't inside a quote
    let inSingle = false;
    let inDouble = false;
    let actualCommentIdx = -1;
    for (let i = 0; i < content.length; i++) {
      const char = content[i];
      if (char === "'" && !inDouble) inSingle = !inSingle;
      else if (char === '"' && !inSingle) inDouble = !inDouble;
      else if (char === '#' && !inSingle && !inDouble) {
        actualCommentIdx = i;
        break;
      }
    }
    if (actualCommentIdx !== -1) {
      codePart = content.slice(0, actualCommentIdx);
      commentPart = content.slice(actualCommentIdx);
    }
  }

  // Tokenize codePart
  const tokenRegex = /(f?"""[\s\S]*?"""|f?'''[\s\S]*?'''|f?"(?:[^"\\]|\\.)*"|f?'(?:[^'\\]|\\.)*'|\b\d+(?:\.\d+)?\b|[a-zA-Z_]\w*|==|!=|<=|>=|->|\*\*|[+\-*\/=<>:,.\(\)\[\]{}])/g;

  const nodes: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = tokenRegex.exec(codePart)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(codePart.slice(lastIndex, match.index));
    }

    const token = match[0];
    const key = `${lineKey}-${match.index}`;

    if (token.startsWith('"') || token.startsWith("'") || token.startsWith('f"') || token.startsWith("f'")) {
      // String literal
      nodes.push(<span key={key} className="text-emerald-400 font-medium">{token}</span>);
    } else if (KEYWORDS.has(token)) {
      // Keyword
      nodes.push(<span key={key} className="text-purple-400 font-bold">{token}</span>);
    } else if (PYTORCH_CLASSES.has(token)) {
      // PyTorch / Scientific Class
      nodes.push(<span key={key} className="text-sky-400 font-semibold">{token}</span>);
    } else if (BUILTIN_METHODS.has(token)) {
      // Method or function
      nodes.push(<span key={key} className="text-amber-300">{token}</span>);
    } else if (/^\d/.test(token)) {
      // Number
      nodes.push(<span key={key} className="text-orange-400">{token}</span>);
    } else if (/^[+\-*\/=<>:,.\(\)\[\]{}]+$/.test(token)) {
      // Operator / Punctuation
      nodes.push(<span key={key} className="text-slate-400">{token}</span>);
    } else {
      nodes.push(<span key={key} className="text-slate-200">{token}</span>);
    }

    lastIndex = match.index + token.length;
  }

  if (lastIndex < codePart.length) {
    nodes.push(codePart.slice(lastIndex));
  }

  return (
    <span key={lineKey}>
      {indent}
      {nodes}
      {commentPart && <span className="text-slate-500 italic">{commentPart}</span>}
    </span>
  );
}

export const NotebookStageCard: React.FC<NotebookStageProps> = ({
  stageNumber,
  stageTitle,
  stageSubtitle,
  isAdvancedMode,
  status,
  executionOrder,
  executionTimeMs,
  onRunCell,
  cellOutput,
  onClearOutput,
  beginnerContent,
  pythonCodeContent,
  defaultExpanded = true,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [copied, setCopied] = useState(false);

  const getStatusBadge = () => {
    switch (status) {
      case 'running':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-sky-50 text-sky-700 border border-sky-200 font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-500 animate-pulse"></span>
            <span>Running cell...</span>
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            <span>Executed {executionTimeMs ? `(${executionTimeMs}ms)` : ''}</span>
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-rose-50 text-rose-700 border border-rose-200 font-bold">
            <AlertCircle className="w-3 h-3 text-rose-600" />
            <span>Failed</span>
          </span>
        );
      case 'locked':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-slate-100 text-slate-500 border border-slate-200 font-medium">
            <Clock className="w-3 h-3 text-slate-400" />
            <span>Queued</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-slate-100 text-slate-600 border border-slate-200 font-medium">
            <span>Ready</span>
          </span>
        );
    }
  };

  const handleCopyCode = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(pythonCodeContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const codeLines = pythonCodeContent.trim().split('\n');

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs hover:border-slate-300 transition-colors">
      {/* Cell Header Strip (Kaggle / Colab Cell Header) */}
      <div 
        className="px-4 py-3 bg-slate-50/90 border-b border-slate-200 flex items-center justify-between cursor-pointer select-none hover:bg-slate-100/70 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-3.5">
          {/* Colab Interactive Play Button in Gutter */}
          {isAdvancedMode && onRunCell ? (
            <div 
              onClick={(e) => {
                e.stopPropagation();
                if (status !== 'running') {
                  onRunCell();
                }
              }}
              title={`Run Cell [${stageNumber}] (Ctrl+Enter)`}
              className={`w-7 h-7 rounded-full flex items-center justify-center transition-all cursor-pointer shadow-xs ${
                status === 'running'
                  ? 'bg-sky-500 text-white animate-pulse'
                  : status === 'completed'
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-300 hover:bg-emerald-100'
                  : 'bg-white border border-slate-300 text-slate-700 hover:border-sky-500 hover:bg-sky-50 hover:text-sky-600 hover:scale-105'
              }`}
            >
              {status === 'running' ? (
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : status === 'completed' ? (
                <Check className="w-3.5 h-3.5 text-emerald-600 stroke-[2.5]" />
              ) : (
                <Play className="w-3 h-3 fill-current ml-0.5" />
              )}
            </div>
          ) : (
            <div className="flex items-center space-x-1 font-mono text-xs">
              <span className="px-2 py-0.5 rounded bg-white border border-slate-300 text-slate-700 font-bold shadow-xs">
                [{stageNumber}]
              </span>
            </div>
          )}

          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono font-bold text-slate-400">
                In [{executionOrder !== undefined && executionOrder !== null ? executionOrder : stageNumber}]:
              </span>
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                {stageTitle}
              </h3>
              {getStatusBadge()}
            </div>
            <p className="text-[11px] text-slate-500 font-medium mt-0.5">
              {stageSubtitle}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1 text-[11px] text-slate-500 font-mono">
            {isAdvancedMode ? (
              <span className="flex items-center space-x-1 text-sky-700 font-semibold bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                <Code2 className="w-3 h-3 text-sky-600" />
                <span>Colab Cell</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1 text-slate-600 bg-white px-2 py-0.5 rounded border border-slate-200 font-medium">
                <Sliders className="w-3 h-3 text-slate-500" />
                <span>Visual Form</span>
              </span>
            )}
          </div>
          <button 
            type="button" 
            className="text-slate-400 hover:text-slate-700 p-1 rounded hover:bg-slate-200/60 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Stage Content */}
      {isExpanded && (
        <div className="p-4 sm:p-5 space-y-4 bg-white">
          {isAdvancedMode ? (
            <div className="space-y-3">
              {/* Colab Cell Action Bar */}
              <div className="flex items-center justify-between text-xs text-slate-500 pb-1.5 border-b border-slate-100 font-mono">
                <div className="flex items-center space-x-2">
                  {onRunCell && (
                    <button
                      type="button"
                      onClick={onRunCell}
                      disabled={status === 'running'}
                      className="px-2.5 py-1 rounded-md bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 text-[11px] font-mono font-bold transition-colors flex items-center space-x-1.5 cursor-pointer shadow-xs disabled:opacity-50"
                    >
                      {status === 'running' ? (
                        <>
                          <div className="w-3 h-3 border-2 border-sky-600 border-t-transparent rounded-full animate-spin"></div>
                          <span>Running...</span>
                        </>
                      ) : (
                        <>
                          <Play className="w-3 h-3 fill-current" />
                          <span>Run Cell</span>
                        </>
                      )}
                    </button>
                  )}
                  <span className="text-slate-400 text-[10px]">
                    Python 3.10 • PyTorch Tensor Core
                  </span>
                </div>

                <div className="flex items-center space-x-1.5">
                  <button
                    type="button"
                    onClick={handleCopyCode}
                    className="px-2.5 py-1 rounded-md bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-[10px] font-mono transition-colors flex items-center space-x-1 cursor-pointer shadow-xs"
                  >
                    {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3 text-slate-500" />}
                    <span>{copied ? 'Copied' : 'Copy Code'}</span>
                  </button>
                </div>
              </div>

              {/* Colab Code Editor Window with Python Syntax Highlighting */}
              <div className="rounded-lg bg-[#0F172A] border border-slate-800/90 overflow-hidden shadow-inner text-xs font-mono">
                <div className="overflow-x-auto py-3 px-2">
                  <div className="table w-full">
                    {codeLines.map((line, idx) => (
                      <div key={idx} className="table-row leading-relaxed hover:bg-slate-800/40">
                        <span className="table-cell select-none text-right pr-3.5 pl-2 text-slate-600 border-r border-slate-800 font-mono text-[11px] w-9">
                          {idx + 1}
                        </span>
                        <span className="table-cell pl-3.5 whitespace-pre">
                          {highlightPythonLine(line, idx)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Colab Cell Output Console (If output exists) */}
              {cellOutput && (
                <div className="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden shadow-xs">
                  <div className="flex items-center justify-between px-3 py-1.5 bg-slate-950/80 border-b border-slate-800 text-[11px] font-mono text-slate-400">
                    <div className="flex items-center space-x-2">
                      <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="font-semibold text-slate-300">
                        Cell Output [In {executionOrder !== undefined && executionOrder !== null ? executionOrder : stageNumber}]
                      </span>
                    </div>
                    {onClearOutput && (
                      <button
                        type="button"
                        onClick={onClearOutput}
                        title="Clear cell output"
                        className="p-1 hover:text-slate-200 rounded transition-colors text-slate-500"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                  <pre className="p-3 text-[11px] font-mono text-emerald-400 whitespace-pre-wrap leading-relaxed overflow-x-auto selection:bg-emerald-950">
                    {cellOutput}
                  </pre>
                </div>
              )}

              {/* Parameter controls / visual inspection widgets beneath cell */}
              <div className="pt-2 border-t border-slate-100">
                <div className="text-[11px] font-mono text-slate-400 uppercase font-bold mb-2">
                  Interactive Controls & Live Telemetry:
                </div>
                {beginnerContent}
              </div>
            </div>
          ) : (
            <div>{beginnerContent}</div>
          )}
        </div>
      )}
    </div>
  );
};
