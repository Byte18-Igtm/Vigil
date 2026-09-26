import React, { useState } from 'react';
import { 
  Settings, 
  ShieldCheck, 
  Cpu, 
  Code2, 
  Terminal, 
  Sliders, 
  Key, 
  Save, 
  CheckCircle2,
  Lock
} from 'lucide-react';

export default function SettingsView() {
  const [model, setModel] = useState('Claude 3.5 Sonnet + GPT-4o Multi-Agent Swarm');
  const [maxConcurrency, setMaxConcurrency] = useState(3);
  const [autoRunTests, setAutoRunTests] = useState(true);
  const [readOnlyMode, setReadOnlyMode] = useState(true);
  const [cveScanning, setCveScanning] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Settings className="w-5 h-5 text-indigo-400" />
            System & Multi-Agent Preferences
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Manage local sandbox permissions, model endpoints, and IDE sidecar integration.
          </p>
        </div>

        <button
          onClick={handleSave}
          className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-indigo-600/30"
        >
          {saved ? <CheckCircle2 className="w-4 h-4 text-emerald-300" /> : <Save className="w-4 h-4" />}
          <span>{saved ? 'Saved Successfully!' : 'Save Settings'}</span>
        </button>
      </div>

      {/* Settings Sections */}
      <div className="space-y-4 text-xs text-slate-300">
        {/* Section 1: AI Swarm Configuration */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
            <Cpu className="w-4 h-4" /> AI Models & Concurrency
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-slate-400 block mb-1">Supervisor Model Engine:</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option>Claude 3.5 Sonnet + GPT-4o Multi-Agent Swarm</option>
                <option>Gemini 1.5 Pro High Context Core</option>
                <option>DeepSeek Coder V2 (Self-Hosted / Local LLM)</option>
              </select>
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Max Parallel Subagent Concurrency:</label>
              <input
                type="number"
                min="1"
                max="8"
                value={maxConcurrency}
                onChange={(e) => setMaxConcurrency(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Security & Permissions */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4" /> Security & Sandboxed Permissions
          </h3>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800/80">
              <div>
                <div className="font-semibold text-slate-200">Require User Approval Before Code Patching</div>
                <div className="text-[11px] text-slate-400">Never write changes directly to disk without explicit click or voice consent.</div>
              </div>
              <input
                type="checkbox"
                checked={readOnlyMode}
                onChange={(e) => setReadOnlyMode(e.target.checked)}
                className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800/80">
              <div>
                <div className="font-semibold text-slate-200">Automated Sandboxed Unit Testing</div>
                <div className="text-[11px] text-slate-400">Allows Testing Agent to spin up ephemeral test runners on proposed patches.</div>
              </div>
              <input
                type="checkbox"
                checked={autoRunTests}
                onChange={(e) => setAutoRunTests(e.target.checked)}
                className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800/80">
              <div>
                <div className="font-semibold text-slate-200">Continuous CVE & Dependency Vulnerability Audits</div>
                <div className="text-[11px] text-slate-400">Maintenance Agent scans package.json against the latest security advisories.</div>
              </div>
              <input
                type="checkbox"
                checked={cveScanning}
                onChange={(e) => setCveScanning(e.target.checked)}
                className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
