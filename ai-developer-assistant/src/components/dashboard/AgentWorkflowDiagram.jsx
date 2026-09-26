import React, { useState } from 'react';
import { 
  Eye, 
  Brain, 
  Bug, 
  FlaskConical, 
  Wrench, 
  MessageSquare, 
  Volume2, 
  ArrowDown, 
  Sparkles,
  Zap,
  CheckCircle2,
  Info
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function AgentWorkflowDiagram() {
  const { isAnalyzing, activeWorkflowStage, setActiveTab } = useApp();
  const [selectedNode, setSelectedNode] = useState(null);

  const isContextActive = isAnalyzing && activeWorkflowStage === 'context';
  const isSupervisorTopActive = isAnalyzing && activeWorkflowStage === 'supervisor';
  const isParallelActive = isAnalyzing && activeWorkflowStage === 'parallel';
  const isSupervisorBottomActive = isAnalyzing && activeWorkflowStage === 'synthesis';
  const isOutputActive = isAnalyzing && activeWorkflowStage === 'output';

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 sm:p-5 flex flex-col justify-between shadow-sm relative overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <div className="p-1 rounded-md bg-indigo-500/20 text-indigo-400">
            <Zap className="w-3.5 h-3.5" />
          </div>
          <h2 className="text-xs sm:text-sm font-bold text-white tracking-tight">
            Agent Workflow <span className="text-indigo-400 font-normal text-xs">(Parallel Execution)</span>
          </h2>
        </div>
        <button
          onClick={() => setActiveTab('agents')}
          className="text-[10px] text-indigo-400 hover:text-indigo-300 font-medium"
        >
          View Studio &rarr;
        </button>
      </div>

      {/* Workflow Diagram Body */}
      <div className="py-3 flex flex-col items-center space-y-2 relative">
        {/* 1. Context Agent */}
        <div 
          onClick={() => setSelectedNode('context')}
          className={`w-full max-w-sm rounded-xl p-2.5 border transition-all duration-300 cursor-pointer text-center relative ${
            isContextActive 
              ? 'bg-blue-600/30 border-blue-400 shadow-lg shadow-blue-500/30 ring-2 ring-blue-500 scale-[1.02]' 
              : 'bg-blue-950/40 border-blue-500/30 hover:bg-blue-900/40 hover:border-blue-400/60'
          }`}
        >
          <div className="flex items-center justify-center space-x-2 text-blue-400 mb-0.5">
            <Eye className="w-4 h-4" />
            <span className="text-xs font-bold text-slate-100">Context Agent</span>
          </div>
          <p className="text-[11px] text-blue-200/80">
            Understands project and developer context
          </p>
        </div>

        {/* Arrow 1 */}
        <div className="flex justify-center text-slate-600">
          <ArrowDown className={`w-4 h-4 ${isContextActive || isSupervisorTopActive ? 'text-indigo-400 animate-bounce' : 'text-slate-600'}`} />
        </div>

        {/* 2. Supervising Agent (Task Planning & Delegation) */}
        <div 
          onClick={() => setSelectedNode('supervisor')}
          className={`w-full max-w-sm rounded-xl p-2.5 border transition-all duration-300 cursor-pointer text-center relative ${
            isSupervisorTopActive 
              ? 'bg-purple-600/30 border-purple-400 shadow-lg shadow-purple-500/30 ring-2 ring-purple-500 scale-[1.02]' 
              : 'bg-purple-950/40 border-purple-500/30 hover:bg-purple-900/40 hover:border-purple-400/60'
          }`}
        >
          <div className="flex items-center justify-center space-x-2 text-purple-400 mb-0.5">
            <Brain className="w-4 h-4" />
            <span className="text-xs font-bold text-slate-100">Supervising Agent</span>
          </div>
          <p className="text-[11px] text-purple-200/80">
            Analyzes task and coordinates other agents
          </p>
        </div>

        {/* Parallel Branch Connectors */}
        <div className="w-full max-w-sm flex items-center justify-around text-slate-600 px-4">
          <ArrowDown className={`w-3.5 h-3.5 ${isParallelActive ? 'text-rose-400 animate-bounce' : 'text-slate-600'}`} />
          <ArrowDown className={`w-3.5 h-3.5 ${isParallelActive ? 'text-emerald-400 animate-bounce' : 'text-slate-600'}`} />
          <ArrowDown className={`w-3.5 h-3.5 ${isParallelActive ? 'text-amber-400 animate-bounce' : 'text-slate-600'}`} />
        </div>

        {/* 3. Parallel Swarm (Debugging, Testing, Maintenance) */}
        <div className="grid grid-cols-3 gap-2 w-full">
          {/* Debugging Agent */}
          <div 
            onClick={() => setSelectedNode('debugging')}
            className={`rounded-xl p-2 border transition-all duration-300 cursor-pointer text-center flex flex-col justify-between ${
              isParallelActive 
                ? 'bg-red-600/30 border-red-400 shadow-lg shadow-red-500/30 ring-2 ring-red-500 scale-[1.03]' 
                : 'bg-red-950/30 border-red-500/30 hover:bg-red-900/30 hover:border-red-400/60'
            }`}
          >
            <div className="flex flex-col items-center text-red-400 mb-1">
              <div className="p-1 rounded-md bg-red-500/10 mb-1">
                <Bug className="w-3.5 h-3.5" />
              </div>
              <span className="text-[11px] font-bold text-slate-100 leading-tight">Debugging Agent</span>
            </div>
            <p className="text-[10px] text-red-200/70 leading-snug">
              Finds root cause and suggests fix
            </p>
          </div>

          {/* Testing Agent */}
          <div 
            onClick={() => setSelectedNode('testing')}
            className={`rounded-xl p-2 border transition-all duration-300 cursor-pointer text-center flex flex-col justify-between ${
              isParallelActive 
                ? 'bg-emerald-600/30 border-emerald-400 shadow-lg shadow-emerald-500/30 ring-2 ring-emerald-500 scale-[1.03]' 
                : 'bg-emerald-950/30 border-emerald-500/30 hover:bg-emerald-900/30 hover:border-emerald-400/60'
            }`}
          >
            <div className="flex flex-col items-center text-emerald-400 mb-1">
              <div className="p-1 rounded-md bg-emerald-500/10 mb-1">
                <FlaskConical className="w-3.5 h-3.5" />
              </div>
              <span className="text-[11px] font-bold text-slate-100 leading-tight">Testing Agent</span>
            </div>
            <p className="text-[10px] text-emerald-200/70 leading-snug">
              Generates and runs unit cases
            </p>
          </div>

          {/* Maintenance Agent */}
          <div 
            onClick={() => setSelectedNode('maintenance')}
            className={`rounded-xl p-2 border transition-all duration-300 cursor-pointer text-center flex flex-col justify-between ${
              isParallelActive 
                ? 'bg-amber-600/30 border-amber-400 shadow-lg shadow-amber-500/30 ring-2 ring-amber-500 scale-[1.03]' 
                : 'bg-amber-950/30 border-amber-500/30 hover:bg-amber-900/30 hover:border-amber-400/60'
            }`}
          >
            <div className="flex flex-col items-center text-amber-400 mb-1">
              <div className="p-1 rounded-md bg-amber-500/10 mb-1">
                <Wrench className="w-3.5 h-3.5" />
              </div>
              <span className="text-[11px] font-bold text-slate-100 leading-tight">Maintenance Agent</span>
            </div>
            <p className="text-[10px] text-amber-200/70 leading-snug">
              Checks dependencies & CVEs
            </p>
          </div>
        </div>

        {/* Converging Connectors */}
        <div className="w-full max-w-sm flex items-center justify-around text-slate-600 px-4">
          <ArrowDown className={`w-3.5 h-3.5 ${isParallelActive || isSupervisorBottomActive ? 'text-indigo-400' : 'text-slate-600'}`} />
          <ArrowDown className={`w-3.5 h-3.5 ${isParallelActive || isSupervisorBottomActive ? 'text-indigo-400' : 'text-slate-600'}`} />
          <ArrowDown className={`w-3.5 h-3.5 ${isParallelActive || isSupervisorBottomActive ? 'text-indigo-400' : 'text-slate-600'}`} />
        </div>

        {/* 4. Supervising Agent (Synthesis) */}
        <div 
          onClick={() => setSelectedNode('supervisor')}
          className={`w-full max-w-sm rounded-xl p-2.5 border transition-all duration-300 cursor-pointer text-center relative ${
            isSupervisorBottomActive 
              ? 'bg-purple-600/30 border-purple-400 shadow-lg shadow-purple-500/30 ring-2 ring-purple-500 scale-[1.02]' 
              : 'bg-purple-950/40 border-purple-500/30 hover:bg-purple-900/40 hover:border-purple-400/60'
          }`}
        >
          <div className="flex items-center justify-center space-x-2 text-purple-400 mb-0.5">
            <Brain className="w-4 h-4" />
            <span className="text-xs font-bold text-slate-100">Supervising Agent</span>
          </div>
          <p className="text-[11px] text-purple-200/80">
            Combines results and creates clear explanation
          </p>
        </div>

        {/* Arrow to Output */}
        <div className="flex justify-center text-slate-600">
          <ArrowDown className={`w-4 h-4 ${isSupervisorBottomActive || isOutputActive ? 'text-indigo-400 animate-bounce' : 'text-slate-600'}`} />
        </div>

        {/* 5. Voice / Chat Output */}
        <div 
          className={`w-full max-w-sm rounded-xl p-2.5 border transition-all duration-300 text-center relative ${
            isOutputActive 
              ? 'bg-indigo-600/40 border-indigo-400 shadow-lg shadow-indigo-500/40 ring-2 ring-indigo-400 scale-[1.02]' 
              : 'bg-indigo-950/40 border-indigo-500/40 hover:bg-indigo-900/40'
          }`}
        >
          <div className="flex items-center justify-center space-x-2 text-indigo-400 mb-0.5">
            <div className="flex items-center gap-1">
              <MessageSquare className="w-3.5 h-3.5" />
              <Volume2 className="w-3.5 h-3.5" />
            </div>
            <span className="text-xs font-bold text-slate-100">Voice / Chat Output</span>
          </div>
          <p className="text-[11px] text-indigo-200/80">
            Delivers insights to developer
          </p>
        </div>
      </div>

      {/* Diagram Footer info */}
      <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-400 flex items-center justify-between">
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"></span>
          Parallel concurrency: 3x
        </span>
        <span className="text-slate-400 font-mono">Avg Latency: 910ms</span>
      </div>
    </div>
  );
}
