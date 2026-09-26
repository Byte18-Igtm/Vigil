import React, { useState } from 'react';
import { X, FileCode2, ShieldAlert, ThumbsUp, ThumbsDown } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function InspectCodeModal() {
  const { activeModal, setActiveModal, report, submitDecision } = useApp();
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (activeModal !== 'inspectDiff') return null;

  const loc = report?.location;
  const fileLabel = loc ? `${loc.file} — line ${loc.line}` : 'unknown location';

  const handleDecision = async (decision) => {
    setSubmitting(true);
    await submitDecision(decision, comment || undefined);
    setSubmitting(false);
    setComment('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-4xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center space-x-3">
            <div className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400">
              <FileCode2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Proposed Patch — Awaiting Your Decision</h3>
              <p className="text-[11px] font-mono text-indigo-300">{fileLabel}</p>
            </div>
          </div>
          <button
            onClick={() => setActiveModal(null)}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Banner */}
        <div className="px-5 py-2.5 bg-amber-950/40 border-b border-amber-500/30 flex items-center gap-2 text-xs text-amber-300 font-semibold">
          <ShieldAlert className="w-4 h-4 shrink-0" />
          Proposed — nothing has been applied. Review the patch below and approve or reject.
        </div>

        {/* Body */}
        <div className="p-5 flex-1 overflow-y-auto space-y-4 text-xs">

          {/* Location + code snippet */}
          {loc && (
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Location</div>
              <div className="font-mono text-slate-200">
                {loc.file} : line {loc.line}
              </div>
              {loc.code && (
                <pre className="mt-1 text-[11px] font-mono text-slate-400 whitespace-pre-wrap">{loc.code}</pre>
              )}
            </div>
          )}

          {/* Root cause + selection reason */}
          {(report?.root_cause || report?.selection_reason) && (
            <div className="p-3 rounded-xl bg-blue-950/20 border border-blue-500/20 space-y-1.5">
              <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Root Cause</div>
              {report.root_cause && <p className="text-slate-300 leading-relaxed">{report.root_cause}</p>}
              {report.selection_reason && (
                <p className="text-slate-400 italic">{report.selection_reason}</p>
              )}
            </div>
          )}

          {/* Full diff */}
          {report?.diff && (
            <div className="rounded-xl bg-slate-950 border border-slate-800 overflow-hidden">
              <div className="px-3 py-2 bg-slate-900 border-b border-slate-800 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                Full Diff
              </div>
              <pre className="p-3 text-[11px] font-mono text-slate-300 overflow-x-auto whitespace-pre leading-relaxed">
                {report.diff}
              </pre>
            </div>
          )}

          {/* Per-agent status */}
          {report?.agents && report.agents.length > 0 && (
            <div className="space-y-2">
              <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Agent Results</div>
              {report.agents.map((ag, i) => (
                <div key={i} className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">{ag.name || ag.agent_id}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                      ag.status === 'success' || ag.status === 'completed'
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : ag.status === 'error'
                        ? 'bg-red-500/20 text-red-300'
                        : 'bg-slate-700 text-slate-400'
                    }`}>{ag.status}</span>
                  </div>
                  {ag.error && <p className="text-red-400 text-[11px]">{ag.error}</p>}
                  {ag.evidence && <p className="text-slate-400 text-[11px]">{ag.evidence}</p>}
                  {ag.conflicts && ag.conflicts.length > 0 && (
                    <p className="text-amber-400 text-[11px]">Conflicts: {ag.conflicts.join(', ')}</p>
                  )}
                  {ag.limitations && ag.limitations.length > 0 && (
                    <p className="text-slate-500 text-[11px]">Limitations: {ag.limitations.join(', ')}</p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Patch hash */}
          {report?.patch_hash && (
            <div className="text-[10px] font-mono text-slate-600">
              Patch hash: {report.patch_hash}
            </div>
          )}

          {/* Optional comment */}
          <div>
            <label className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-1.5">
              Comment (optional)
            </label>
            <input
              type="text"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Add a note for the audit trail…"
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3.5 border-t border-slate-800 bg-slate-950 flex items-center justify-between">
          <button
            onClick={() => setActiveModal(null)}
            disabled={submitting}
            className="px-4 py-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white text-xs font-medium transition-colors disabled:opacity-40"
          >
            Close
          </button>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleDecision('reject')}
              disabled={submitting || !report?.patch_hash}
              className="px-4 py-1.5 rounded-lg bg-red-600/80 hover:bg-red-600 text-white text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-40"
            >
              <ThumbsDown className="w-3.5 h-3.5" />
              Reject
            </button>
            <button
              onClick={() => handleDecision('approve')}
              disabled={submitting || !report?.patch_hash}
              className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-emerald-600/30 disabled:opacity-40"
            >
              <ThumbsUp className="w-3.5 h-3.5" />
              {submitting ? 'Submitting…' : 'Approve'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
