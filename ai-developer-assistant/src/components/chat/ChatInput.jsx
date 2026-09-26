import React, { useState } from 'react';
import { Send, Mic, MicOff, Paperclip, Sparkles } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function ChatInput() {
  const [text, setText] = useState('');
  const { runAgentAnalysis, isAnalyzing, voiceMode, setVoiceMode } = useApp();

  const handleSend = (e) => {
    e?.preventDefault();
    if (!text.trim() || isAnalyzing) return;
    runAgentAnalysis(text);
    setText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickPrompt = (prompt) => {
    setText(prompt);
  };

  return (
    <div className="space-y-2 mt-3">
      {/* Quick Suggestion Chips */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-[11px] no-scrollbar">
        <span className="text-slate-500 text-[10px] uppercase font-bold shrink-0">Try:</span>
        <button
          onClick={() => handleQuickPrompt("Check login API for authentication error")}
          className="px-2 py-0.5 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 whitespace-nowrap transition-colors border border-slate-700/60"
        >
          🔍 Auth Error in login API
        </button>
        <button
          onClick={() => handleQuickPrompt("Why is /api/users taking 2.4 seconds?")}
          className="px-2 py-0.5 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 whitespace-nowrap transition-colors border border-slate-700/60"
        >
          ⚡ Query Latency Bottleneck
        </button>
        <button
          onClick={() => handleQuickPrompt("Run security audit on all npm packages")}
          className="px-2 py-0.5 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 whitespace-nowrap transition-colors border border-slate-700/60"
        >
          🛡️ Run CVE Dependency Audit
        </button>
      </div>

      {/* Input Box */}
      <form onSubmit={handleSend} className="relative flex items-center">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={voiceMode ? "Voice mode enabled — speak or type your message..." : "Type your message..."}
          disabled={isAnalyzing}
          className="w-full pl-4 pr-24 py-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all shadow-inner disabled:opacity-60"
        />

        <div className="absolute right-2 flex items-center space-x-1">
          {/* Voice Input Toggle */}
          <button
            type="button"
            onClick={() => setVoiceMode(!voiceMode)}
            className={`p-1.5 rounded-lg transition-colors ${
              voiceMode
                ? 'bg-rose-500/20 text-rose-400 animate-pulse border border-rose-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
            title={voiceMode ? "Voice mode active" : "Enable voice mode"}
          >
            {voiceMode ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
          </button>

          {/* Send Button */}
          <button
            type="submit"
            disabled={!text.trim() || isAnalyzing}
            className="p-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-40 disabled:hover:bg-indigo-600 transition-all shadow-md shadow-indigo-600/30"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>
    </div>
  );
}
