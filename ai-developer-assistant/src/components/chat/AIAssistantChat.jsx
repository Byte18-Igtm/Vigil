import React, { useRef, useEffect } from 'react';
import { Sparkles, Mic, User, Bot, Loader2, ArrowRight } from 'lucide-react';
import MultiAgentResponseCard from './MultiAgentResponseCard';
import ChatInput from './ChatInput';
import { useApp } from '../../context/AppContext';

export default function AIAssistantChat() {
  const { 
    chatMessages, 
    voiceMode, 
    setVoiceMode, 
    isAnalyzing, 
    activeWorkflowStage,
    currentScenario
  } = useApp();

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, isAnalyzing]);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 sm:p-5 flex flex-col h-full shadow-sm">
      {/* Header with Voice Mode Toggle */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 shrink-0">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              AI Assistant
            </h2>
            <span className="text-[10px] text-slate-400 font-medium">Multi-Agent Orchestrator</span>
          </div>
        </div>

        {/* Voice Mode Toggle Switch */}
        <div className="flex items-center space-x-2">
          <span className="text-xs font-medium text-slate-400">Voice Mode</span>
          <button
            type="button"
            onClick={() => setVoiceMode(!voiceMode)}
            className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
              voiceMode ? 'bg-indigo-600' : 'bg-slate-700'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                voiceMode ? 'translate-x-4' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1 min-h-[360px] max-h-[580px]">
        {chatMessages.map((msg) => {
          if (msg.sender === 'user') {
            return (
              <div key={msg.id} className="flex items-start justify-end space-x-2.5">
                <div className="bg-indigo-600/90 text-white text-xs px-4 py-2.5 rounded-2xl rounded-tr-sm max-w-md shadow-md">
                  <p className="leading-relaxed">{msg.text}</p>
                  <span className="block text-[10px] text-indigo-200 text-right mt-1 opacity-80">
                    {msg.timestamp || 'Just now'}
                  </span>
                </div>
                <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-rose-500 to-amber-500 flex items-center justify-center font-bold text-[10px] text-white shrink-0 mt-0.5 shadow-sm">
                  AJ
                </div>
              </div>
            );
          }

          if (msg.isError) {
            return (
              <div key={msg.id} className="flex items-start space-x-2.5">
                <div className="w-7 h-7 rounded-lg bg-red-600/80 flex items-center justify-center text-white shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="px-4 py-2.5 rounded-2xl bg-red-950/40 border border-red-500/30 text-xs text-red-300 max-w-md">
                  {msg.text}
                </div>
              </div>
            );
          }
          return (
            <div key={msg.id} className="flex items-start space-x-2.5">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shrink-0 mt-0.5 shadow-md shadow-indigo-600/30">
                <Bot className="w-4 h-4" />
              </div>
              <MultiAgentResponseCard data={msg.scenarioData || currentScenario} reportData={msg.reportData} />
            </div>
          );
        })}

        {/* Live Multi-Agent Execution Progress Indicator */}
        {isAnalyzing && (
          <div className="flex items-start space-x-2.5 animate-fadeIn">
            <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white shrink-0 mt-0.5 animate-bounce">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="p-4 rounded-2xl bg-slate-950/80 border border-indigo-500/40 text-xs text-slate-200 space-y-2 max-w-md shadow-lg shadow-indigo-500/10">
              <div className="flex items-center space-x-2 text-indigo-400 font-semibold">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                <span>Multi-Agent Swarm Running...</span>
              </div>
              <div className="space-y-1.5 text-[11px] text-slate-400 pl-2 border-l border-slate-800">
                <p className={activeWorkflowStage === 'context' ? 'text-blue-400 font-bold' : ''}>
                  • Context Agent: Indexing AST & buffer stack...
                </p>
                <p className={activeWorkflowStage === 'supervisor' ? 'text-purple-400 font-bold' : ''}>
                  • Supervising Agent: Dispatching worker subagents...
                </p>
                <p className={activeWorkflowStage === 'parallel' ? 'text-amber-400 font-bold' : ''}>
                  • Parallel: Debugging + Testing + Maintenance agents analyzing...
                </p>
                <p className={activeWorkflowStage === 'synthesis' ? 'text-emerald-400 font-bold' : ''}>
                  • Supervising Agent: Synthesizing final resolution...
                </p>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input Container */}
      <ChatInput />
    </div>
  );
}
