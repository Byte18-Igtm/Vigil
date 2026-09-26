import React, { useEffect, useReducer, useRef, useState } from 'react';
import { api } from '../api/client';

// ---------------------------------------------------------------------------
// State machine
// ---------------------------------------------------------------------------

const INIT = {
  // form
  repoPath: (typeof import.meta !== 'undefined' && import.meta.env?.VITE_DEMO_REPO_PATH) || '',
  bugReport: '',
  consent: false,
  // health
  health: null,
  healthError: null,
  // flow
  phase: 'start',        // start | running | done
  runStage: null,
  sessionId: null,
  report: null,
  runError: null,
  preScan: null,         // scan result from /projects/scan
  // decision
  deciding: false,
  decisionError: null,
};

function reducer(s, a) {
  switch (a.type) {
    case 'HEALTH_OK':    return { ...s, health: a.payload, healthError: null };
    case 'HEALTH_ERR':   return { ...s, healthError: a.error };
    case 'SET_REPO':     return { ...s, repoPath: a.value };
    case 'SET_BUG':      return { ...s, bugReport: a.value };
    case 'SET_CONSENT':  return { ...s, consent: a.value };
    case 'SET_PRESCAN':  return { ...s, preScan: a.scan, bugReport: a.bugReport ?? s.bugReport };
    case 'RUN_START':    return { ...s, phase: 'running', runStage: 'creating', runError: null, report: null, sessionId: null };
    case 'RUN_STAGE':    return { ...s, runStage: a.stage };
    case 'RUN_SESSION':  return { ...s, sessionId: a.sessionId };
    case 'RUN_REPORT':   return { ...s, report: a.report };
    case 'RUN_DONE':     return { ...s, phase: 'done', runStage: null, report: a.report };
    case 'RUN_ERROR':    return { ...s, phase: 'start', runStage: null, runError: a.error };
    case 'DECIDING':     return { ...s, deciding: true, decisionError: null };
    case 'DECISION_ERR': return { ...s, deciding: false, decisionError: a.error };
    case 'DECISION_DONE':return { ...s, deciding: false, report: a.report, phase: 'done' };
    case 'RESET':        return { ...INIT, health: s.health, repoPath: s.repoPath };
    default:             return s;
  }
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function VigilApp() {
  const [s, dispatch] = useReducer(reducer, INIT);
  const cancelRef = useRef(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyList, setHistoryList] = useState([]);
  const [historyEntry, setHistoryEntry] = useState(null); // selected history record
  const [securityOpen, setSecurityOpen] = useState(false);
  const [securityList, setSecurityList] = useState([]);

  // Poll health on mount
  useEffect(() => {
    let alive = true;
    async function poll() {
      try {
        const h = await api.health();
        if (alive) dispatch({ type: 'HEALTH_OK', payload: h });
      } catch (e) {
        if (alive) dispatch({ type: 'HEALTH_ERR', error: e.message || 'Cannot reach backend' });
      }
    }
    poll();
    const t = setInterval(poll, 10000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  const canAnalyse = s.consent && s.repoPath.trim() && s.bugReport.trim() && s.phase === 'start';

  async function handleAnalyse() {
    cancelRef.current = false;
    dispatch({ type: 'RUN_START' });
    try {
      dispatch({ type: 'RUN_STAGE', stage: 'creating' });
      const { session_id } = await api.createSession(
        s.repoPath.trim(), s.bugReport.trim(), true,
        s.preScan || undefined
      );
      if (cancelRef.current) return;
      dispatch({ type: 'RUN_SESSION', sessionId: session_id });

      dispatch({ type: 'RUN_STAGE', stage: 'investigating' });
      const report = await api.investigate(session_id);
      if (cancelRef.current) return;
      dispatch({ type: 'RUN_DONE', report });
    } catch (e) {
      if (!cancelRef.current) dispatch({ type: 'RUN_ERROR', error: e.message || 'Unknown error' });
    }
  }

  async function handleDecision(decision) {
    dispatch({ type: 'DECIDING' });
    try {
      const result = await api.decision(s.sessionId, decision, s.report.patch_hash, 'user');
      dispatch({ type: 'DECISION_DONE', report: result });
    } catch (e) {
      dispatch({ type: 'DECISION_ERR', error: e.message || 'Unknown error' });
    }
  }

  function handleReset() {
    cancelRef.current = true;
    setHistoryEntry(null);
    dispatch({ type: 'RESET' });
  }

  async function openHistory() {
    setHistoryOpen(true);
    try {
      const list = await api.listSessions();
      setHistoryList(list);
    } catch {}
  }

  async function openSecurity() {
    setSecurityOpen(true);
    try {
      const list = await api.getSecurity();
      setSecurityList(list);
    } catch {}
  }

  async function loadHistoryEntry(entry) {
    // Try to fetch full report if in memory
    try {
      const full = await api.getSession(entry.session_id);
      setHistoryEntry(full);
    } catch {
      setHistoryEntry(entry);
    }
    setHistoryOpen(false);
  }

  const reportState = s.report?.state;
  const showProposal = reportState === 'AWAITING_APPROVAL';
  const showResult   = ['COMPLETED','REJECTED','TESTS_FAILED','NO_PATCH','FAILED'].includes(reportState);

  // If showing a history entry in read-only mode
  if (historyEntry) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-200 font-sans">
        <div className="flex">
          <Sidebar onHistory={openHistory} onSecurity={openSecurity} onNew={handleReset} />
          <div className="flex-1 max-w-5xl mx-auto px-4 py-8 space-y-8">
            <Header health={s.health} healthError={s.healthError} />
            <div className="flex items-center gap-3">
              <button onClick={() => setHistoryEntry(null)} className="text-xs text-slate-400 hover:text-slate-200 underline">← Back</button>
              <span className="text-xs text-slate-500">History entry (read-only)</span>
            </div>
            <ResultSection report={historyEntry} readOnly />
          </div>
        </div>
        {historyOpen && <HistoryPanel list={historyList} onClose={() => setHistoryOpen(false)} onSelect={loadHistoryEntry} />}
        {securityOpen && <SecurityPanel list={securityList} onClose={() => setSecurityOpen(false)} />}
      </div>
    );
  }

  const hasReport = !!s.report;
  const isWide = hasReport;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans">
      <div className="flex">
        <Sidebar onHistory={openHistory} onSecurity={openSecurity} onNew={handleReset} />

        {/* Main area */}
        <div className={`flex-1 ${isWide ? 'max-w-7xl' : 'max-w-3xl'} mx-auto px-4 py-8`}>
          <div className="space-y-8">
            <Header health={s.health} healthError={s.healthError} />

            {s.phase === 'start' && (
              <StartSection
                repoPath={s.repoPath}
                bugReport={s.bugReport}
                consent={s.consent}
                canAnalyse={canAnalyse}
                runError={s.runError}
                onRepoPath={v => dispatch({ type: 'SET_REPO', value: v })}
                onBugReport={v => dispatch({ type: 'SET_BUG', value: v })}
                onConsent={v => dispatch({ type: 'SET_CONSENT', value: v })}
                onAnalyse={handleAnalyse}
                onScanResult={(scan, bugReport) => dispatch({ type: 'SET_PRESCAN', scan, bugReport })}
                preScan={s.preScan}
              />
            )}

            {(s.phase === 'running' || s.phase === 'done') && (
              <ProgressSection stage={s.runStage} reportState={reportState} runError={s.runError} />
            )}

            {/* Two-column layout once we have a report */}
            {hasReport && (
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {/* Left column: CodeView + Diff */}
                <div className="space-y-6">
                  <CodeView report={s.report} />
                  <DiffView report={s.report} />
                </div>

                {/* Right column: Agents + Decision */}
                <div className="space-y-6">
                  <AgentsSection report={s.report} />

                  {showProposal && (
                    <ProposalSection
                      report={s.report}
                      deciding={s.deciding}
                      decisionError={s.decisionError}
                      onDecide={handleDecision}
                    />
                  )}

                  {showResult && (
                    <ResultSection report={s.report} preScan={s.preScan} />
                  )}
                </div>
              </div>
            )}

            {(s.phase === 'done' || s.runError) && (
              <div className="pt-2">
                <button
                  onClick={handleReset}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-sm font-semibold text-slate-200 transition-colors"
                >
                  ↩ New analysis
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {historyOpen && <HistoryPanel list={historyList} onClose={() => setHistoryOpen(false)} onSelect={loadHistoryEntry} />}
      {securityOpen && <SecurityPanel list={securityList} onClose={() => setSecurityOpen(false)} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sidebar
// ---------------------------------------------------------------------------

function Sidebar({ onHistory, onSecurity, onNew }) {
  return (
    <aside className="w-14 shrink-0 flex flex-col items-center py-6 gap-4 bg-slate-900 border-r border-slate-800 min-h-screen sticky top-0">
      <button
        onClick={onNew}
        title="New analysis"
        className="w-9 h-9 flex items-center justify-center rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-base font-bold transition-colors"
      >+</button>
      <button
        onClick={onHistory}
        title="History"
        className="w-9 h-9 flex items-center justify-center rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-base transition-colors"
      >⏱</button>
      <button
        onClick={onSecurity}
        title="Security"
        className="w-9 h-9 flex items-center justify-center rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-base transition-colors"
      >🔒</button>
    </aside>
  );
}

// ---------------------------------------------------------------------------
// Header
// ---------------------------------------------------------------------------

function Header({ health, healthError }) {
  let dot = 'bg-slate-600';
  let modeLabel = 'connecting…';
  if (healthError) { dot = 'bg-red-500'; modeLabel = 'backend unreachable'; }
  else if (health) {
    dot = 'bg-emerald-500';
    const m = health.agent_mode || 'unknown';
    modeLabel = m === 'stub' ? 'stub (demo mode)' : m === 'real' ? 'real' : m;
  }

  return (
    <header className="flex items-start justify-between gap-4 pb-4 border-b border-slate-800">
      <div>
        <h1 className="text-2xl font-extrabold text-white tracking-tight">Vigil</h1>
        <p className="text-sm text-indigo-400 mt-0.5">Multi-agent bug fixing with human approval</p>
      </div>
      <div className="flex items-center gap-2 mt-1 shrink-0">
        <span className={`w-2 h-2 rounded-full ${dot}`} />
        <span className="text-xs text-slate-400">{modeLabel}</span>
      </div>
    </header>
  );
}

// ---------------------------------------------------------------------------
// Section 1 — Start
// ---------------------------------------------------------------------------

function StartSection({ repoPath, bugReport, consent, canAnalyse, runError, onRepoPath, onBugReport, onConsent, onAnalyse, onScanResult, preScan }) {
  const [projects, setProjects] = useState([]);
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState(null);

  useEffect(() => {
    api.listProjects().then(setProjects).catch(() => {});
  }, []);

  async function handleScan() {
    if (!repoPath.trim()) return;
    setScanning(true);
    setScanError(null);
    try {
      const result = await api.scanProject(repoPath.trim());
      onScanResult(result.scan, result.bug_report || '');
      if (result.bug_report) onBugReport(result.bug_report);
    } catch (e) {
      setScanError(e.message || 'Scan failed');
    } finally {
      setScanning(false);
    }
  }

  const scanFailures = preScan?.failures || [];

  return (
    <section className="space-y-4">
      <SectionTitle n="1" title="Start" />

      {/* Project dropdown + path */}
      <label className="block space-y-1">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Project</span>
        {projects.length > 0 && (
          <select
            value={repoPath}
            onChange={e => { onRepoPath(e.target.value); onScanResult(null, null); }}
            className="w-full px-3 py-2 mb-1 rounded-lg bg-slate-900 border border-slate-700 text-sm font-mono text-slate-100 focus:outline-none focus:border-indigo-500"
          >
            <option value="">— pick a project —</option>
            {projects.map(p => (
              <option key={p.path} value={p.path}>{p.name}</option>
            ))}
          </select>
        )}
        <input
          type="text"
          value={repoPath}
          onChange={e => { onRepoPath(e.target.value); onScanResult(null, null); }}
          placeholder="/absolute/path/to/repo"
          className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-sm font-mono text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500"
        />
      </label>

      {/* Scan button */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleScan}
          disabled={scanning || !repoPath.trim()}
          className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors"
        >
          {scanning ? 'Scanning…' : '🔍 Scan for bugs'}
        </button>
        {preScan && !preScan.error && scanFailures.length === 0 && (
          <span className="text-sm text-emerald-400 font-semibold">✓ All tests pass — no bugs found</span>
        )}
      </div>

      {/* Scan failures */}
      {scanFailures.length > 0 && (
        <div className="rounded-xl bg-slate-900 border border-amber-500/30 overflow-hidden">
          <div className="px-4 py-2 bg-slate-950 border-b border-amber-500/20 text-[10px] uppercase font-bold text-amber-400 tracking-wider">
            Failing tests
          </div>
          <ul className="px-4 py-3 space-y-2">
            {scanFailures.map((f, i) => (
              <li key={i} className="text-xs font-mono">
                <span className="text-red-400 font-semibold">{f.test}</span>
                {f.file && f.line && <span className="text-slate-500 ml-2">{f.file}:{f.line}</span>}
                {f.message && <div className="text-slate-400 mt-0.5 pl-2">{f.message}</div>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {scanError && <ErrorBox message={scanError} />}

      {/* Bug report */}
      <label className="block space-y-1">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Bug report</span>
        <textarea
          value={bugReport}
          onChange={e => onBugReport(e.target.value)}
          rows={4}
          placeholder="Describe the bug… (or scan above to auto-fill)"
          className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 resize-none"
        />
      </label>

      <label className="flex items-start gap-3 cursor-pointer select-none">
        <input
          type="checkbox"
          checked={consent}
          onChange={e => onConsent(e.target.checked)}
          className="mt-0.5 w-4 h-4 rounded accent-indigo-500"
        />
        <span className="text-sm text-slate-300">
          I allow Vigil to analyse this project; nothing will be changed without my approval.
        </span>
      </label>

      {runError && <ErrorBox message={runError} />}

      <button
        onClick={onAnalyse}
        disabled={!canAnalyse}
        className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors shadow-md shadow-indigo-600/30"
      >
        Analyse
      </button>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 2 — Progress
// ---------------------------------------------------------------------------

const STAGES = [
  { key: 'creating',     label: 'Creating session' },
  { key: 'investigating',label: 'Investigating' },
  { key: 'awaiting',     label: 'Awaiting approval' },
  { key: 'deciding',     label: 'Applying decision' },
];

function reportStateToStage(state) {
  if (!state) return null;
  if (state === 'AWAITING_APPROVAL') return 'awaiting';
  if (['COMPLETED','REJECTED','TESTS_FAILED','NO_PATCH','FAILED'].includes(state)) return 'deciding';
  return 'investigating';
}

function ProgressSection({ stage, reportState, runError }) {
  const activeKey = stage || reportStateToStage(reportState);
  const activeIdx = STAGES.findIndex(s => s.key === activeKey);
  const isDone = ['COMPLETED','REJECTED','TESTS_FAILED','NO_PATCH','FAILED'].includes(reportState);

  return (
    <section className="space-y-3">
      <SectionTitle n="2" title="Progress" />
      <ol className="space-y-1">
        {STAGES.map((st, i) => {
          const done    = i < activeIdx || isDone;
          const current = st.key === activeKey && !isDone;
          return (
            <li key={st.key} className="flex items-center gap-3 text-sm">
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0 ${
                done    ? 'bg-emerald-500 text-white'
                : current ? 'bg-indigo-500 text-white animate-pulse'
                : 'bg-slate-800 text-slate-500'
              }`}>
                {done ? '✓' : i + 1}
              </span>
              <span className={done ? 'text-slate-400 line-through' : current ? 'text-slate-100 font-semibold' : 'text-slate-500'}>
                {st.label}
              </span>
              {current && (
                <span className="ml-1 text-xs text-slate-500 animate-pulse">Running…</span>
              )}
            </li>
          );
        })}
      </ol>
      {runError && <ErrorBox message={runError} />}
    </section>
  );
}

// ---------------------------------------------------------------------------
// CodeView — editor-style panel with context
// ---------------------------------------------------------------------------

function CodeView({ report }) {
  const loc = report?.location;
  if (!loc || !loc.context || loc.context.length === 0) return null;

  return (
    <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden">
      {/* Tab header */}
      <div className="flex items-center gap-2 px-4 py-2 bg-slate-950 border-b border-slate-800">
        <span className="text-[11px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">{loc.file}</span>
      </div>
      {/* Line content */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono border-collapse">
          <tbody>
            {loc.context.map((entry) => {
              const isTarget = entry.target === true;
              return (
                <tr
                  key={entry.line}
                  className={isTarget ? 'bg-red-950/40 border-l-2 border-red-500' : ''}
                >
                  <td className="select-none pl-3 pr-4 py-0.5 text-right text-slate-600 w-10 shrink-0">
                    {entry.line}
                  </td>
                  <td className="pr-4 py-0.5 whitespace-pre text-slate-300">
                    {entry.code}
                    {isTarget && (
                      <span className="ml-4 text-red-400 font-semibold not-italic">
                        {'← Bug found here'}
                        {report.root_cause && <span className="ml-2 text-red-300 font-normal">({report.root_cause})</span>}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// DiffView — colored diff with Before/After toggle
// ---------------------------------------------------------------------------

function DiffView({ report }) {
  const patch = report?.patch;
  if (!patch) return null;

  const [mode, setMode] = useState('diff'); // 'diff' | 'before' | 'after'

  // Parse hunk headers for line numbers
  const lines = patch.split('\n');

  // Build before/after content from diff
  const beforeLines = [];
  const afterLines = [];
  let oldLine = 0, newLine = 0;

  for (const line of lines) {
    if (line.startsWith('@@')) {
      // Parse @@ -a,b +c,d @@
      const m = line.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
      if (m) { oldLine = parseInt(m[1]); newLine = parseInt(m[2]); }
      continue;
    }
    if (line.startsWith('---') || line.startsWith('+++')) continue;
    if (line.startsWith('diff ') || line.startsWith('index ')) continue;
    if (line.startsWith('-')) {
      beforeLines.push({ line: oldLine++, text: line.slice(1) });
    } else if (line.startsWith('+')) {
      afterLines.push({ line: newLine++, text: line.slice(1) });
    } else {
      beforeLines.push({ line: oldLine, text: line.slice(1) });
      afterLines.push({ line: newLine, text: line.slice(1) });
      oldLine++; newLine++;
    }
  }

  // For "target" lines in before/after: find the bug line
  const bugLine = report?.location?.line;

  return (
    <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-slate-950 border-b border-slate-800">
        <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Diff</span>
        <div className="flex items-center gap-1">
          {['diff','before','after'].map(m => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors ${mode === m ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'}`}
            >
              {m === 'diff' ? 'Diff' : m === 'before' ? 'Before' : 'After'}
            </button>
          ))}
        </div>
      </div>

      {mode === 'diff' && (
        <pre className="px-0 py-2 text-xs font-mono overflow-x-auto leading-relaxed">
          {(() => {
            let ol = 0, nl = 0;
            return lines.map((line, i) => {
              let lineNum = '';
              if (line.startsWith('@@')) {
                const m = line.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
                if (m) { ol = parseInt(m[1]); nl = parseInt(m[2]); }
                return <span key={i} className="text-indigo-400 block px-4">{line}</span>;
              }
              if (line.startsWith('---') || line.startsWith('+++') || line.startsWith('diff ') || line.startsWith('index ')) {
                return <span key={i} className="text-slate-500 block px-4">{line}</span>;
              }
              if (line.startsWith('-')) {
                lineNum = ol++;
                return (
                  <span key={i} className="text-red-400 block px-4">
                    <span className="select-none text-slate-600 mr-3 w-8 inline-block text-right">{lineNum}</span>
                    {line}
                  </span>
                );
              }
              if (line.startsWith('+')) {
                lineNum = nl++;
                return (
                  <span key={i} className="text-emerald-400 block px-4">
                    <span className="select-none text-slate-600 mr-3 w-8 inline-block text-right">{lineNum}</span>
                    {line}
                  </span>
                );
              }
              lineNum = ol; ol++; nl++;
              return (
                <span key={i} className="text-slate-400 block px-4">
                  <span className="select-none text-slate-600 mr-3 w-8 inline-block text-right">{lineNum}</span>
                  {line}
                </span>
              );
            });
          })()}
        </pre>
      )}

      {mode === 'before' && (
        <table className="w-full text-xs font-mono border-collapse">
          <tbody>
            {beforeLines.map((entry, i) => (
              <tr key={i} className={entry.line === bugLine ? 'bg-red-950/40 border-l-2 border-red-500' : ''}>
                <td className="select-none pl-3 pr-4 py-0.5 text-right text-slate-600 w-10">{entry.line}</td>
                <td className="pr-4 py-0.5 whitespace-pre text-slate-300">{entry.text}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {mode === 'after' && (
        <table className="w-full text-xs font-mono border-collapse">
          <tbody>
            {afterLines.map((entry, i) => (
              <tr key={i}>
                <td className="select-none pl-3 pr-4 py-0.5 text-right text-slate-600 w-10">{entry.line}</td>
                <td className="pr-4 py-0.5 whitespace-pre text-emerald-300">{entry.text}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section 3 — Agents
// ---------------------------------------------------------------------------

function AgentsSection({ report }) {
  const statuses = report.agent_statuses || [];
  const evidence = report.evidence || [];
  const isPending = report.state === 'INVESTIGATING' || report.state === 'UNDERSTANDING';

  // Build per-agent findings from evidence
  const allFindings = [];
  for (const res of (report._agent_results || [])) {
    for (const f of (res.findings || [])) {
      allFindings.push({ agent: res.agent, file: f.file, line: f.line });
    }
  }

  // Find file+line agreements between debug and test
  function getAgreement(agentKey, otherKey) {
    const myFindings = evidence.filter(e => e.source === agentKey);
    const otherFindings = evidence.filter(e => e.source === otherKey);
    // Look for shared file:line in content (heuristic: "file:line" pattern)
    const lineRe = /(\S+):(\d+)/;
    for (const a of myFindings) {
      const ma = a.content.match(lineRe);
      if (!ma) continue;
      for (const b of otherFindings) {
        const mb = b.content.match(lineRe);
        if (mb && ma[1] === mb[1] && ma[2] === mb[2]) {
          return { file: ma[1], line: ma[2] };
        }
      }
    }
    return null;
  }

  const agents = ['debug', 'test'].map(key => ({
    key,
    label: key === 'debug' ? 'Debug Agent' : 'Test Agent',
    status: statuses.find(s => s.agent === key) || null,
    evidence: evidence.filter(e => e.source === key),
    isPending,
  }));

  const agreement = getAgreement('debug', 'test');

  return (
    <section className="space-y-3">
      <SectionTitle n="3" title="Agents" />
      {agreement && (
        <div className="px-3 py-2 rounded-lg bg-emerald-950/30 border border-emerald-500/20 text-xs text-emerald-400">
          ✓ Agrees with Debug on line {agreement.file}:{agreement.line}
        </div>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {agents.map(ag => (
          <AgentCard key={ag.key} agent={ag} allStatuses={statuses} />
        ))}
      </div>
    </section>
  );
}

function AgentCard({ agent, allStatuses }) {
  const st = agent.status;
  const isPending = agent.isPending && !st;
  const statusColor = !st ? 'text-slate-500'
    : st.status === 'ok'      ? 'text-emerald-400'
    : st.status === 'failed'  ? 'text-red-400'
    : st.status === 'timeout' ? 'text-amber-400'
    : 'text-slate-400';

  return (
    <div className="rounded-xl bg-slate-900 border border-slate-800 p-4 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-bold text-slate-100">{agent.label}</span>
        {isPending ? (
          <span className="flex items-center gap-1.5 text-xs text-slate-400">
            <span className="w-3 h-3 border-2 border-slate-500 border-t-indigo-400 rounded-full animate-spin inline-block" />
            Running…
          </span>
        ) : st ? (
          <span className={`text-xs font-semibold ${statusColor}`}>{st.status}</span>
        ) : null}
      </div>
      {st?.error && <p className="text-xs text-red-400">{st.error}</p>}
      {agent.evidence.length > 0 && (
        <ul className="space-y-1 mt-1">
          {agent.evidence.map(ev => (
            <li key={ev.id} className="text-[11px] text-slate-400 leading-relaxed">
              <span className="text-slate-500 font-mono uppercase tracking-wider mr-1">[{ev.type}]</span>
              {ev.content}
            </li>
          ))}
        </ul>
      )}
      {!st && !isPending && agent.evidence.length === 0 && (
        <p className="text-xs text-slate-600 italic">No data from this agent.</p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section 4 — Proposal (right column)
// ---------------------------------------------------------------------------

function ProposalSection({ report, deciding, decisionError, onDecide }) {
  const conflicts = report.conflicts || [];
  const limitations = report.limitations || [];

  return (
    <section className="space-y-4">
      <SectionTitle n="4" title="Proposal" />

      {/* Banner */}
      <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-amber-950/50 border border-amber-500/40 text-xs font-semibold text-amber-300">
        <span>⚠</span>
        Proposed — nothing has been applied.
      </div>

      {/* Root cause + selection reason */}
      {(report.root_cause || report.selection_reason) && (
        <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden">
          <div className="px-4 py-2 bg-slate-950 border-b border-slate-800 text-[10px] uppercase font-bold text-slate-500 tracking-wider">
            Root cause
          </div>
          <div className="px-4 py-3 space-y-2">
            {report.root_cause && <p className="text-sm text-slate-300 leading-relaxed">{report.root_cause}</p>}
            {report.selection_reason && (
              <p className="text-xs text-slate-500 italic">{report.selection_reason}</p>
            )}
          </div>
        </div>
      )}

      {/* Conflicts */}
      {conflicts.length > 0 && (
        <div className="rounded-xl bg-slate-900 border border-amber-500/20 overflow-hidden">
          <div className="px-4 py-2 bg-slate-950 border-b border-amber-500/20 text-[10px] uppercase font-bold text-amber-500 tracking-wider">
            Conflicts
          </div>
          <ul className="px-4 py-3 space-y-1">
            {conflicts.map((c, i) => (
              <li key={i} className="text-xs text-slate-300">
                <span className="text-amber-400 font-semibold">{c.agents_involved?.join(', ')}: </span>
                {c.description}
                {c.resolution !== 'open' && <span className="text-slate-500"> — {c.resolution}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Limitations */}
      {limitations.length > 0 && (
        <div className="px-4 py-3 rounded-xl bg-slate-900 border border-slate-800">
          <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1.5">Limitations</p>
          <ul className="space-y-0.5">
            {limitations.map((l, i) => <li key={i} className="text-xs text-slate-500">• {l}</li>)}
          </ul>
        </div>
      )}

      {decisionError && <ErrorBox message={decisionError} />}

      {/* Approve / Reject */}
      <div className="flex items-center gap-3 pt-1">
        <button
          onClick={() => onDecide('reject')}
          disabled={deciding}
          className="px-5 py-2.5 rounded-lg bg-red-700/80 hover:bg-red-600 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors"
        >
          Reject
        </button>
        <button
          onClick={() => onDecide('approve')}
          disabled={deciding}
          className="px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors shadow-md shadow-emerald-600/30"
        >
          {deciding ? 'Submitting…' : 'Approve'}
        </button>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 5 — Result
// ---------------------------------------------------------------------------

function ResultSection({ report, preScan, readOnly }) {
  const tr = report.test_result;
  const rejected = report.state === 'REJECTED';
  const audit = report.audit || [];
  const preScanFailures = preScan?.failures || [];

  function exportMarkdown() {
    const lines = [
      `# Vigil Report`,
      `**Session:** ${report.session_id || report.session_id || 'n/a'}`,
      `**State:** ${report.state || report.final_state}`,
      `**Patch hash:** ${report.patch_hash || 'n/a'}`,
      ``,
      `## Bug report`,
      report.explanation || report.bug_report || 'n/a',
      ``,
      `## Root cause`,
      report.root_cause || 'n/a',
      ``,
      `## Audit`,
      ...audit.map(a => `- ${a.decision} by ${a.approver} at ${a.timestamp}`),
      ``,
      `## Test result`,
      tr ? `${tr.passed ? 'PASSED' : 'FAILED'} (exit ${tr.exit_code})` : 'n/a',
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'vigil_report.md'; a.click();
    URL.revokeObjectURL(url);
  }

  function exportJSON() {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'vigil_report.json'; a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="space-y-3">
      <SectionTitle n="5" title="Result" />

      {rejected ? (
        <div className="px-4 py-3 rounded-xl bg-slate-900 border border-red-500/30 text-sm text-red-400 font-semibold">
          Rejected — nothing was changed.
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">State</span>
            <span className={`text-sm font-semibold ${report.state === 'COMPLETED' ? 'text-emerald-400' : 'text-red-400'}`}>
              {report.state || report.final_state}
            </span>
          </div>

          {report.branch && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Branch</span>
              <code className="text-sm font-mono text-slate-200">{report.branch}</code>
            </div>
          )}

          {/* Before / After test result */}
          {(preScanFailures.length > 0 || tr) && (
            <div className="flex items-start gap-4 flex-wrap">
              {preScanFailures.length > 0 && (
                <div className="rounded-lg bg-red-950/30 border border-red-500/20 px-3 py-2">
                  <span className="text-[10px] uppercase font-bold text-red-500 tracking-wider block mb-1">Before</span>
                  {preScanFailures.map((f, i) => (
                    <div key={i} className="text-xs text-red-400 font-mono">{f.test}</div>
                  ))}
                </div>
              )}
              {tr && (
                <div className={`rounded-lg border px-3 py-2 ${tr.passed ? 'bg-emerald-950/30 border-emerald-500/20' : 'bg-red-950/30 border-red-500/20'}`}>
                  <span className={`text-[10px] uppercase font-bold tracking-wider block mb-1 ${tr.passed ? 'text-emerald-500' : 'text-red-500'}`}>After</span>
                  <span className={`text-xs font-semibold ${tr.passed ? 'text-emerald-400' : 'text-red-400'}`}>
                    {tr.passed ? 'Tests passed' : 'Tests failed'}
                  </span>
                </div>
              )}
            </div>
          )}

          {tr && (
            <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden">
              <div className="px-4 py-2 bg-slate-950 border-b border-slate-800 text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                Test result
              </div>
              <div className="px-4 py-3 space-y-2">
                <div className="flex items-center gap-4 text-sm">
                  <span className={`font-bold ${tr.passed ? 'text-emerald-400' : 'text-red-400'}`}>
                    {tr.passed ? 'PASSED' : 'FAILED'}
                  </span>
                  <span className="text-slate-500 text-xs">exit {tr.exit_code}</span>
                </div>
                {tr.command && <p className="text-[11px] font-mono text-slate-500">{tr.command}</p>}
                {tr.output_tail && (
                  <pre className="text-[11px] font-mono text-slate-400 bg-black/40 rounded p-2 overflow-x-auto whitespace-pre-wrap max-h-40 overflow-y-auto">
                    {tr.output_tail}
                  </pre>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Audit list */}
      {audit.length > 0 && (
        <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden">
          <div className="px-4 py-2 bg-slate-950 border-b border-slate-800 text-[10px] uppercase font-bold text-slate-500 tracking-wider">
            Audit
          </div>
          <ul className="px-4 py-3 space-y-1">
            {audit.map((a, i) => (
              <li key={i} className="text-xs text-slate-300">
                <span className={`font-semibold mr-1 ${a.decision === 'approve' ? 'text-emerald-400' : 'text-red-400'}`}>
                  {a.decision}
                </span>
                by <span className="text-slate-200">{a.approver}</span>
                <span className="text-slate-500 ml-2">{new Date(a.timestamp).toLocaleString()}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Export buttons */}
      {!readOnly && (
        <div className="flex gap-3 pt-1">
          <button
            onClick={exportMarkdown}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-sm text-slate-200 transition-colors"
          >
            Export Markdown
          </button>
          <button
            onClick={exportJSON}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-sm text-slate-200 transition-colors"
          >
            Export JSON
          </button>
        </div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// History panel (slide-in overlay)
// ---------------------------------------------------------------------------

const STATE_COLORS = {
  COMPLETED:   'bg-emerald-600',
  REJECTED:    'bg-red-700',
  TESTS_FAILED:'bg-amber-600',
  FAILED:      'bg-red-900',
  NO_PATCH:    'bg-slate-600',
  CREATED:     'bg-slate-700',
  AWAITING_APPROVAL: 'bg-indigo-600',
};

function HistoryPanel({ list, onClose, onSelect }) {
  return (
    <div className="fixed inset-0 z-40 flex">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative ml-14 w-80 bg-slate-900 border-r border-slate-800 h-full overflow-y-auto shadow-xl z-50">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
          <h2 className="text-sm font-bold text-slate-200">History</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-200 text-lg leading-none">×</button>
        </div>
        {list.length === 0 && <p className="px-4 py-4 text-xs text-slate-500 italic">No history yet.</p>}
        <ul className="divide-y divide-slate-800">
          {list.map(entry => {
            const state = entry.state || entry.final_state || '';
            const color = STATE_COLORS[state] || 'bg-slate-700';
            return (
              <li
                key={entry.session_id}
                className="px-4 py-3 hover:bg-slate-800 cursor-pointer"
                onClick={() => onSelect(entry)}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-[10px] font-bold text-white px-1.5 py-0.5 rounded ${color}`}>{state}</span>
                  <span className="text-[10px] text-slate-500">{entry.created_at ? new Date(entry.created_at).toLocaleString() : ''}</span>
                </div>
                <p className="text-xs text-slate-300 truncate">{entry.bug_report || '—'}</p>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Security panel
// ---------------------------------------------------------------------------

function SecurityPanel({ list, onClose }) {
  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-96 bg-slate-900 border-l border-slate-800 h-full overflow-y-auto shadow-xl z-50">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
          <h2 className="text-sm font-bold text-slate-200">Security Guarantees</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-200 text-lg leading-none">×</button>
        </div>
        {list.length === 0 && <p className="px-4 py-4 text-xs text-slate-500 italic">Loading…</p>}
        <ul className="divide-y divide-slate-800">
          {list.map((item, i) => (
            <li key={i} className="px-4 py-3 space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-emerald-400">✓</span>
                <span className="text-sm font-semibold text-slate-200">{item.guarantee}</span>
              </div>
              <p className="text-xs text-slate-400">{item.description}</p>
              <p className="text-[10px] font-mono text-slate-500">{item.file} · {item.function}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Shared primitives
// ---------------------------------------------------------------------------

function SectionTitle({ n, title }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="w-6 h-6 rounded-full bg-indigo-600 flex items-center justify-center text-[11px] font-bold text-white shrink-0">
        {n}
      </span>
      <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider">{title}</h2>
    </div>
  );
}

function ErrorBox({ message }) {
  return (
    <div className="px-4 py-3 rounded-lg bg-red-950/40 border border-red-500/40 text-sm text-red-400">
      {message}
    </div>
  );
}
