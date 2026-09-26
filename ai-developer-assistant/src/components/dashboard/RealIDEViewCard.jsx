import React, { useState } from 'react';
import {
  FileCode2,
  Folder,
  AlertCircle,
  CheckCircle2,
  Copy,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { MOCK_IDE_CODE } from '../../data/mockData';
import { useApp } from '../../context/AppContext';

export default function RealIDEViewCard() {
  const { setActiveModal, setActiveTab } = useApp();
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(MOCK_IDE_CODE);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-xl flex flex-col justify-between">
      {/* IDE Window Top Bar */}
      <div className="bg-slate-900 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {/* Traffic light window controls */}
          <div className="flex space-x-1.5 mr-2">
            <div className="w-3 h-3 rounded-full bg-rose-500/80"></div>
            <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
            <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
          </div>
          <span className="text-xs font-semibold text-slate-300">
            Real IDE View <span className="text-slate-500 font-normal">(Example)</span>
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveModal('inspectDiff')}
            className="text-[11px] px-2 py-0.5 rounded bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 font-medium transition-colors"
          >
            Inspect Diff
          </button>
          <button
            onClick={handleCopy}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            title="Copy code"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Editor Body with File Tree & Code Area */}
      <div className="flex flex-1 min-h-[220px] max-h-[340px] overflow-hidden">
        {/* Mini File Explorer Sidebar */}
        <div className="w-40 bg-slate-950/90 border-r border-slate-800/80 p-2.5 hidden sm:block text-[11px] font-mono select-none">
          <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2">Explorer</div>
          
          <div className="space-y-1">
            <div className="flex items-center space-x-1 text-slate-400 font-semibold">
              <ChevronDown className="w-3 h-3" />
              <Folder className="w-3.5 h-3.5 text-indigo-400" />
              <span>src</span>
            </div>

            <div className="pl-3 space-y-1">
              <div className="flex items-center space-x-1 text-slate-400 font-medium">
                <ChevronDown className="w-3 h-3" />
                <Folder className="w-3.5 h-3.5 text-indigo-400" />
                <span>auth</span>
              </div>

              <div className="pl-3">
                <div className="flex items-center justify-between p-1 rounded bg-indigo-600/20 text-indigo-300 font-medium">
                  <div className="flex items-center space-x-1 truncate">
                    <FileCode2 className="w-3 h-3 text-indigo-400 shrink-0" />
                    <span className="truncate">authService.js</span>
                  </div>
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-ping shrink-0"></span>
                </div>
              </div>

              <div className="pl-3 flex items-center space-x-1 text-slate-400 hover:text-slate-200 p-1">
                <FileCode2 className="w-3 h-3 text-slate-500" />
                <span>jwtHelper.js</span>
              </div>
            </div>

            <div className="pl-3 flex items-center space-x-1 text-slate-400 p-1">
              <ChevronRight className="w-3 h-3 text-slate-600" />
              <Folder className="w-3.5 h-3.5 text-slate-500" />
              <span>api</span>
            </div>

            <div className="pl-3 flex items-center space-x-1 text-slate-400 p-1">
              <ChevronRight className="w-3 h-3 text-slate-600" />
              <Folder className="w-3.5 h-3.5 text-slate-500" />
              <span>tests</span>
            </div>

            <div className="flex items-center space-x-1 text-slate-400 p-1">
              <FileCode2 className="w-3 h-3 text-amber-500/80" />
              <span>package.json</span>
            </div>
          </div>
        </div>

        {/* Code & Error Annotation Pane */}
        <div className="flex-1 flex flex-col bg-slate-950/70 overflow-y-auto">
          {/* Active Tab */}
          <div className="bg-slate-900/60 border-b border-slate-800/80 px-3 py-1 flex items-center space-x-2 text-xs font-mono text-slate-300">
            <FileCode2 className="w-3.5 h-3.5 text-indigo-400" />
            <span>authService.js</span>
            <span className="text-[10px] text-slate-500 font-sans">• UTF-8</span>
          </div>

          {/* Code Text with Error Callout */}
          <div className="p-3 text-xs font-mono leading-relaxed space-y-1 overflow-x-auto text-slate-300">
            <div className="text-slate-500">// File: src/auth/authService.js</div>
            <div><span className="text-purple-400">import</span> jwt <span className="text-purple-400">from</span> <span className="text-emerald-300">'jsonwebtoken'</span>;</div>
            <div><span className="text-purple-400">import</span> &#123; getUserById &#125; <span className="text-purple-400">from</span> <span className="text-emerald-300">'../models/userModel.js'</span>;</div>
            <div className="text-slate-600">...</div>

            {/* Simulated Error Line */}
            <div className="p-2 rounded-lg border bg-red-950/30 border-red-500/40 transition-all">
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="text-slate-400 font-mono">Line 42:</span>
                <span className="text-red-400 font-sans font-semibold flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> Uncaught Exception
                </span>
              </div>
              <div className="space-y-1">
                <div className="text-rose-300 bg-black/40 p-1.5 rounded font-mono text-[11px] border border-rose-500/30">
                  <span className="text-rose-400 font-bold">Error:</span> TokenExpiredError: jwt expired at verify (authService.js:42)
                </div>
                <div className="flex items-center justify-between pt-1">
                  <span className="text-[10px] text-slate-400">Unhandled in try/catch block</span>
                  <button
                    onClick={() => setActiveModal('selectProject')}
                    className="text-[10px] px-2 py-0.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-semibold flex items-center gap-1 transition-colors"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>Analyse with Vigil</span>
                  </button>
                </div>
              </div>
            </div>

            <div className="text-slate-600">...</div>
          </div>
        </div>
      </div>
    </div>
  );
}
