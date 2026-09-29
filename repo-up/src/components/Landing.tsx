import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileArchive, GitBranch, FileCode2, ChevronRight, Lock } from 'lucide-react';

interface LandingProps {
  onAnalyze: (file?: File) => void;
}

export const Landing: React.FC<LandingProps> = ({ onAnalyze }) => {
  const [activeTab, setActiveTab] = useState<'zip' | 'github' | 'paste'>('zip');
  const [githubUrl, setGithubUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const isAnalyzeEnabled = (activeTab === 'github' && githubUrl.length > 5) || (activeTab === 'zip' && selectedFile !== null);

  return (
    <div className="w-full max-w-7xl mx-auto px-4 lg:px-8 py-12 flex flex-col lg:flex-row items-center gap-16 relative z-10">
      
      {/* Left Column: Copy & Mockup */}
      <div className="flex-1 w-full flex flex-col items-start">
        {/* Unified Glass Text Panel */}
        <div className="hover-glass rounded-2xl p-8 md:p-10 mb-8 w-full max-w-[680px]">
          <h1 className="text-5xl lg:text-6xl font-bold mb-6 tracking-tight text-white font-display leading-tight">
            Repo-Up
          </h1>

          <p className="text-base lg:text-lg text-secondary-dark max-w-[480px] leading-[1.6]">
            Code doesn't fail in isolation — it fails in connections. Repo-Up maps every file, every call, every dependency, and tells you exactly where the structure gives way.
          </p>
        </div>

        {/* Mock Code Window */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          className="hover-glass rounded-2xl w-full max-w-[680px] mb-8 relative animate-none group/code"
        >
          {/* Mac window dots */}
          <div className="flex items-center gap-2 px-4 py-3 border-b border-transparent group-hover/code:border-white/5 transition-colors duration-300">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-[#FF5F56]" />
              <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
              <div className="w-3 h-3 rounded-full bg-[#27C93F]" />
            </div>
            <span className="ml-4 text-xs font-mono text-secondary-dark">app.py</span>
          </div>

          <div className="p-5 font-mono text-sm relative">
            <div className="flex">
              <div className="text-secondary-dark/50 select-none text-right pr-4 border-r border-[#2A2E37]/50 mr-4 space-y-1.5 shrink-0">
                <div className="py-[1px]">1</div><div className="py-[1px]">2</div><div className="py-[1px]">3</div><div className="py-[1px]">4</div>
              </div>
              <div className="text-primary-dark/80 space-y-1.5 w-full">
                <div className="py-[1px] whitespace-pre"><span className="text-purple-400">@app</span><span className="text-blue-400">.get</span><span className="text-secondary-dark">("/users")</span></div>
                <div className="py-[1px] whitespace-pre"><span className="text-[#6D5EF0] font-medium">def</span> <span className="text-blue-400">users</span>():</div>
                <div className="flex items-center justify-between gap-2 overflow-hidden py-[1px]">
                  <div className="relative shrink-0 whitespace-pre">
                    <span>    rows = db.execute(f"SELECT * FROM users")</span>
                    {/* Wavy underline */}
                    <div className="absolute left-4 -bottom-1 w-[330px] h-1 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2IiBoZWlnaHQ9IjMiPjxwYXRoIGQ9Ik0wLDFDMiwyLDQsMiw2LDFWM0gweiIgZmlsbD0iI2VmNDQ0NCIvPjwvc3ZnPg==')] repeat-x" />
                  </div>
                  <span className="bg-[#2A0F12] border border-status-security/30 text-status-security text-[10px] px-2 py-0.5 rounded flex items-center gap-1 font-sans z-10 shadow-lg shrink min-w-0">
                    <Lock size={10} className="shrink-0" /> <span className="truncate">Unparameterised query</span>
                  </span>
                </div>
                <div className="flex items-center justify-between gap-2 overflow-hidden py-[1px]">
                  <div className="relative shrink-0 whitespace-pre">
                    <span>    <span className="text-purple-400">return</span> jsonify(rows)</span>
                    {/* Wavy underline */}
                    <div className="absolute left-4 -bottom-1 w-[190px] h-1 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2IiBoZWlnaHQ9IjMiPjxwYXRoIGQ9Ik0wLDFDMiwyLDQsMiw2LDFWM0gweiIgZmlsbD0iI2Y1OWUwYiIvPjwvc3ZnPg==')] repeat-x" />
                  </div>
                  <span className="bg-[#2A1D0F] border border-status-structure/30 text-status-structure text-[10px] px-2 py-0.5 rounded flex items-center gap-1 font-sans z-10 shadow-lg shrink min-w-0">
                    <span className="truncate">Missing error handling</span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>


      </div>


      {/* Right Column: Upload Card */}
      <motion.div 
        initial={{ opacity: 0, x: 40 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, ease: "easeOut", delay: 0.1 }}
        className="w-full max-w-md lg:w-[480px] shrink-0"
      >
        <div className="relative group/upload rounded-2xl p-[1px]">
          {/* Gradient border wrapper */}
          <div className="absolute inset-0 bg-gradient-to-br from-[#6D5EF0]/40 to-blue-500/40 opacity-70 rounded-2xl group-hover/upload:from-[#6D5EF0] group-hover/upload:to-blue-500 group-hover/upload:opacity-100 transition-all duration-500" />
          
          <div className="bg-[#0b0c10]/55 backdrop-blur-[16px] rounded-2xl p-6 relative z-10 h-full w-full group-hover/upload:shadow-[0_8px_32px_rgba(109,94,240,0.25)] transition-shadow duration-300">
            
            {/* Tabs */}
            <div className="flex gap-2 mb-8">
              {[
                { id: 'zip', icon: FileArchive, label: 'Upload ZIP', sub: '.zip · 50 MB', active: activeTab === 'zip' },
                { id: 'github', icon: GitBranch, label: 'GitHub repo', sub: 'public URL', active: activeTab === 'github' },
                { id: 'paste', icon: FileCode2, label: 'Paste code', sub: 'Coming soon', active: false, disabled: true },
              ].map((tab) => (
                <button
                  key={tab.id}
                  disabled={tab.disabled}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex-1 p-3 rounded-xl border border-transparent text-left transition-all relative overflow-hidden ${
                    tab.active 
                      ? 'bg-gradient-to-br from-[#6D5EF0]/20 to-blue-500/20 shadow-[0_0_15px_rgba(109,94,240,0.2)]' 
                      : 'bg-white/5 hover:bg-white/10 hover:border-white/10 opacity-80'
                  } ${tab.disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <tab.icon size={16} className={`mb-2 ${tab.active ? 'text-[#6D5EF0]' : 'text-secondary-dark'}`} />
                  <div className={`text-sm font-semibold mb-1 ${tab.active ? 'text-primary-dark' : 'text-secondary-dark'}`}>{tab.label}</div>
                  <div className="text-[10px] text-secondary-dark font-mono">{tab.sub}</div>
                </button>
              ))}
            </div>

            {/* Content Area */}
            <div className="bg-black/20 border border-white/5 rounded-xl p-5 mb-6">
              <AnimatePresence mode="wait">
                {activeTab === 'github' && (
                  <motion.div
                    key="github"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    <label className="block text-xs font-mono text-secondary-dark mb-2">Repository URL</label>
                    <input 
                      type="text"
                      placeholder="https://github.com/username/my-ai-project"
                      value={githubUrl}
                      onChange={(e) => setGithubUrl(e.target.value)}
                      className="w-full bg-black/45 border border-white/5 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-[#6D5EF0]/50 focus:shadow-[0_0_10px_rgba(109,94,240,0.15)] transition-all placeholder:text-secondary-dark/50 mb-4"
                    />
                    <p className="text-xs text-secondary-dark leading-relaxed">
                      Public repositories only in this prototype — nothing is cloned or stored.
                    </p>
                  </motion.div>
                )}
                {activeTab === 'zip' && (
                  <motion.div
                    key="zip"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="flex flex-col items-center justify-center text-center relative"
                  >
                    <label className="w-full flex flex-col items-center justify-center py-6 border-2 border-dashed border-[#6D5EF0]/40 rounded-lg hover:border-transparent transition-all cursor-pointer relative group/drop z-0">
                      {/* Gradient border on hover */}
                      <div className="absolute -inset-[2px] rounded-lg bg-gradient-to-br from-[#6D5EF0] to-blue-500 opacity-0 group-hover/drop:opacity-100 -z-10 transition-opacity" />
                      {/* Inner background on hover */}
                      <div className="absolute inset-0 rounded-lg bg-[#0b0c10] opacity-0 group-hover/drop:opacity-100 -z-10 transition-opacity" />
                      <div className="absolute inset-0 rounded-lg bg-gradient-to-br from-[#6D5EF0]/15 to-blue-500/15 opacity-0 group-hover/drop:opacity-100 -z-10 transition-opacity" />
                      
                      <FileArchive size={24} className={selectedFile ? "text-[#6D5EF0] mb-2 relative z-10" : "text-secondary-dark mb-2 relative z-10"} />
                      <div className="text-sm font-medium text-primary-dark relative z-10">
                        {selectedFile ? selectedFile.name : 'Click to browse'}
                      </div>
                      <div className="text-xs text-secondary-dark mt-1 relative z-10">or drag and drop a .zip</div>
                      <input 
                        type="file" 
                        accept=".zip" 
                        className="hidden" 
                        onChange={(e) => {
                          if (e.target.files && e.target.files.length > 0) {
                            setSelectedFile(e.target.files[0]);
                          }
                        }}
                      />
                    </label>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Action Button */}
            <button
              onClick={() => onAnalyze(selectedFile || undefined)}
              disabled={!isAnalyzeEnabled}
              className={`w-full py-4 rounded-xl font-semibold text-sm transition-all flex items-center justify-center gap-2 ${
                isAnalyzeEnabled
                  ? 'bg-[#6D5EF0] text-white hover:bg-[#6D5EF0]/95 shadow-[0_0_20px_rgba(109,94,240,0.3)] hover:shadow-[0_0_30px_rgba(109,94,240,0.5)]'
                  : 'bg-[#2A2E37]/50 text-secondary-dark cursor-not-allowed border border-white/5'
              }`}
            >
              {isAnalyzeEnabled ? 'Analyze Project' : 'Waiting for a project...'}
              {isAnalyzeEnabled && <ChevronRight size={16} />}
            </button>
            
          </div>
        </div>
      </motion.div>
      
    </div>
  );
};
