import React from 'react';
import { Sparkles, Activity, ShieldCheck, Cpu, RefreshCw } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function Header() {
  const { isAnalyzing, runAgentAnalysis, setActiveModal } = useApp();

  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 py-4">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Left: App Title & Subtitle */}
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-200 bg-clip-text">
                Vigil
              </h1>
              <span className="hidden sm:inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                <Sparkles className="w-3 h-3 text-indigo-400" /> Multi-Agent Core
            </span>
          </div>
          <p className="text-sm font-medium text-indigo-400 mt-0.5">
            Autonomous patch proposal with human approval.
          </p>
        </div>

        {/* Right: Explanatory Subtext & System Health Badge */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 lg:max-w-xl">
          <p className="text-xs text-slate-400 leading-relaxed font-normal">
            An intelligent multi-agent system that helps developers across the complete software development lifecycle — from code understanding to debugging, testing, maintenance, and beyond.
          </p>
          
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => setActiveModal('selectProject')}
              disabled={isAnalyzing}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all shadow-md ${
                isAnalyzing
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 cursor-wait'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/30 hover:shadow-indigo-500/40'
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzing ? 'animate-spin' : ''}`} />
              <span>{isAnalyzing ? 'Agents Running...' : 'Select Project'}</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
