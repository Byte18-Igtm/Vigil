import React, { useState } from 'react';
import { X, Terminal, Filter, RefreshCw, Copy, Check, Sparkles } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { MOCK_AGENT_LOGS } from '../../data/mockData';

export default function AgentLogsModal() {
  const { activeModal, setActiveModal } = useApp();
  const [selectedAgentFilter, setSelectedAgentFilter] = useState('ALL');
  const [copied, setCopied] = useState(false);

  if (activeModal !== 'logs') return null;

  const filteredLogs = selectedAgentFilter === 'ALL'
    ? MOCK_AGENT_LOGS
    : MOCK_AGENT_LOGS.filter(l => l.agent.toLowerCase().includes(selectedAgentFilter.toLowerCase()));

  const handleCopy = () => {
    const text = filteredLogs.map(l => `[${l.timestamp}] [${l.agent}] [${l.level}] ${l.msg}`).join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-950 border border-slate-700 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-900">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400">
              <Terminal className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                Multi-Agent Stream Logs
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              </h3>
              <p className="text-[11px] text-slate-400">Live IPC telemetry between Supervising & Parallel agents</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              title="Copy all logs"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setActiveModal(null)}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filter Toolbar */}
        <div className="px-5 py-2.5 bg-slate-900/60 border-b border-slate-800 flex items-center justify-between text-xs overflow-x-auto gap-2">
          <div className="flex items-center space-x-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400 text-[11px] font-medium mr-1">Filter:</span>
            {['ALL', 'Supervisor', 'Context', 'Debugging', 'Testing', 'Maintenance'].map((filter) => (
              <button
                key={filter}
                onClick={() => setSelectedAgentFilter(filter)}
                className={`px-2 py-0.5 rounded-md text-[11px] font-medium transition-colors ${
                  selectedAgentFilter === filter
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700'
                }`}
              >
                {filter}
              </button>
            ))}
          </div>

          <span className="text-[10px] font-mono text-slate-500">
            {filteredLogs.length} events logged
          </span>
        </div>

        {/* Terminal Log Console */}
        <div className="p-4 flex-1 overflow-y-auto font-mono text-[11px] leading-relaxed space-y-2 bg-slate-950 text-slate-300 select-text">
          {filteredLogs.map((log, idx) => {
            const agentColors = {
              'Context Agent': 'text-blue-400 bg-blue-500/10 border-blue-500/30',
              'Supervising Agent': 'text-purple-400 bg-purple-500/10 border-purple-500/30',
              'Debugging Agent': 'text-red-400 bg-red-500/10 border-red-500/30',
              'Testing Agent': 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
              'Maintenance Agent': 'text-amber-400 bg-amber-500/10 border-amber-500/30',
              'Voice/Chat Output': 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30',
            };

            return (
              <div key={idx} className="flex items-start space-x-2 py-1 border-b border-slate-900 hover:bg-slate-900/40 px-1.5 rounded transition-colors">
                <span className="text-slate-500 shrink-0 select-none">[{log.timestamp}]</span>
                <span className={`px-1.5 py-0.2 rounded text-[10px] font-semibold border shrink-0 ${agentColors[log.agent] || 'text-slate-300'}`}>
                  {log.agent}
                </span>
                <span className="text-slate-400 shrink-0 font-bold">[{log.level}]</span>
                <span className="text-slate-200">{log.msg}</span>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-800 bg-slate-900/80 flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Parallel execution time: <strong>910ms</strong>
          </span>
          <button
            onClick={() => setActiveModal(null)}
            className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-colors"
          >
            Close Logs
          </button>
        </div>
      </div>
    </div>
  );
}
