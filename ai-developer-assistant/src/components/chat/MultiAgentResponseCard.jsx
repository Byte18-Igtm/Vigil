import React from 'react';
import {
  Sparkles,
  AlertCircle,
  Bug,
  CheckCircle2,
  FlaskConical,
  FileCode2,
  XCircle,
  Terminal,
} from 'lucide-react';
import AudioWaveformPlayer from './AudioWaveformPlayer';
import { useApp } from '../../context/AppContext';

export default function MultiAgentResponseCard({ data, reportData }) {
  const { setActiveModal } = useApp();

  // If we have real backend report data, render real view
  if (reportData) {
    return <ReportCard report={reportData} setActiveModal={setActiveModal} />;
  }

  // Fallback: decorative mock card for the initial pre-session message
  const scenario = data || {};
  const {
    issueSummary = { title: 'Authentication error in login API', file: 'src/auth/authService.js' },
    rootCause = { description: 'Token expiration is not handled properly in the auth service.' },
    followUpPrompt = "Would you like me to inspect the code changes or run the tests again?",
    audioDuration = '0:42'
  } = scenario;

  return (
    <div className="bg-slate-900/90 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-4 sm:p-5 text-slate-200 shadow-lg space-y-4 max-w-2xl transition-all">
      <div className="flex items-center space-x-2 text-xs text-indigo-300 font-medium">
        <div className="w-5 h-5 rounded-md bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
          <Sparkles className="w-3.5 h-3.5" />
        </div>
        <span>Example analysis — connect a project to run a real investigation.</span>
      </div>

      <div className="flex items-start space-x-2.5 p-2.5 rounded-lg bg-red-950/20 border border-red-500/20 text-xs">
        <div className="p-1 rounded bg-red-500/10 text-red-400 shrink-0 mt-0.5">
          <AlertCircle className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="font-bold text-red-300">Issue Summary: </span>
          <span className="text-slate-200">{issueSummary.title}</span>
          {issueSummary.file && (
            <span className="block text-[11px] font-mono text-red-400/80 mt-0.5">
              Target: {issueSummary.file}
            </span>
          )}
        </div>
      </div>

      <div className="flex items-start space-x-2.5 p-2.5 rounded-lg bg-blue-950/20 border border-blue-500/20 text-xs">
        <div className="p-1 rounded bg-blue-500/10 text-blue-400 shrink-0 mt-0.5">
          <Bug className="w-3.5 h-3.5" />
        </div>
        <div>
          <div className="flex items-center gap-1.5 font-bold text-blue-300">
            <span>Root Cause</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-500/20 text-blue-300 font-semibold">
              Debugging Agent
            </span>
          </div>
          <p className="text-slate-300 mt-1 leading-relaxed">{rootCause.description}</p>
        </div>
      </div>

      <p className="text-xs text-slate-300 font-medium pt-1">{followUpPrompt}</p>
      <AudioWaveformPlayer duration={audioDuration} />
    </div>
  );
}

// Real-data card: renders awaiting-approval, completed, or rejected state
function ReportCard({ report, setActiveModal }) {
  const state = report?.state;

  if (state === 'AWAITING_APPROVAL') {
    const loc = report.location;
    return (
      <div className="bg-slate-900/90 border border-amber-500/40 rounded-2xl p-4 sm:p-5 text-slate-200 shadow-lg space-y-3 max-w-2xl">
        <div className="flex items-center gap-2 text-xs text-amber-300 font-semibold">
          <Sparkles className="w-4 h-4 text-amber-400" />
          Investigation complete — patch proposed, awaiting your approval.
        </div>

        {loc && (
          <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-0.5">
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Location</div>
            <div className="font-mono text-slate-200">{loc.file} : line {loc.line}</div>
            {loc.code && <pre className="text-[11px] font-mono text-slate-400 mt-1 whitespace-pre-wrap">{loc.code}</pre>}
          </div>
        )}

        {report.root_cause && (
          <div className="p-2.5 rounded-lg bg-blue-950/20 border border-blue-500/20 text-xs">
            <div className="flex items-center gap-1.5 font-bold text-blue-300 mb-1">
              <Bug className="w-3.5 h-3.5" /> Root Cause
            </div>
            <p className="text-slate-300 leading-relaxed">{report.root_cause}</p>
          </div>
        )}

        <button
          onClick={() => setActiveModal('inspectDiff')}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-semibold transition-all hover:scale-[1.02]"
        >
          <FileCode2 className="w-3.5 h-3.5" />
          <span>Review Full Patch &amp; Decide</span>
        </button>
      </div>
    );
  }

  if (state === 'COMPLETED') {
    const tr = report.test_result;
    return (
      <div className="bg-slate-900/90 border border-emerald-500/40 rounded-2xl p-4 sm:p-5 text-slate-200 shadow-lg space-y-3 max-w-2xl">
        <div className="flex items-center gap-2 text-xs text-emerald-300 font-semibold">
          <CheckCircle2 className="w-4 h-4" />
          Patch approved and applied.
        </div>

        {report.branch && (
          <div className="text-xs font-mono text-slate-400">Branch: <span className="text-slate-200">{report.branch}</span></div>
        )}

        {tr && (
          <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-indigo-300 mb-1">
              <FlaskConical className="w-3.5 h-3.5" /> Test Result
            </div>
            <div className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${tr.passed ? 'bg-emerald-400' : 'bg-rose-400'}`} />
              <span className={tr.passed ? 'text-emerald-300' : 'text-rose-300'}>
                {tr.passed ? 'PASSED' : 'FAILED'} — exit {tr.exit_code}
              </span>
            </div>
            {tr.command && (
              <div className="flex items-center gap-1.5 text-slate-500">
                <Terminal className="w-3 h-3" />
                <code className="text-[10px]">{tr.command}</code>
              </div>
            )}
            {tr.output_tail && (
              <pre className="mt-1 text-[10px] font-mono text-slate-400 whitespace-pre-wrap max-h-28 overflow-y-auto bg-black/40 p-2 rounded">
                {tr.output_tail}
              </pre>
            )}
          </div>
        )}
      </div>
    );
  }

  if (state === 'REJECTED') {
    return (
      <div className="bg-slate-900/90 border border-red-500/30 rounded-2xl p-4 sm:p-5 text-slate-200 shadow-lg space-y-2 max-w-2xl">
        <div className="flex items-center gap-2 text-xs text-red-400 font-semibold">
          <XCircle className="w-4 h-4" />
          Patch rejected. No changes were applied.
        </div>
      </div>
    );
  }

  // Generic fallback for any other state
  return (
    <div className="bg-slate-900/90 border border-slate-700 rounded-2xl p-4 sm:p-5 text-slate-200 shadow-lg space-y-2 max-w-2xl text-xs">
      <div className="flex items-center gap-2 text-indigo-300 font-semibold">
        <Sparkles className="w-4 h-4" />
        State: {state || 'unknown'}
      </div>
    </div>
  );
}
