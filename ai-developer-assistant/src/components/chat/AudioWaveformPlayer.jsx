import React, { useState } from 'react';
import { Play, Pause, Volume2, ThumbsUp, ThumbsDown, Sparkles } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function AudioWaveformPlayer({ duration = "0:42" }) {
  const { isPlayingAudio, setIsPlayingAudio, audioProgress, setAudioProgress } = useApp();
  const [feedback, setFeedback] = useState(null); // 'like' | 'dislike' | null

  // Waveform bars heights pattern
  const bars = [
    30, 45, 60, 85, 40, 70, 95, 55, 30, 65, 80, 100, 75, 45, 90, 60, 35, 70, 85, 40, 60, 75, 30, 50, 80, 65, 40, 55, 30, 20
  ];

  const togglePlay = () => {
    setIsPlayingAudio(!isPlayingAudio);
  };

  return (
    <div className="mt-3 p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between gap-3 shadow-inner">
      {/* Play/Pause Button */}
      <button
        onClick={togglePlay}
        className="w-8 h-8 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white flex items-center justify-center shrink-0 transition-transform active:scale-95 shadow-md shadow-indigo-600/30"
        title={isPlayingAudio ? "Pause Audio" : "Play Voice Explanation"}
      >
        {isPlayingAudio ? (
          <Pause className="w-3.5 h-3.5 fill-current" />
        ) : (
          <Play className="w-3.5 h-3.5 fill-current ml-0.5" />
        )}
      </button>

      {/* Animated Waveform Visualizer */}
      <div 
        className="flex-1 flex items-center gap-0.5 sm:gap-1 h-6 cursor-pointer overflow-hidden px-1"
        onClick={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          const clickX = e.clientX - rect.left;
          const newProgress = Math.max(0, Math.min(1, clickX / rect.width));
          setAudioProgress(newProgress);
        }}
      >
        {bars.map((height, idx) => {
          const barProgress = idx / bars.length;
          const isPlayed = barProgress <= audioProgress;
          return (
            <div
              key={idx}
              className={`w-1 rounded-full transition-all duration-150 ${
                isPlayed
                  ? 'bg-indigo-400'
                  : 'bg-slate-700 hover:bg-slate-600'
              } ${isPlayingAudio && isPlayed ? 'animate-pulse' : ''}`}
              style={{
                height: `${isPlayingAudio ? Math.max(20, (height * (0.6 + Math.random() * 0.5))) : height}%`,
              }}
            />
          );
        })}
      </div>

      {/* Duration & Volume */}
      <div className="flex items-center space-x-2 shrink-0 text-slate-400 text-xs font-mono">
        <span className="text-indigo-300 font-semibold">{duration}</span>
        <Volume2 className="w-3.5 h-3.5 text-slate-400 hover:text-indigo-400 cursor-pointer transition-colors" />
      </div>

      {/* Feedback Thumbs */}
      <div className="flex items-center space-x-1 border-l border-slate-800 pl-2 shrink-0">
        <button
          onClick={() => setFeedback(feedback === 'like' ? null : 'like')}
          className={`p-1 rounded hover:bg-slate-800 transition-colors ${
            feedback === 'like' ? 'text-emerald-400 bg-emerald-500/10' : 'text-slate-500 hover:text-slate-300'
          }`}
          title="Helpful"
        >
          <ThumbsUp className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setFeedback(feedback === 'dislike' ? null : 'dislike')}
          className={`p-1 rounded hover:bg-slate-800 transition-colors ${
            feedback === 'dislike' ? 'text-rose-400 bg-rose-500/10' : 'text-slate-500 hover:text-slate-300'
          }`}
          title="Not helpful"
        >
          <ThumbsDown className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
