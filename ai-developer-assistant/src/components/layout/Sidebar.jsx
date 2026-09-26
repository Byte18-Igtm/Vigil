import React from 'react';
import { 
  Home, 
  Folder, 
  MessageSquare, 
  Mic, 
  Settings, 
  LogOut, 
  Sparkles, 
  Cpu, 
  Code2, 
  CheckCircle2,
  Sliders
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function Sidebar() {
  const { activeTab, setActiveTab, selectedProject } = useApp();

  const navItems = [
    { id: 'dashboard', label: 'Home', icon: Home },
    { id: 'project', label: 'Project', icon: Folder, badge: 'Active' },
    { id: 'chat', label: 'Chat', icon: MessageSquare, badge: 'Live' },
    { id: 'voice', label: 'Voice', icon: Mic },
    { id: 'agents', label: 'Agents Studio', icon: Cpu },
    { id: 'ide', label: 'IDE Companion', icon: Code2 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-950/90 border-r border-slate-800/80 flex flex-col justify-between shrink-0 select-none">
      {/* Brand Header */}
      <div>
        <div className="p-4 border-b border-slate-800/70 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 ring-1 ring-indigo-400/30">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
                DevAssist <span className="text-xs px-1.5 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">AI</span>
              </h1>
              <p className="text-[11px] text-slate-400 font-medium">Multi-Agent Assistant</p>
            </div>
          </div>
        </div>

        {/* Current Active Workspace Indicator */}
        <div className="px-3 pt-3">
          <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-2 truncate">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
              <span className="text-xs font-mono text-slate-300 truncate">{selectedProject.name}</span>
            </div>
            <span className="text-[10px] text-emerald-400 font-medium bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
              Active
            </span>
          </div>
        </div>

        {/* Navigation items */}
        <nav className="p-3 space-y-1 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 font-semibold'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 transition-transform group-hover:scale-110 ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && !isActive && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 group-hover:bg-slate-700">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* User profile & footer */}
      <div className="p-3 border-t border-slate-800/80 space-y-2">
        <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50 hover:bg-slate-900 border border-slate-800/60 transition-colors">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-rose-500 to-amber-500 flex items-center justify-center font-bold text-xs text-white ring-2 ring-slate-800">
                AJ
              </div>
              <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-slate-900"></span>
            </div>
            <div className="text-left">
              <div className="text-xs font-semibold text-slate-200 leading-tight">Alex Johnson</div>
              <div className="text-[11px] text-slate-400 truncate max-w-[110px]">alex@company.com</div>
            </div>
          </div>
          <button 
            title="Log out" 
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-md transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
