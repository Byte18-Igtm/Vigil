import React, { useState } from 'react';
import {
  Code2,
  FileCode2,
  Folder,
  Sparkles,
  Terminal,
  FlaskConical,
  RefreshCw,
  ChevronDown
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { MOCK_IDE_CODE } from '../../data/mockData';

export default function IDECompanionView() {
  const { runAgentAnalysis, isAnalyzing, setActiveModal } = useApp();
  const [activeTab, setActiveFileTab] = useState('authService.js');
  const [activeTerminalTab, setActiveTerminalTab] = useState('tests');

  return (
    <div className="space-y-4 pb-12">
      {/* Top Banner */}
      <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
            <Code2 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white">DevAssist IDE Companion & Sidecar</h2>
            <p className="text-xs text-slate-400">Live background error interception, AST diffing & automated testing runner</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => runAgentAnalysis()}
            disabled={isAnalyzing}
            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{isAnalyzing ? 'Analyzing...' : 'Scan Buffer with Swarm'}</span>
          </button>
        </div>
      </div>

      {/* Main IDE Window */}
      <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl flex flex-col min-h-[580px]">
        {/* Editor Top Bar */}
        <div className="bg-slate-900 px-4 py-2 border-b border-slate-800 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2">
            <div className="flex space-x-1.5 mr-3">
              <div className="w-3 h-3 rounded-full bg-rose-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
            </div>
            
            <button className="flex items-center space-x-1.5 px-3 py-1 rounded bg-slate-950 text-indigo-300 border-t-2 border-indigo-500 font-mono">
              <FileCode2 className="w-3.5 h-3.5 text-indigo-400" />
              <span>authService.js</span>
              <span className="w-2 h-2 rounded-full bg-rose-400 animate-pulse ml-1"></span>
            </button>
            <button className="flex items-center space-x-1.5 px-3 py-1 rounded hover:bg-slate-800/60 text-slate-400 font-mono">
              <FileCode2 className="w-3.5 h-3.5 text-slate-500" />
              <span>jwtHelper.js</span>
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-[11px] text-slate-400 font-mono">JavaScript (ES2024)</span>
          </div>
        </div>

        {/* Editor Body */}
        <div className="flex-1 flex overflow-hidden">
          {/* File Tree */}
          <div className="w-48 bg-slate-950 border-r border-slate-800 p-3 text-xs font-mono select-none hidden md:block">
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2">Workspace Explorer</div>
            <div className="space-y-1 text-slate-400">
              <div className="flex items-center space-x-1 text-slate-300 font-semibold">
                <ChevronDown className="w-3.5 h-3.5" />
                <Folder className="w-3.5 h-3.5 text-indigo-400" />
                <span>src</span>
              </div>
              <div className="pl-3 space-y-1">
                <div className="flex items-center space-x-1 text-slate-300">
                  <ChevronDown className="w-3.5 h-3.5" />
                  <Folder className="w-3.5 h-3.5 text-indigo-400" />
                  <span>auth</span>
                </div>
                <div className="pl-3">
                  <div className="p-1 rounded bg-indigo-600/20 text-indigo-300 font-medium flex items-center justify-between">
                    <span>authService.js</span>
                    <span className="text-[9px] bg-red-500/20 text-red-400 px-1 rounded">!</span>
                  </div>
                  <div className="p-1 text-slate-400 hover:text-slate-200">jwtHelper.js</div>
                </div>
              </div>
            </div>
          </div>

          {/* Code Area */}
          <div className="flex-1 p-4 font-mono text-xs text-slate-200 overflow-y-auto leading-relaxed bg-slate-950/80">
            <pre className="space-y-1">
              <code>{MOCK_IDE_CODE}</code>
            </pre>
          </div>
        </div>

        {/* Integrated Terminal & Test Harness */}
        <div className="border-t border-slate-800 bg-slate-900 p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-3 text-xs font-semibold">
              <button 
                onClick={() => setActiveTerminalTab('tests')}
                className={`flex items-center space-x-1.5 pb-1 border-b-2 ${activeTerminalTab === 'tests' ? 'border-emerald-500 text-emerald-300' : 'border-transparent text-slate-400'}`}
              >
                <FlaskConical className="w-3.5 h-3.5" />
                <span>Testing Agent Harness (Jest/Vitest)</span>
              </button>
              <button 
                onClick={() => setActiveTerminalTab('terminal')}
                className={`flex items-center space-x-1.5 pb-1 border-b-2 ${activeTerminalTab === 'terminal' ? 'border-indigo-500 text-indigo-300' : 'border-transparent text-slate-400'}`}
              >
                <Terminal className="w-3.5 h-3.5" />
                <span>DevAssist Terminal</span>
              </button>
            </div>

            <button
              onClick={() => setActiveModal('selectProject')}
              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium flex items-center gap-1 transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              <span>New Analysis</span>
            </button>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-950 font-mono text-[11px] text-slate-300 space-y-1">
            <div className="text-emerald-400 font-bold">PASS src/tests/auth.test.js (5 suites passed)</div>
            <div className="text-slate-400">✓ test_valid_jwt_token_returns_user (14 ms)</div>
            <div className="text-slate-400">✓ test_missing_header_returns_401 (8 ms)</div>
            <div className="text-slate-400">✓ test_malformed_signature_returns_403 (12 ms)</div>
            <div className="text-slate-400">✓ test_expired_token_graceful_catch (19 ms)</div>
            <div className="text-slate-400">✓ test_refresh_token_handshake (22 ms)</div>
            <div className="text-slate-500 text-[10px] pt-1">Test Suites: 1 passed, 1 total | Tests: 5 passed, 5 total | Time: 0.812 s</div>
          </div>
        </div>
      </div>
    </div>
  );
}
