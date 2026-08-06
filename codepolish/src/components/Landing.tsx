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
      <motion.div 
        initial={{ opacity: 0, x: -40 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="flex-1 w-full"
      >
        <div className="inline-flex items-center gap-2 bg-[#1A1D23]/80 border border-[#2A2E37] px-3 py-1.5 rounded-full text-xs font-medium text-secondary-dark mb-8">
          <div className="w-2 h-2 rounded-full bg-primary-brand shadow-[0_0_8px_rgba(45,212,167,0.8)]" />
          Static analysis · no code leaves your machine
        </div>

        <h1 className="text-5xl lg:text-7xl font-bold mb-6 tracking-tight text-primary-dark">
          Grammarly for <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-brand to-blue-500">code.</span>
        </h1>

        <p className="text-lg lg:text-xl text-secondary-dark mb-12 max-w-lg leading-relaxed">
          Drop a vibe-coded repository into the scanner. CodePolish parses every file and shows, calmly and concretely, what stands between it and production.
        </p>

        {/* Mock Code Window */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          className="bg-[#0D0F12] border border-[#2A2E37] rounded-xl overflow-hidden shadow-2xl relative"
        >
          {/* Mac window dots */}
          <div className="flex items-center gap-2 px-4 py-3 bg-[#13151A] border-b border-[#2A2E37]">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-[#FF5F56]" />
              <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
              <div className="w-3 h-3 rounded-full bg-[#27C93F]" />
            </div>
            <span className="ml-4 text-xs font-mono text-secondary-dark">app.py</span>
          </div>

          <div className="p-5 font-mono text-sm overflow-x-auto relative">
            <div className="flex">
              <div className="text-secondary-dark/50 select-none text-right pr-4 border-r border-[#2A2E37]/50 mr-4 space-y-1.5">
                <div>1</div><div>2</div><div>3</div><div>4</div>
              </div>
              <div className="text-primary-dark/80 space-y-1.5 whitespace-pre">
                <div><span className="text-purple-400">@app</span><span className="text-blue-400">.get</span><span className="text-secondary-dark">("/users")</span></div>
                <div><span className="text-primary-brand">def</span> <span className="text-blue-400">users</span>():</div>
                <div className="relative">
                  <span>    rows = db.execute(f"SELECT * FROM users")</span>
                  {/* Wavy underline */}
                  <div className="absolute left-4 -bottom-1 w-[330px] h-1 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2IiBoZWlnaHQ9IjMiPjxwYXRoIGQ9Ik0wLDFDMiwyLDQsMiw2LDFWM0gweiIgZmlsbD0iI2VmNDQ0NCIvPjwvc3ZnPg==')] repeat-x" />
                  <span className="absolute left-[360px] top-0 bg-[#2A0F12] border border-status-security/30 text-status-security text-[10px] px-2 py-0.5 rounded flex items-center gap-1 font-sans z-10 shadow-lg">
                    <Lock size={10} /> Unparameterised query
                  </span>
                </div>
                <div className="relative">
                  <span>    <span className="text-purple-400">return</span> jsonify(rows)</span>
                  {/* Wavy underline */}
                  <div className="absolute left-4 -bottom-1 w-[190px] h-1 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2IiBoZWlnaHQ9IjMiPjxwYXRoIGQ9Ik0wLDFDMiwyLDQsMiw2LDFWM0gweiIgZmlsbD0iI2Y1OWUwYiIvPjwvc3ZnPg==')] repeat-x" />
                  <span className="absolute left-[220px] top-0 bg-[#2A1D0F] border border-status-structure/30 text-status-structure text-[10px] px-2 py-0.5 rounded flex items-center gap-1 font-sans z-10 shadow-lg">
                    Missing error handling
                  </span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Feature Pills */}
        <div className="flex flex-wrap gap-3 mt-8">
          <span className="px-3 py-1.5 rounded-full border border-primary-brand/30 bg-primary-brand/10 text-primary-brand text-xs font-medium">Structure analysis</span>
          <span className="px-3 py-1.5 rounded-full border border-[#2A2E37] bg-[#1A1D23] text-secondary-dark text-xs font-medium">Security · Phase 2</span>
          <span className="px-3 py-1.5 rounded-full border border-[#2A2E37] bg-[#1A1D23] text-secondary-dark text-xs font-medium">Auto-fix · Phase 4</span>
          <span className="px-3 py-1.5 rounded-full border border-[#2A2E37] bg-[#1A1D23] text-secondary-dark text-xs font-medium">LLM checks · Phase 5</span>
        </div>
      </motion.div>


      {/* Right Column: Upload Card */}
      <motion.div 
        initial={{ opacity: 0, x: 40 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, ease: "easeOut", delay: 0.1 }}
        className="w-full max-w-md lg:w-[480px] shrink-0"
      >
        <div className="relative group">
          {/* Glow effect */}
          <div className="absolute -inset-[1px] bg-gradient-to-r from-primary-brand/40 to-blue-500/40 rounded-2xl blur-sm opacity-50 group-hover:opacity-100 transition duration-1000" />
          
          <div className="relative bg-[#13151A] border border-[#2A2E37] rounded-2xl p-6 shadow-2xl">
            
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
                  className={`flex-1 p-3 rounded-xl border text-left transition-all relative overflow-hidden ${
                    tab.active 
                      ? 'border-primary-brand/50 bg-primary-brand/5 shadow-[0_0_15px_rgba(45,212,167,0.1)]' 
                      : 'border-[#2A2E37] bg-[#1A1D23]/50 hover:bg-[#1A1D23] hover:border-border-dark opacity-80'
                  } ${tab.disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <tab.icon size={16} className={`mb-2 ${tab.active ? 'text-primary-brand' : 'text-secondary-dark'}`} />
                  <div className={`text-sm font-semibold mb-1 ${tab.active ? 'text-primary-dark' : 'text-secondary-dark'}`}>{tab.label}</div>
                  <div className="text-[10px] text-secondary-dark font-mono">{tab.sub}</div>
                </button>
              ))}
            </div>

            {/* Content Area */}
            <div className="bg-[#1A1D23] border border-[#2A2E37] rounded-xl p-5 mb-6">
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
                      className="w-full bg-[#0D0F12] border border-[#2A2E37] rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary-brand/50 focus:shadow-[0_0_10px_rgba(45,212,167,0.1)] transition-all placeholder:text-secondary-dark/50 mb-4"
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
                    <label className="w-full flex flex-col items-center justify-center py-6 border-2 border-dashed border-[#2A2E37] rounded-lg hover:border-primary-brand/30 hover:bg-primary-brand/5 transition-colors cursor-pointer">
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
                      <FileArchive size={24} className={selectedFile ? "text-primary-brand mb-2" : "text-secondary-dark mb-2"} />
                      <div className="text-sm font-medium text-primary-dark">
                        {selectedFile ? selectedFile.name : 'Click to browse'}
                      </div>
                      <div className="text-xs text-secondary-dark mt-1">or drag and drop a .zip</div>
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
                  ? 'bg-primary-brand text-[#0D0F12] hover:bg-primary-brand/90 shadow-[0_0_20px_rgba(45,212,167,0.3)] hover:shadow-[0_0_30px_rgba(45,212,167,0.5)]'
                  : 'bg-[#2A2E37] text-secondary-dark cursor-not-allowed'
              }`}
            >
              {isAnalyzeEnabled ? 'Analyze Project' : 'Waiting for a project...'}
              {isAnalyzeEnabled && <ChevronRight size={16} />}
            </button>
            
            <p className="text-[11px] text-secondary-dark mt-4 text-center">
              Phase 1 scores structure. Security and error handling arrive in Phase 2.
            </p>

          </div>
        </div>
      </motion.div>
      
    </div>
  );
};
