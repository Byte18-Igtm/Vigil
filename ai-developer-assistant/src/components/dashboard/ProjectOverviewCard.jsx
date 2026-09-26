import React from 'react';
import { Folder, GitBranch, Shield, Sparkles, CheckCircle2 } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function ProjectOverviewCard() {
  const { selectedProject, setActiveModal } = useApp();

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Project Overview
        </h2>
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          Session Active
        </span>
      </div>

      <div className="flex items-start space-x-3 p-3 rounded-lg bg-slate-950/70 border border-slate-800/80">
        <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
          <Folder className="w-5 h-5 fill-indigo-500/20" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-100 truncate">
              {selectedProject.name}
            </h3>
            <span className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
              <GitBranch className="w-3 h-3 text-indigo-400" /> {selectedProject.branch}
            </span>
          </div>
          <p className="text-[11px] font-mono text-indigo-300 truncate mt-0.5">
            {selectedProject.path}
          </p>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
        <div className="p-2 rounded-md bg-slate-950/40 border border-slate-800/60 flex items-center justify-between">
          <span className="text-slate-400">Framework</span>
          <span className="text-slate-200 font-medium">Node / React</span>
        </div>
        <div className="p-2 rounded-md bg-slate-950/40 border border-slate-800/60 flex items-center justify-between">
          <span className="text-slate-400">Health Score</span>
          <span className="text-emerald-400 font-bold">{selectedProject.healthScore}%</span>
        </div>
      </div>
    </div>
  );
}
