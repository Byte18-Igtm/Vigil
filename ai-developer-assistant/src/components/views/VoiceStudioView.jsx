import React, { useState, useEffect } from 'react';
import { 
  Mic, 
  MicOff, 
  Volume2, 
  Sparkles, 
  Play, 
  Pause, 
  Radio, 
  RotateCcw, 
  Brain, 
  CheckCircle2,
  Cpu
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function VoiceStudioView() {
  const { isPlayingAudio, setIsPlayingAudio, isAnalyzing, runAgentAnalysis } = useApp();
  const [isRecording, setIsRecording] = useState(false);
  const [voiceQuery, setVoiceQuery] = useState("Hey DevAssist, check why my login endpoint is returning 500 error.");
  const [speechPitch, setSpeechPitch] = useState(1);
  const [selectedVoice, setSelectedVoice] = useState('Alloy (Natural Neural)');

  const handleToggleRecord = () => {
    if (!isRecording) {
      setIsRecording(true);
      setTimeout(() => {
        setIsRecording(false);
        runAgentAnalysis(voiceQuery);
      }, 2500);
    } else {
      setIsRecording(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      {/* Voice Hero Card */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 md:p-8 text-center shadow-xl relative overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-32 bg-indigo-600/15 blur-3xl pointer-events-none"></div>

        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 text-xs font-semibold mb-4">
          <Radio className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
          <span>Real-Time Bi-Directional Neural Voice</span>
        </div>

        <h2 className="text-xl md:text-3xl font-extrabold text-white tracking-tight">
          Hands-Free Multi-Agent Voice Companion
        </h2>
        <p className="text-sm text-slate-400 max-w-xl mx-auto mt-2">
          Speak naturally while you code. The Supervising Agent routes your question in real time across the Debugging, Testing, and Maintenance swarm.
        </p>

        {/* Animated Visualizer Mic Orb */}
        <div className="my-8 flex flex-col items-center justify-center">
          <div className="relative">
            {isRecording && (
              <div className="absolute -inset-4 rounded-full bg-rose-500/20 animate-ping"></div>
            )}
            {isPlayingAudio && (
              <div className="absolute -inset-4 rounded-full bg-indigo-500/20 animate-pulse"></div>
            )}

            <button
              onClick={handleToggleRecord}
              className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 shadow-2xl relative z-10 ${
                isRecording
                  ? 'bg-rose-600 text-white shadow-rose-600/50 scale-110'
                  : isPlayingAudio
                  ? 'bg-gradient-to-tr from-indigo-600 to-purple-600 text-white shadow-indigo-600/50'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white hover:scale-105 shadow-indigo-600/40'
              }`}
            >
              {isRecording ? (
                <Mic className="w-10 h-10 animate-bounce" />
              ) : isPlayingAudio ? (
                <Volume2 className="w-10 h-10 animate-pulse" />
              ) : (
                <Mic className="w-10 h-10" />
              )}
            </button>
          </div>

          <span className="text-xs font-medium text-slate-400 mt-4">
            {isRecording
              ? 'Listening to speech input...'
              : isPlayingAudio
              ? 'DevAssist speaking...'
              : 'Click microphone or press Space to talk'}
          </span>
        </div>

        {/* Voice Waveform Live Simulation */}
        <div className="flex items-center justify-center gap-1.5 h-12 max-w-md mx-auto">
          {[40, 65, 80, 45, 90, 70, 30, 85, 100, 60, 40, 75, 95, 50, 65, 30, 90, 80, 50, 70].map((h, i) => (
            <div
              key={i}
              className={`w-1.5 rounded-full transition-all duration-200 ${
                isRecording
                  ? 'bg-rose-400 animate-pulse'
                  : isPlayingAudio
                  ? 'bg-indigo-400 animate-pulse'
                  : 'bg-slate-700'
              }`}
              style={{
                height: `${(isRecording || isPlayingAudio) ? Math.max(25, h * (0.5 + Math.random() * 0.6)) : 20}%`
              }}
            />
          ))}
        </div>

        {/* Real-time speech transcript bubble */}
        <div className="mt-6 p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-left max-w-lg mx-auto">
          <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-1">
            Live Speech Transcript:
          </span>
          <p className="text-xs text-slate-200 font-medium italic">
            "{voiceQuery}"
          </p>
        </div>
      </div>

      {/* Voice Configuration & Audio Engine */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Voice Persona & Output Engine
          </h3>
          <div className="space-y-2">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Neural Voice Model:</label>
              <select
                value={selectedVoice}
                onChange={(e) => setSelectedVoice(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option>Alloy (Natural Neural)</option>
                <option>Echo (Calm Studio)</option>
                <option>Fable (Technical British)</option>
                <option>Onyx (Deep Engineering)</option>
                <option>Nova (Energetic Assistant)</option>
              </select>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Multi-Agent Speech Synthesis
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            The voice engine compiles parallel insights into concise 20-40 second audio summaries so you never have to break your coding focus.
          </p>
          <div className="pt-2 flex items-center gap-2 text-emerald-400 text-xs font-medium">
            <CheckCircle2 className="w-4 h-4" />
            <span>Low-Latency WebRTC Stream Ready</span>
          </div>
        </div>
      </div>
    </div>
  );
}
