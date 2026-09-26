import React, { useState } from 'react';
import { 
  Eye, 
  Brain, 
  Bug, 
  FlaskConical, 
  Wrench, 
  Activity, 
  CheckCircle2, 
  Sparkles, 
  Play, 
  Sliders, 
  Cpu, 
  Terminal,
  ShieldAlert,
  Layers
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

const iconMap = {
  Eye,
  Brain,
  Bug,
  FlaskConical,
  Wrench
};

export default function AgentsView() {
  const { agents, runAgentAnalysis, isAnalyzing, setActiveModal } = useApp();
  const [selectedAgentId, setSelectedAgentId] = useState('supervisor');

  const selectedAgent = agents.find(a => a.id === selectedAgentId) || agents[0];
  const Icon = iconMap[selectedAgent.icon] || Brain;

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/90 border border-slate-800 p-5 rounded-xl">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-400" />
            Multi-Agent Architecture & Swarm Studio
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure agent personas, concurrency parameters, execution pipelines, and telemetry inspectors.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveModal('logs')}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-colors border border-slate-700"
          >
            <Terminal className="w-3.5 h-3.5 text-emerald-400" />
            <span>View Live Logs</span>
          </button>
          <button
            onClick={() => runAgentAnalysis()}
            disabled={isAnalyzing}
            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-indigo-600/30 disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{isAnalyzing ? 'Swarm Running...' : 'Trigger Swarm Run'}</span>
          </button>
        </div>
      </div>

      {/* Grid of Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => {
          const AgentIcon = iconMap[agent.icon] || Brain;
          const isSelected = agent.id === selectedAgentId;

          return (
            <div
              key={agent.id}
              onClick={() => setSelectedAgentId(agent.id)}
              className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between group ${
                isSelected
                  ? 'bg-slate-900 border-indigo-500 shadow-xl ring-2 ring-indigo-500/30'
                  : 'bg-slate-900/60 border-slate-800 hover:bg-slate-900 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2.5">
                    <div className={`p-2 rounded-lg ${agent.bgColor} ${agent.textColor}`}>
                      <AgentIcon className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-100 group-hover:text-white">
                        {agent.name}
                      </h3>
                      <span className="text-[10px] text-slate-400 block font-mono">{agent.role}</span>
                    </div>
                  </div>
                  <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    {agent.status}
                  </span>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed mb-4">
                  {agent.description}
                </p>
              </div>

              {/* Metrics Bar */}
              <div className="pt-3 border-t border-slate-800 grid grid-cols-3 gap-2 text-center text-[10px]">
                {Object.entries(agent.metrics).map(([k, val]) => (
                  <div key={k} className="bg-slate-950/60 p-1.5 rounded-md border border-slate-800/80">
                    <div className="text-slate-400 uppercase tracking-tight truncate">{k}</div>
                    <div className="text-slate-100 font-bold font-mono mt-0.5">{val}</div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Agent Deep Dive Panel */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex items-center space-x-3 mb-4 pb-3 border-b border-slate-800">
          <div className={`p-2 rounded-xl ${selectedAgent.bgColor} ${selectedAgent.textColor}`}>
            <Icon className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              {selectedAgent.name} Configuration & Telemetry
            </h3>
            <span className="text-xs text-slate-400 font-mono">ID: {selectedAgent.id} • Concurrency: 1x</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-slate-300">
          <div className="space-y-3">
            <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">Core Capabilities</h4>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/90 space-y-1.5">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Isolated AST parser and tree-sitter listener</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Zero latency context retrieval with local embeddings</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Asynchronous inter-agent streaming IPC channel</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">System Prompt Persona</h4>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/90 font-mono text-[11px] text-slate-400 leading-relaxed">
              "You are the {selectedAgent.name} in an autonomous multi-agent engineering workflow. Your priority is: {selectedAgent.role}. Maintain high code accuracy, run non-destructive verification, and communicate via JSON-RPC to Supervising Agent."
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
