import React from 'react';
import { 
  UserCheck, 
  FolderGit2, 
  Eye, 
  Cpu, 
  Brain, 
  MessageSquare, 
  User, 
  ArrowRight 
} from 'lucide-react';

export default function EndToEndWorkflowPipeline() {
  const steps = [
    { label: 'Login & Consent', icon: UserCheck, color: 'text-blue-400 bg-blue-500/10 border-blue-500/30' },
    { label: 'Select Project', icon: FolderGit2, color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30' },
    { label: 'Context Agent', icon: Eye, color: 'text-sky-400 bg-sky-500/10 border-sky-500/30' },
    { 
      label: 'Parallel Agents', 
      sublabel: 'Debugging • Testing • Maintenance', 
      icon: Cpu, 
      color: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
      isHighlight: true 
    },
    { label: 'Supervisor', icon: Brain, color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30' },
    { label: 'Chat / Voice', icon: MessageSquare, color: 'text-violet-400 bg-violet-500/10 border-violet-500/30' },
    { label: 'Developer', icon: User, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' }
  ];

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 sm:p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
          Example Workflow — End to End
        </h3>
        <span className="text-[10px] text-slate-400 font-mono">Autonomous Execution Pipeline</span>
      </div>

      <div className="flex flex-wrap md:flex-nowrap items-center justify-between gap-2 overflow-x-auto pb-2">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isLast = idx === steps.length - 1;

          return (
            <React.Fragment key={idx}>
              <div className="flex flex-col items-center text-center min-w-[85px] sm:min-w-[105px] group">
                <div className={`w-10 h-10 rounded-full border flex items-center justify-center transition-all duration-200 group-hover:scale-110 shadow-sm ${step.color} ${step.isHighlight ? 'ring-2 ring-purple-500/30' : ''}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <span className="text-[11px] font-bold text-slate-200 mt-2 leading-tight">
                  {step.label}
                </span>
                {step.sublabel && (
                  <span className="text-[9px] text-purple-300 font-medium mt-0.5 leading-none">
                    {step.sublabel}
                  </span>
                )}
              </div>

              {!isLast && (
                <div className="hidden md:flex text-slate-600 shrink-0">
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
