import React from 'react';
import { ExternalLink, FolderTree, FileCode2, Terminal, Play, Sparkles } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function QuickActionsCard() {
  const { setActiveModal, setActiveTab, runAgentAnalysis, isAnalyzing } = useApp();

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
      <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
        Quick Actions
      </h2>

      <div className="space-y-2">
        {/* Open in IDE */}
        <button
          onClick={() => setActiveTab('ide')}
          className="w-full flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 text-slate-200 text-xs font-medium transition-all group"
        >
          <div className="flex items-center space-x-2.5">
            <div className="p-1 rounded-md bg-blue-500/10 text-blue-400">
              <ExternalLink className="w-3.5 h-3.5" />
            </div>
            <span>Open in IDE</span>
          </div>
          <span className="text-[10px] text-slate-400 group-hover:text-indigo-400">Launch</span>
        </button>

        {/* View Project Structure */}
        <button
          onClick={() => setActiveModal('structure')}
          className="w-full flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 text-slate-200 text-xs font-medium transition-all group"
        >
          <div className="flex items-center space-x-2.5">
            <div className="p-1 rounded-md bg-indigo-500/10 text-indigo-400">
              <FolderTree className="w-3.5 h-3.5" />
            </div>
            <span>View Project Structure</span>
          </div>
          <span className="text-[10px] text-slate-400 group-hover:text-indigo-400">Explore</span>
        </button>

        {/* View Logs */}
        <button
          onClick={() => setActiveModal('logs')}
          className="w-full flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 text-slate-200 text-xs font-medium transition-all group"
        >
          <div className="flex items-center space-x-2.5">
            <div className="p-1 rounded-md bg-emerald-500/10 text-emerald-400">
              <Terminal className="w-3.5 h-3.5" />
            </div>
            <span>View Logs</span>
          </div>
          <span className="text-[10px] text-slate-400 group-hover:text-emerald-400">Live</span>
        </button>
      </div>
    </div>
  );
}
