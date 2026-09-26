import React from 'react';
import { 
  Layers, 
  Zap, 
  Brain, 
  Volume2, 
  ShieldCheck, 
  CheckCircle2, 
  Sparkles 
} from 'lucide-react';
import { KEY_FEATURES } from '../../data/mockData';

const iconMap = {
  Layers,
  Zap,
  Brain,
  Mic: Volume2,
  ShieldCheck
};

export default function KeyFeaturesCard() {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 sm:p-5 shadow-sm flex flex-col justify-between space-y-4">
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Key Features
          </h3>
          <span className="text-[10px] text-indigo-400 font-medium bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20">
            Autonomous Core
          </span>
        </div>

        <div className="space-y-2.5">
          {KEY_FEATURES.map((feat, idx) => {
            const Icon = iconMap[feat.icon] || Sparkles;
            return (
              <div key={idx} className="flex items-start space-x-2.5 group">
                <div className="p-1 rounded-md bg-indigo-500/10 text-indigo-400 shrink-0 mt-0.5 group-hover:bg-indigo-500/20 transition-colors">
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-200 group-hover:text-indigo-300 transition-colors">
                    {feat.title}
                  </div>
                  <div className="text-[11px] text-slate-400 leading-tight">
                    ({feat.subtitle})
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* The Result Callout Box */}
      <div className="p-3 rounded-xl bg-gradient-to-r from-emerald-950/40 via-emerald-900/20 to-indigo-950/30 border border-emerald-500/30">
        <div className="flex items-center space-x-2 text-emerald-400 mb-1">
          <CheckCircle2 className="w-4 h-4 fill-emerald-500/20 text-emerald-400" />
          <span className="text-xs font-bold uppercase tracking-wide text-emerald-300">The result?</span>
        </div>
        <p className="text-[11px] text-slate-300 leading-relaxed font-medium">
          Faster development, fewer errors, less manual effort, and a healthier codebase.
        </p>
      </div>
    </div>
  );
}
