import React from 'react';
import { 
  UserCheck, 
  FolderGit2, 
  CheckCircle2, 
  Code2, 
  Sparkles, 
  ChevronRight,
  Play,
  Check
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function WorkflowStepsBar() {
  const { selectedProject, setActiveModal, setActiveTab } = useApp();

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3.5 my-5">
      {/* Step 1: Login & Consent */}
      <div className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-xl p-4 flex flex-col justify-between transition-all duration-200 shadow-sm relative group">
        <div>
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center space-x-2">
              <span className="w-5 h-5 rounded-full bg-blue-500 text-white text-[11px] font-bold flex items-center justify-center">
                1
              </span>
              <span className="text-xs font-bold text-slate-200">Login & Consent</span>
            </div>
            <span className="text-emerald-400 bg-emerald-500/10 p-1 rounded-full">
              <Check className="w-3.5 h-3.5" />
            </span>
          </div>

          <div className="my-3 flex justify-center">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400 group-hover:scale-105 transition-transform">
              <UserCheck className="w-6 h-6" />
            </div>
          </div>

          <p className="text-[11px] text-slate-400 text-center leading-relaxed">
            Sign in and accept terms and conditions to allow the system to access your development environment.
          </p>
        </div>

        <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
          <span className="text-emerald-400 font-medium flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Authorized
          </span>
          <button 
            onClick={() => setActiveModal('consent')}
            className="text-indigo-400 hover:text-indigo-300 font-medium"
          >
            Permissions
          </button>
        </div>
      </div>

      {/* Step 2: Select Project */}
      <div className="bg-slate-900/80 border border-slate-800 hover:border-indigo-500/40 rounded-xl p-4 flex flex-col justify-between transition-all duration-200 shadow-sm relative group">
        <div>
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center space-x-2">
              <span className="w-5 h-5 rounded-full bg-indigo-500 text-white text-[11px] font-bold flex items-center justify-center">
                2
              </span>
              <span className="text-xs font-bold text-slate-200">Select Project</span>
            </div>
            <span className="text-emerald-400 bg-emerald-500/10 p-1 rounded-full">
              <Check className="w-3.5 h-3.5" />
            </span>
          </div>

          <div className="my-2 bg-slate-950 p-2 rounded-lg border border-slate-800/90 flex flex-col gap-1.5">
            <div className="flex items-center space-x-2 text-slate-300">
              <FolderGit2 className="w-4 h-4 text-indigo-400 shrink-0" />
              <span className="text-[11px] font-mono truncate text-indigo-200">{selectedProject.path}</span>
            </div>
            <button 
              onClick={() => setActiveModal('selectProject')}
              className="w-full py-1 bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-semibold rounded transition-colors flex items-center justify-center gap-1 shadow-sm"
            >
              <Play className="w-3 h-3 fill-current" />
              <span>Start Session</span>
            </button>
          </div>

          <p className="text-[11px] text-slate-400 text-center leading-relaxed mt-2">
            Choose the project folder you want to work on.
          </p>
        </div>

        <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
          <span className="text-slate-300 font-mono">142 files</span>
          <button 
            onClick={() => setActiveModal('selectProject')}
            className="text-indigo-400 hover:text-indigo-300 font-medium"
          >
            Change
          </button>
        </div>
      </div>

      {/* Step 3: Start Session */}
      <div className="bg-slate-900/80 border border-emerald-500/30 rounded-xl p-4 flex flex-col justify-between transition-all duration-200 shadow-sm relative group bg-gradient-to-b from-emerald-950/10 to-transparent">
        <div>
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center space-x-2">
              <span className="w-5 h-5 rounded-full bg-emerald-500 text-white text-[11px] font-bold flex items-center justify-center">
                3
              </span>
              <span className="text-xs font-bold text-slate-200">Start Session</span>
            </div>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          </div>

          <div className="my-2 flex flex-col items-center text-center">
            <div className="w-10 h-10 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 mb-1.5">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold text-emerald-400">Project Loaded Successfully</span>
          </div>

          <p className="text-[11px] text-slate-400 text-center leading-relaxed">
            Monitoring and analysis ready.
          </p>
        </div>

        <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px]">
          <span className="text-emerald-400 font-medium">AST Indexed</span>
          <span className="text-slate-400">Latency: 120ms</span>
        </div>
      </div>

      {/* Step 4: Work Normally */}
      <div className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-xl p-4 flex flex-col justify-between transition-all duration-200 shadow-sm relative group">
        <div>
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center space-x-2">
              <span className="w-5 h-5 rounded-full bg-blue-600 text-white text-[11px] font-bold flex items-center justify-center">
                4
              </span>
              <span className="text-xs font-bold text-slate-200">Work Normally</span>
            </div>
            <span className="text-[10px] text-blue-400 font-mono">VS Code</span>
          </div>

          <div className="my-3 flex justify-center">
            <div className="w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/30 flex items-center justify-center text-blue-400 group-hover:scale-105 transition-transform">
              <Code2 className="w-6 h-6" />
            </div>
          </div>

          <p className="text-[11px] text-slate-400 text-center leading-relaxed">
            Open your IDE and work as usual. The system understands your context and handles the rest in the background.
          </p>
        </div>

        <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
          <span className="text-blue-400 font-medium flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span> Plugin Attached
          </span>
          <button 
            onClick={() => setActiveTab('ide')}
            className="text-indigo-400 hover:text-indigo-300 font-medium"
          >
            Open IDE
          </button>
        </div>
      </div>

      {/* Step 5: Get Help & Insights */}
      <div className="bg-slate-900/80 border border-slate-800 hover:border-indigo-500/50 rounded-xl p-4 flex flex-col justify-between transition-all duration-200 shadow-sm relative group bg-gradient-to-b from-indigo-950/10 to-transparent">
        <div>
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center space-x-2">
              <span className="w-5 h-5 rounded-full bg-indigo-500 text-white text-[11px] font-bold flex items-center justify-center">
                5
              </span>
              <span className="text-xs font-bold text-slate-200">Get Help & Insights</span>
            </div>
            <span className="text-[10px] text-indigo-400 font-medium">Chat & Voice</span>
          </div>

          <div className="my-3 flex justify-center">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 group-hover:scale-105 transition-transform">
              <Sparkles className="w-6 h-6" />
            </div>
          </div>

          <p className="text-[11px] text-slate-400 text-center leading-relaxed">
            Receive real-time insights, fixes, test results, maintenance alerts, and explanations — all through chat or voice.
          </p>
        </div>

        <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
          <span className="text-indigo-400 font-medium flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"></span> 5 Agents Ready
          </span>
          <button 
            onClick={() => setActiveTab('chat')}
            className="text-indigo-400 hover:text-indigo-300 font-semibold"
          >
            Chat Now
          </button>
        </div>
      </div>
    </div>
  );
}
