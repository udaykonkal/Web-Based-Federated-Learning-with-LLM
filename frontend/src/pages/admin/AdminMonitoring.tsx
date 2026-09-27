import React, { useEffect, useState, useRef } from 'react';
import { api } from '../../services/api';
import { 
  Radio, 
  Activity, 
  Building2, 
  Clock
} from 'lucide-react';

interface TelemetryEvent {
  type: string;
  timestamp: string;
  data: any;
}

interface ClientStatus {
  id: string;
  name: string;
  state: 'idle' | 'training' | 'uploading' | 'complete';
  lastLoss: number | null;
  lastAccuracy: number | null;
  sampleCount: number;
  lastL2Norm: number | null;
  lastUpdated: string | null;
}

export const AdminMonitoring: React.FC = () => {
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [clients, setClients] = useState<Record<string, ClientStatus>>({
    client_1: { id: 'client_1', name: 'Hospital A (Regional Medical Center)', state: 'idle', lastLoss: null, lastAccuracy: null, sampleCount: 345, lastL2Norm: null, lastUpdated: null },
    client_2: { id: 'client_2', name: 'Hospital B (Community Healthcare)', state: 'idle', lastLoss: null, lastAccuracy: null, sampleCount: 268, lastL2Norm: null, lastUpdated: null },
    client_3: { id: 'client_3', name: 'Hospital C (University Clinic)', state: 'idle', lastLoss: null, lastAccuracy: null, sampleCount: 155, lastL2Norm: null, lastUpdated: null },
  });
  const [activeRound, setActiveRound] = useState<number | null>(null);
  const [latestEval, setLatestEval] = useState<{ accuracy: number; loss: number; f1: number } | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const eventsEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    // 1. Initial sync from REST endpoint
    const fetchRecent = async () => {
      try {
        const res = await api.get<TelemetryEvent[]>('/telemetry/recent');
        if (res.data) {
          setEvents(res.data);
          processEventsForState(res.data);
        }
      } catch (err) {
        console.error('Failed to load initial telemetry snapshot:', err);
      }
    };
    fetchRecent();

    // 2. Establish WebSocket connection
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/ws/telemetry`;

    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(wsUrl);
        socketRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
        };

        ws.onmessage = (message) => {
          try {
            const parsed = JSON.parse(message.data);
            if (parsed.type === 'INITIAL_SYNC' && Array.isArray(parsed.events)) {
              setEvents(parsed.events);
              processEventsForState(parsed.events);
            } else if (parsed.type && parsed.type !== 'PONG') {
              setEvents((prev) => [...prev.slice(-49), parsed]);
              processSingleEvent(parsed);
            }
          } catch (e) {
            console.error('Error parsing WebSocket message:', e);
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          // Try reconnecting after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = () => {
          setIsConnected(false);
        };
      } catch (e) {
        setIsConnected(false);
      }
    };

    connectWebSocket();

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [events]);

  const processSingleEvent = (event: TelemetryEvent) => {
    const { type, data, timestamp } = event;
    if (type === 'ROUND_STARTED') {
      setActiveRound(data.round_number);
      setClients((prev) => {
        const updated = { ...prev };
        Object.keys(updated).forEach((k) => {
          updated[k] = { ...updated[k], state: 'training' };
        });
        return updated;
      });
    } else if (type === 'CLIENT_TRAINING_STARTED') {
      if (data.client_id && clients[data.client_id]) {
        setClients((prev) => ({
          ...prev,
          [data.client_id]: { ...prev[data.client_id], state: 'training', lastUpdated: timestamp }
        }));
      }
    } else if (type === 'CLIENT_TRAINING_COMPLETED') {
      if (data.client_id && clients[data.client_id]) {
        setClients((prev) => ({
          ...prev,
          [data.client_id]: {
            ...prev[data.client_id],
            state: 'complete',
            lastLoss: data.loss,
            lastAccuracy: data.accuracy,
            sampleCount: data.sample_count,
            lastL2Norm: data.l2_norm,
            lastUpdated: timestamp
          }
        }));
      }
    } else if (type === 'GLOBAL_EVALUATION_COMPLETED') {
      setLatestEval({
        accuracy: data.accuracy,
        loss: data.loss,
        f1: data.f1_score
      });
      setClients((prev) => {
        const updated = { ...prev };
        Object.keys(updated).forEach((k) => {
          updated[k] = { ...updated[k], state: 'idle' };
        });
        return updated;
      });
    }
  };

  const processEventsForState = (eventList: TelemetryEvent[]) => {
    eventList.forEach(processSingleEvent);
  };

  const getEventBadge = (type: string) => {
    switch (type) {
      case 'ROUND_STARTED':
        return <span className="badge-sky font-mono text-[10px]">ROUND START</span>;
      case 'CLIENT_TRAINING_STARTED':
        return <span className="badge-indigo font-mono text-[10px]">CLIENT TRAIN</span>;
      case 'CLIENT_TRAINING_COMPLETED':
        return <span className="badge-emerald font-mono text-[10px]">TRAIN COMPLETE</span>;
      case 'SECURITY_VERIFICATION_PASSED':
        return <span className="badge-sky font-mono text-[10px]">SECURITY PASS</span>;
      case 'AGGREGATION_COMPLETED':
        return <span className="badge-indigo font-mono text-[10px]">FEDAVG AGGREGATED</span>;
      case 'GLOBAL_EVALUATION_COMPLETED':
        return <span className="badge-amber font-mono text-[10px]">GLOBAL EVAL</span>;
      case 'EXPERIMENT_COMPLETED':
        return <span className="badge-emerald font-mono text-[10px]">EXPERIMENT DONE</span>;
      default:
        return <span className="badge-slate font-mono text-[10px]">{type}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="card p-6 bg-white border border-slate-200 rounded-xl shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-sky-700 text-xs font-semibold uppercase tracking-wider mb-1">
            <Radio className="w-4 h-4 text-sky-600" />
            <span>Phase 7: Real-Time Telemetry Stream</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Live Federated Learning Monitor
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time event stream broadcasting round states, client gradient computations, security validation, and FedAvg updates.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-xs font-medium ${
            isConnected
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-amber-50 border-amber-200 text-amber-800'
          }`}>
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`}></span>
            <span>{isConnected ? 'WebSocket Stream Active' : 'Connecting to Stream...'}</span>
          </div>
        </div>
      </div>

      {/* Top Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase">Current FL Round</span>
          <p className="text-xl font-bold font-mono text-slate-900">
            {activeRound ? `Round #${activeRound}` : 'Idle / Standby'}
          </p>
        </div>

        <div className="card p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase">Latest Global Accuracy</span>
          <p className="text-xl font-bold font-mono text-emerald-700">
            {latestEval ? `${(latestEval.accuracy * 100).toFixed(1)}%` : 'Awaiting Round'}
          </p>
        </div>

        <div className="card p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase">Global Evaluation Loss</span>
          <p className="text-xl font-bold font-mono text-sky-700">
            {latestEval ? latestEval.loss.toFixed(4) : 'Awaiting Round'}
          </p>
        </div>

        <div className="card p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase">Total Logged Telemetry Events</span>
          <p className="text-xl font-bold font-mono text-indigo-700">
            {events.length} events
          </p>
        </div>
      </div>

      {/* Hospital Nodes Status Matrix */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
            <Building2 className="w-4 h-4 text-sky-600" />
            <span>Clinical Client Node Telemetry Status (3 Isolated Hospitals)</span>
          </h2>
          <span className="text-xs text-slate-500 font-mono">Zero raw records transmitted</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.values(clients).map((client) => {
            const isTraining = client.state === 'training';
            const isComplete = client.state === 'complete';
            return (
              <div
                key={client.id}
                className={`card p-5 bg-white rounded-xl border transition-all shadow-xs ${
                  isTraining
                    ? 'border-sky-400 bg-sky-50/40 shadow-card-hover'
                    : isComplete
                    ? 'border-emerald-300 bg-emerald-50/30'
                    : 'border-slate-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="badge-slate uppercase font-mono">
                      {client.id.toUpperCase()}
                    </span>
                    <h3 className="text-xs font-bold text-slate-900 mt-1.5">{client.name}</h3>
                  </div>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    isTraining
                      ? 'bg-sky-50 text-sky-700 border border-sky-200 animate-pulse'
                      : isComplete
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {client.state.toUpperCase()}
                  </span>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 space-y-1.5 text-xs">
                  <div className="flex justify-between text-slate-600">
                    <span>Private Samples:</span>
                    <strong className="text-slate-900 font-mono">{client.sampleCount} patients</strong>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Last Local Loss:</span>
                    <strong className="text-sky-700 font-mono">
                      {client.lastLoss !== null ? client.lastLoss.toFixed(4) : 'Pending'}
                    </strong>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Last Local Accuracy:</span>
                    <strong className="text-emerald-700 font-mono">
                      {client.lastAccuracy !== null ? `${(client.lastAccuracy * 100).toFixed(1)}%` : 'Pending'}
                    </strong>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Update Norm ||ΔW||₂:</span>
                    <strong className="text-indigo-700 font-mono">
                      {client.lastL2Norm !== null ? client.lastL2Norm : 'Pending'}
                    </strong>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Live Event Stream / Audit Log */}
      <div className="card p-6 bg-white rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-emerald-600" />
            <h2 className="text-sm font-bold text-slate-900">
              Real-Time Event Audit Stream (Live FIFO Buffer)
            </h2>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            {events.length} events logged
          </span>
        </div>

        <div className="h-80 overflow-y-auto space-y-2 pr-2 font-mono text-xs">
          {events.length === 0 ? (
            <div className="h-full flex items-center justify-center text-slate-400 text-xs">
              Waiting for live federated learning events...
            </div>
          ) : (
            events.map((ev, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-100/70 transition-colors"
              >
                <div className="flex items-center space-x-2.5">
                  {getEventBadge(ev.type)}
                  <span className="text-slate-800 text-xs">
                    {ev.type === 'ROUND_STARTED' && `Round #${ev.data.round_number} initialized for ${ev.data.task}. Clients: ${ev.data.selected_clients?.join(', ')}`}
                    {ev.type === 'CLIENT_TRAINING_STARTED' && `${ev.data.client_id} started local PyTorch training.`}
                    {ev.type === 'CLIENT_TRAINING_COMPLETED' && `${ev.data.client_id} finished training. Loss: ${ev.data.loss}, Acc: ${(ev.data.accuracy * 100).toFixed(1)}%, ||ΔW||₂: ${ev.data.l2_norm}`}
                    {ev.type === 'SECURITY_VERIFICATION_PASSED' && `Cryptographic and anomaly screening passed for updates.`}
                    {ev.type === 'AGGREGATION_COMPLETED' && `FedAvg parameter aggregation completed across ${ev.data.total_samples} samples.`}
                    {ev.type === 'GLOBAL_EVALUATION_COMPLETED' && `Global Benchmark Evaluated: Accuracy ${(ev.data.accuracy * 100).toFixed(1)}%, Loss: ${ev.data.loss}`}
                    {ev.type === 'EXPERIMENT_COMPLETED' && `Experiment completed all ${ev.data.total_rounds} rounds. Final Acc: ${(ev.data.final_accuracy * 100).toFixed(1)}%`}
                    {!['ROUND_STARTED', 'CLIENT_TRAINING_STARTED', 'CLIENT_TRAINING_COMPLETED', 'SECURITY_VERIFICATION_PASSED', 'AGGREGATION_COMPLETED', 'GLOBAL_EVALUATION_COMPLETED', 'EXPERIMENT_COMPLETED'].includes(ev.type) && JSON.stringify(ev.data)}
                  </span>
                </div>

                <div className="flex items-center space-x-1.5 text-slate-400 text-[11px] flex-shrink-0">
                  <Clock className="w-3 h-3" />
                  <span>{new Date(ev.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            ))
          )}
          <div ref={eventsEndRef} />
        </div>
      </div>
    </div>
  );
};

