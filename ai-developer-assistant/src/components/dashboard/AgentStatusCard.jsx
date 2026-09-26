import React from 'react';
import { Eye, Brain, Bug, FlaskConical, Wrench, ChevronRight, Activity } from 'lucide-react';
import { useApp } from '../../context/AppContext';

const iconMap = {
  Eye: Eye,
  Brain: Brain,
  Bug: Bug,
  FlaskConical: FlaskConical,
  Wrench: Wrench
};

export default function AgentStatusCard() {
  const { agents, isAnalyzing, activeWorkflowStage, setActiveTab } = useApp();

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-indigo-400" />
          Agents Status
        </h2>
        <span className="text-[10px] text-slate-400 font-mono">5/5 Online</span>
      </div>

      <div className="space-y-2">
        {agents.map((agent) => {
          const Icon = iconMap[agent.icon] || Brain;
          
          // Check if this agent is currently active in the simulation
          const isBusy = isAnalyzing && (
            (activeWorkflowStage === 'context' && agent.id === 'context') ||
            (activeWorkflowStage === 'supervisor' && agent.id === 'supervisor') ||
            (activeWorkflowStage === 'parallel' && ['debugging', 'testing', 'maintenance'].includes(agent.id)) ||
            (activeWorkflowStage === 'synthesis' && agent.id === 'supervisor')
          );

          return (
            <div
              key={agent.id}
              onClick={() => setActiveTab('agents')}
              className={`p-2.5 rounded-lg border transition-all duration-200 cursor-pointer flex items-center justify-between group ${
                isBusy
                  ? 'bg-slate-800/90 border-indigo-500 shadow-md ring-1 ring-indigo-500/50'
                  : 'bg-slate-950/60 border-slate-800/80 hover:bg-slate-800/50 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className={`w-2 h-2 rounded-full shrink-0 ${isBusy ? 'bg-amber-400 animate-ping' : 'bg-emerald-400'}`}></div>
                <div className={`p-1 rounded-md shrink-0 ${agent.bgColor} ${agent.textColor}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div className="truncate">
                  <span className="text-xs font-semibold text-slate-200 block truncate group-hover:text-white">
                    {agent.name}
                  </span>
                </div>
              </div>

              <div className="flex items-center space-x-2 shrink-0">
                <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                  isBusy 
                    ? 'bg-amber-500/20 text-amber-300 animate-pulse border border-amber-500/30'
                    : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                }`}>
                  {isBusy ? 'Processing...' : agent.status}
                </span>
                <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-slate-300 transition-transform group-hover:translate-x-0.5" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
