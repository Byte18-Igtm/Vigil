import React, { useState } from 'react';
import { X, FolderGit2, Check, Sparkles, Plus, Folder } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function ProjectSelectorModal() {
  const { activeModal, setActiveModal, selectedProject, setSelectedProject, runAgentAnalysis } = useApp();
  const [folderInput, setFolderInput] = useState(selectedProject.path);
  const [bugInput, setBugInput] = useState('average() returns wrong result');

  if (activeModal !== 'selectProject') return null;

  const sampleProjects = [
    { name: 'MyWebApp', path: 'C:\\Projects\\MyWebApp', branch: 'main', framework: 'React + Express', files: 142 },
    { name: 'EcommerceBackend', path: 'C:\\Projects\\EcommerceBackend', branch: 'feature/stripe', framework: 'NestJS + PostgreSQL', files: 218 },
    { name: 'MobileApp-Client', path: 'C:\\Projects\\MobileApp-Client', branch: 'dev', framework: 'React Native + Expo', files: 96 },
  ];

  const handleSelect = (proj) => {
    setSelectedProject({
      name: proj.name,
      path: proj.path,
      branch: proj.branch,
      status: 'Session Active',
      framework: proj.framework,
      filesCount: proj.files,
      healthScore: 96
    });
    setActiveModal(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center space-x-2.5">
            <FolderGit2 className="w-5 h-5 text-indigo-400" />
            <h3 className="text-sm font-bold text-white">Select Workspace Project</h3>
          </div>
          <button
            onClick={() => setActiveModal(null)}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">
              Project Directory Path:
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={folderInput}
                onChange={(e) => setFolderInput(e.target.value)}
                placeholder="/absolute/path/to/repo"
                className="flex-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-100 focus:outline-none focus:border-indigo-500"
              />
              <button
                onClick={() => {
                  setSelectedProject(prev => ({ ...prev, path: folderInput }));
                  setActiveModal(null);
                  setTimeout(() => runAgentAnalysis(bugInput), 50);
                }}
                className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition-colors"
              >
                Analyse
              </button>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">
              Bug Report:
            </label>
            <input
              type="text"
              value={bugInput}
              onChange={(e) => setBugInput(e.target.value)}
              placeholder="Describe the bug…"
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
              Recent Projects:
            </span>
            <div className="space-y-2">
              {sampleProjects.map((p) => (
                <div
                  key={p.path}
                  onClick={() => handleSelect(p)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between group ${
                    selectedProject.path === p.path
                      ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                      : 'bg-slate-950/60 border-slate-800 hover:bg-slate-800/60 hover:border-slate-700 text-slate-300'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <Folder className="w-5 h-5 text-indigo-400" />
                    <div>
                      <div className="text-xs font-bold text-slate-100 flex items-center gap-2">
                        {p.name}
                        <span className="text-[10px] text-slate-400 font-mono font-normal">({p.branch})</span>
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 mt-0.5">{p.path}</div>
                    </div>
                  </div>
                  {selectedProject.path === p.path && (
                    <span className="p-1 rounded-full bg-emerald-500/20 text-emerald-400">
                      <Check className="w-3.5 h-3.5" />
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-800 bg-slate-950 flex justify-end">
          <button
            onClick={() => setActiveModal(null)}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
