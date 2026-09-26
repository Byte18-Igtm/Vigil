import React from 'react';
import { X, ShieldCheck, Check, Lock, Terminal, FileCode2 } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function ConsentModal() {
  const { activeModal, setActiveModal, confirmConsentAndAnalyze } = useApp();

  if (activeModal !== 'consent') return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Permissions & Security Consent</h3>
              <p className="text-[11px] text-slate-400">Local sandboxed access controls</p>
            </div>
          </div>
          <button
            onClick={() => setActiveModal(null)}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-3.5 text-xs text-slate-300">
          <div className="space-y-2">
            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex items-start space-x-3">
              <span className="p-1 rounded bg-emerald-500/10 text-emerald-400 mt-0.5"><Check className="w-3.5 h-3.5" /></span>
              <div>
                <span className="font-semibold text-slate-100">Read Project Files & AST:</span>
                <p className="text-[11px] text-slate-400 mt-0.5">Allows Context Agent to index code structure and dependency tree locally.</p>
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex items-start space-x-3">
              <span className="p-1 rounded bg-emerald-500/10 text-emerald-400 mt-0.5"><Check className="w-3.5 h-3.5" /></span>
              <div>
                <span className="font-semibold text-slate-100">Isolated Unit Test Execution:</span>
                <p className="text-[11px] text-slate-400 mt-0.5">Testing Agent runs test specs inside an ephemeral sandboxed runner without modifying root files.</p>
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex items-start space-x-3">
              <span className="p-1 rounded bg-emerald-500/10 text-emerald-400 mt-0.5"><Check className="w-3.5 h-3.5" /></span>
              <div>
                <span className="font-semibold text-slate-100">Explicit Patch Approval:</span>
                <p className="text-[11px] text-slate-400 mt-0.5">Zero direct modifications without explicit user click or voice command approval.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-800 bg-slate-950 flex justify-end">
          <button
            onClick={() => setActiveModal(null)}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors mr-2"
          >
            Cancel
          </button>
          <button
            onClick={confirmConsentAndAnalyze}
            className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors"
          >
            Confirm &amp; Analyse
          </button>
        </div>
      </div>
    </div>
  );
}
