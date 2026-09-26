import React from 'react';
import { X, Folder, FileCode2, ChevronRight, ChevronDown, CheckCircle2, Shield } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { MOCK_PROJECT_FILES } from '../../data/mockData';

export default function ProjectStructureModal() {
  const { activeModal, setActiveModal, selectedProject } = useApp();

  if (activeModal !== 'structure') return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center space-x-2">
            <Folder className="w-5 h-5 text-indigo-400" />
            <div>
              <h3 className="text-sm font-bold text-white">Project Structure & AST Index</h3>
              <p className="text-[11px] font-mono text-slate-400">{selectedProject.path}</p>
            </div>
          </div>
          <button
            onClick={() => setActiveModal(null)}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tree Content */}
        <div className="p-5 max-h-[420px] overflow-y-auto font-mono text-xs space-y-2">
          <div className="p-2.5 rounded-lg bg-indigo-950/20 border border-indigo-500/20 flex items-center justify-between mb-3 text-slate-300">
            <span>Indexed files: <strong>142 files</strong></span>
            <span className="text-emerald-400 flex items-center gap-1 font-sans text-xs">
              <CheckCircle2 className="w-3.5 h-3.5" /> AST Context Live
            </span>
          </div>

          <div className="pl-2 space-y-2 text-slate-300">
            <div className="flex items-center space-x-2 font-semibold text-indigo-300">
              <Folder className="w-4 h-4 text-indigo-400" />
              <span>src/</span>
            </div>

            <div className="pl-6 space-y-2">
              <div className="flex items-center space-x-2 font-semibold text-blue-300">
                <Folder className="w-4 h-4 text-blue-400" />
                <span>auth/</span>
              </div>
              <div className="pl-6 space-y-1.5 text-slate-400">
                <div className="flex items-center justify-between p-1.5 rounded bg-slate-800/60 border border-slate-700/60 text-slate-200">
                  <div className="flex items-center space-x-2">
                    <FileCode2 className="w-3.5 h-3.5 text-indigo-400" />
                    <span>authService.js</span>
                  </div>
                  <span className="text-[10px] text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/30">
                    Exception at L42
                  </span>
                </div>
                <div className="flex items-center space-x-2 p-1 text-slate-400">
                  <FileCode2 className="w-3.5 h-3.5 text-slate-500" />
                  <span>jwtHelper.js</span>
                </div>
              </div>

              <div className="flex items-center space-x-2 font-semibold text-slate-300">
                <Folder className="w-4 h-4 text-indigo-400" />
                <span>api/</span>
              </div>
              <div className="pl-6 space-y-1 text-slate-400">
                <div className="flex items-center space-x-2 p-1">
                  <FileCode2 className="w-3.5 h-3.5 text-slate-500" />
                  <span>login.js</span>
                </div>
                <div className="flex items-center space-x-2 p-1">
                  <FileCode2 className="w-3.5 h-3.5 text-slate-500" />
                  <span>users.js</span>
                </div>
              </div>

              <div className="flex items-center space-x-2 font-semibold text-slate-300">
                <Folder className="w-4 h-4 text-emerald-400" />
                <span>tests/</span>
              </div>
              <div className="pl-6 space-y-1 text-slate-400">
                <div className="flex items-center space-x-2 p-1">
                  <FileCode2 className="w-3.5 h-3.5 text-emerald-500" />
                  <span>auth.test.js</span>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2 p-1 text-amber-300">
              <FileCode2 className="w-4 h-4 text-amber-400" />
              <span>package.json (jsonwebtoken@2.4.0 outdated)</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-800 bg-slate-950/60 flex justify-end">
          <button
            onClick={() => setActiveModal(null)}
            className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors"
          >
            Close Explorer
          </button>
        </div>
      </div>
    </div>
  );
}
