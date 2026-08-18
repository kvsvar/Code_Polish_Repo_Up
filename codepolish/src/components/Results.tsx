import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Code2, Home, Network, AlertTriangle, Archive, Clock, 
  Download, Moon, Sun, Lock, ChevronRight, File
} from 'lucide-react';
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer 
} from 'recharts';
import { GraphView } from './GraphView';

interface Rubric {
  final_score: number;
  structural_score: number;
  metrics_score: number;
  category_breakdown: {
    modularity: number;
    analysability: number;
    modifiability: number;
    testability: number;
  };
  metric_ratings: {
    cof: "good" | "regular" | "bad";
    afferent_couplings: "good" | "regular" | "bad";
    public_fields: "good" | "regular" | "bad";
    public_methods: "good" | "regular" | "bad";
    dit: "good" | "regular" | "bad";
    lcom: "good" | "regular" | "bad";
  };
}

interface ResultsProps {
  data: any;
  onReset: () => void;
}

export const Results: React.FC<ResultsProps> = ({ data, onReset }) => {
  const [showGraph, setShowGraph] = useState(false);
  // Ensure data exists, fallback if undefined
  const d = data || {};
  const rubric: Rubric | undefined = d.rubric;
  const score = rubric?.final_score ?? (d.score ?? 0);
  const structuralScore = rubric?.structural_score ?? (d.score ?? 0);
  const metricsScore = rubric?.metrics_score ?? 0;
  
  const language = d.language || 'Unknown';
  const framework = d.framework || 'Unknown';
  const filesCount = d.files || 0;
  const issues = d.issues || [];
  const tree = d.tree || [];

  const radarData = rubric ? [
    { subject: 'Modularity', A: rubric.category_breakdown.modularity, fullMark: 100 },
    { subject: 'Analysability', A: rubric.category_breakdown.analysability, fullMark: 100 },
    { subject: 'Modifiability', A: rubric.category_breakdown.modifiability, fullMark: 100 },
    { subject: 'Testability', A: rubric.category_breakdown.testability, fullMark: 100 },
    { subject: 'Structure', A: rubric.structural_score, fullMark: 100 },
  ] : [
    { subject: 'Structure', A: score, fullMark: 100 },
    { subject: 'Security', A: 20, fullMark: 100 },
    { subject: 'Errors', A: 30, fullMark: 100 },
    { subject: 'Style', A: 45, fullMark: 100 },
    { subject: 'Docs', A: 10, fullMark: 100 },
  ];

  const getScoreColor = (val: number) => {
    if (val >= 80) return { text: 'text-status-verified', bg: 'bg-status-verified', border: 'border-status-verified' };
    if (val >= 50) return { text: 'text-status-structure', bg: 'bg-status-structure', border: 'border-status-structure' };
    return { text: 'text-status-security', bg: 'bg-status-security', border: 'border-status-security' };
  };

  const getRatingStyle = (rating: string) => {
    switch (rating) {
      case 'good': return 'bg-status-verified/20 text-status-verified border-status-verified/30';
      case 'regular': return 'bg-status-structure/20 text-status-structure border-status-structure/30';
      case 'bad': return 'bg-status-security/20 text-status-security border-status-security/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getSeverityColor = (sev: string) => {
    switch (sev?.toLowerCase()) {
      case 'high': return { color: 'text-status-security', border: 'border-l-status-security' };
      case 'medium': return { color: 'text-status-structure', border: 'border-l-status-structure' };
      default: return { color: 'text-status-style', border: 'border-l-status-style' };
    }
  };

  const handleDownloadReport = () => {
    const report = {
      time: new Date().toISOString().split('T')[0],
      language,
      framework,
      score,
      issues
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'report.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const scrollToSection = (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="flex h-full w-full bg-[#0B0C10] text-primary-dark overflow-hidden font-sans">
      
      {/* SIDEBAR */}
      <div className="w-64 border-r border-[#2A2E37] bg-[#0F1115] p-4 flex flex-col shrink-0 relative z-20 overflow-y-auto overflow-x-hidden">
        <div className="flex items-center gap-2 mb-8 px-2 cursor-pointer" onClick={onReset}>
          <div className="text-primary-brand">
            <Code2 size={24} />
          </div>
          <span className="font-bold text-xl tracking-tight text-white">CodePolish</span>
        </div>

        <nav className="space-y-1 mb-8">
          <a href="#overview" onClick={(e) => scrollToSection(e, 'overview')} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-secondary-dark hover:text-primary-dark hover:bg-[#1A1D23] transition-colors focus:bg-primary-brand/10 focus:text-primary-brand">
            <Home size={18} /> Overview
          </a>
          <a href="#structure" onClick={(e) => scrollToSection(e, 'structure')} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-secondary-dark hover:text-primary-dark hover:bg-[#1A1D23] transition-colors focus:bg-primary-brand/10 focus:text-primary-brand">
            <Network size={18} /> Structure
          </a>
          <a href="#issues" onClick={(e) => scrollToSection(e, 'issues')} className="flex items-center justify-between px-3 py-2.5 rounded-lg text-secondary-dark hover:text-primary-dark hover:bg-[#1A1D23] transition-colors focus:bg-primary-brand/10 focus:text-primary-brand">
            <div className="flex items-center gap-3"><AlertTriangle size={18} /> Issues</div>
            <span className="bg-status-security/20 text-status-security text-xs px-2 py-0.5 rounded-full font-bold">{issues.length}</span>
          </a>
          <a href="#files" onClick={(e) => scrollToSection(e, 'files')} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-secondary-dark hover:text-primary-dark hover:bg-[#1A1D23] transition-colors focus:bg-primary-brand/10 focus:text-primary-brand">
            <Archive size={18} /> Files
          </a>
          <a href="#timeline" onClick={(e) => scrollToSection(e, 'timeline')} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-secondary-dark hover:text-primary-dark hover:bg-[#1A1D23] transition-colors focus:bg-primary-brand/10 focus:text-primary-brand">
            <Clock size={18} /> Timeline
          </a>
        </nav>

        <div className="mt-4 px-3 mb-auto">
          <div className="text-[10px] font-bold text-secondary-dark tracking-wider mb-3 uppercase">Project</div>
          <div className="flex items-center gap-2 mb-3">
            <span className="font-medium text-sm">Uploaded Project</span>
            <span className="bg-[#1A1D23] border border-[#2A2E37] text-purple-400 text-[10px] px-1.5 py-0.5 rounded">{language}</span>
          </div>
          <div className="space-y-2 text-xs text-secondary-dark">
            <div className="flex items-center gap-2"><File size={12} /> {filesCount} Files</div>
            <div className="flex items-center gap-2"><Clock size={12} /> Analyzed just now</div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-8 bg-gradient-to-b from-[#1A1D23] to-[#0F1115] border border-[#2A2E37] rounded-xl p-4 text-center relative overflow-hidden group">
          <div className="absolute inset-0 bg-primary-brand/5 group-hover:bg-primary-brand/10 transition-colors" />
          <h4 className="font-bold text-sm mb-2 text-white relative z-10">Make it Production Ready ✨</h4>
          <p className="text-xs text-secondary-dark mb-4 relative z-10">Apply fixes and run in sandbox (Phase 4)</p>
          <button className="w-full py-2 bg-[#1A1D23] border border-[#2A2E37] rounded-lg text-xs font-medium text-secondary-dark flex items-center justify-center gap-2 cursor-not-allowed relative z-10 hover:border-primary-brand/30">
            <Lock size={12} /> Coming Soon
          </button>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
        
        {/* Header */}
        <header className="h-16 border-b border-[#2A2E37] bg-[#0F1115]/80 backdrop-blur-sm flex items-center justify-between px-8 shrink-0">
          <div className="flex items-center gap-2 text-sm text-secondary-dark">
            <span>Projects</span> <ChevronRight size={14} /> <span className="text-primary-dark font-medium">Results</span>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setShowGraph(!showGraph)}
              className={`flex items-center gap-2 text-xs font-medium transition-colors px-3 py-1.5 border rounded-lg ${showGraph ? 'bg-[#6D5EF0] text-white border-[#6D5EF0]' : 'text-secondary-dark border-[#2A2E37] hover:border-[#6D5EF0]/30 hover:text-primary-dark'}`}
            >
              <Network size={14} /> {showGraph ? 'Hide Graph' : 'View Graph'}
            </button>
            <button 
              onClick={handleDownloadReport}
              className="flex items-center gap-2 text-xs font-medium text-secondary-dark hover:text-primary-dark transition-colors px-3 py-1.5 border border-[#2A2E37] rounded-lg hover:border-primary-dark/30"
            >
              <Download size={14} /> Export Report
            </button>
            <div className="flex items-center gap-2 border-l border-[#2A2E37] pl-4">
              <button className="text-secondary-dark hover:text-primary-dark transition-colors"><Sun size={16} /></button>
              <button className="text-secondary-dark hover:text-primary-dark transition-colors"><Moon size={16} /></button>
            </div>
            <div className="w-8 h-8 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center text-xs font-bold border border-purple-500/30 ml-2">
              AK
            </div>
          </div>
        </header>

        {/* Scrollable Dashboard */}
        <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6">
          
          <AnimatePresence>
            {showGraph && d.graph && (
              <GraphView 
                nodes={d.graph.nodes} 
                edges={d.graph.edges} 
                onClose={() => setShowGraph(false)} 
              />
            )}
          </AnimatePresence>
          
          <motion.div 
            id="overview"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col xl:flex-row gap-6"
          >
            {/* BIG SCORE CARD */}
            <div className="flex-1 bg-[#13151A] border border-[#2A2E37] rounded-2xl p-8 relative overflow-hidden flex items-center gap-8 shadow-2xl min-h-[240px]">
              <div className="absolute inset-0 bg-gradient-to-r from-primary-brand/5 to-transparent pointer-events-none" />
              
              {/* Circular Progress */}
              <div className="relative w-40 h-40 shrink-0">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="none" stroke="#2A2E37" strokeWidth="8" />
                  <circle cx="50" cy="50" r="45" fill="none" stroke="#6D5EF0" strokeWidth="8" strokeDasharray="282.7" strokeDashoffset={282.7 - (282.7 * score) / 100} className="drop-shadow-[0_0_8px_rgba(109,94,240,0.8)]" />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-5xl font-black text-white">{score}</span>
                  <span className="text-xs text-secondary-dark font-medium">/100</span>
                </div>
              </div>

              {/* Info */}
              <div className="flex-1">
                <div className="text-[10px] font-bold text-secondary-dark tracking-wider mb-2 uppercase">Project Readiness Score</div>
                <h2 className={`text-3xl font-bold mb-3 ${getScoreColor(score).text}`}>
                  {score >= 90 ? 'Excellent' : score >= 70 ? 'Good' : 'Needs Improvement'}
                </h2>
                
                {rubric && (
                  <div className="text-xs text-secondary-dark mb-4 flex items-center gap-2">
                    <span className="bg-[#1A1D23] px-2 py-1 rounded border border-[#2A2E37]">Structure: {structuralScore}</span>
                    <span className="bg-[#1A1D23] px-2 py-1 rounded border border-[#2A2E37]">Metrics: {metricsScore}</span>
                  </div>
                )}
                
                <p className="text-sm text-secondary-dark mb-6 max-w-md leading-relaxed">
                  Your project works, but check the structural improvements to be production ready.
                </p>
                <div className="flex gap-3">
                  <span className="px-2.5 py-1 rounded bg-[#1A1D23] border border-[#2A2E37] text-xs text-secondary-dark flex items-center gap-1.5"><Code2 size={12}/> {language}</span>
                  <span className="px-2.5 py-1 rounded bg-[#1A1D23] border border-[#2A2E37] text-xs text-secondary-dark flex items-center gap-1.5"><Archive size={12}/> {framework}</span>
                </div>
              </div>

              {/* Radar Chart */}
              <div className="hidden md:block w-48 h-48 shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                    <PolarGrid stroke="#2A2E37" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
                    <Radar name="Score" dataKey="A" stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.4} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </motion.div>

          {/* CATEGORY ROW */}
          <motion.div 
            id="structure"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-2 md:grid-cols-5 gap-4"
          >
            {rubric ? (
              <>
                <div className="bg-[#13151A] border-2 border-primary-brand/30 rounded-xl p-4 shadow-[0_0_15px_rgba(109,94,240,0.15)] relative overflow-hidden">
                  <div className="flex items-center gap-2 mb-4 text-primary-brand font-medium">
                    <Network size={16} /> <span className="font-semibold text-sm text-white">Structure</span>
                  </div>
                  <div className="text-2xl font-bold text-white flex items-baseline gap-1 mb-3">
                    {rubric.structural_score} <span className="text-xs text-secondary-dark font-normal">/100</span>
                  </div>
                  <div className="h-1.5 w-full bg-[#2A2E37] rounded-full overflow-hidden">
                    <div className="h-full bg-primary-brand rounded-full" style={{ width: `${rubric.structural_score}%` }} />
                  </div>
                </div>

                {['Modularity', 'Analysability', 'Modifiability', 'Testability'].map((cat, idx) => {
                  const val = rubric.category_breakdown[cat.toLowerCase() as keyof typeof rubric.category_breakdown];
                  const color = getScoreColor(val);
                  return (
                    <div key={idx} className="bg-[#13151A] border border-[#2A2E37] rounded-xl p-4 relative overflow-hidden">
                      <div className={`flex items-center gap-2 mb-4 ${color.text}`}>
                        <Archive size={16} /> <span className="font-semibold text-sm text-white">{cat}</span>
                      </div>
                      <div className="text-2xl font-bold text-secondary-dark flex items-baseline gap-1 mb-3">
                        {val} <span className="text-xs font-normal">/100</span>
                      </div>
                      <div className="h-1.5 w-full bg-[#2A2E37] rounded-full overflow-hidden">
                         <div className={`h-full ${color.bg} rounded-full`} style={{ width: `${val}%` }} />
                      </div>
                    </div>
                  );
                })}
              </>
            ) : (
              <>
                <div className="bg-[#13151A] border-2 border-primary-brand/30 rounded-xl p-4 shadow-[0_0_15px_rgba(109,94,240,0.15)] relative overflow-hidden">
                  <div className="flex items-center gap-2 mb-4 text-primary-brand font-medium">
                    <Network size={16} /> <span className="font-semibold text-sm text-white">Structure</span>
                  </div>
                  <div className="text-2xl font-bold text-white flex items-baseline gap-1 mb-3">
                    {score} <span className="text-xs text-secondary-dark font-normal">/100</span>
                  </div>
                  <div className="h-1.5 w-full bg-[#2A2E37] rounded-full overflow-hidden">
                    <div className="h-full bg-primary-brand rounded-full" style={{ width: `${score}%` }} />
                  </div>
                </div>
                {/* Fallbacks if no rubric */}
                <div className="bg-[#13151A] border border-[#2A2E37] rounded-xl p-4 relative overflow-hidden opacity-60">
                  <div className="absolute right-2 top-2 bg-status-security/20 text-status-security text-[9px] px-1.5 py-0.5 rounded font-bold">Phase 2</div>
                  <div className="flex items-center gap-2 mb-4 text-status-security">
                    <Lock size={16} /> <span className="font-semibold text-sm text-white">Security</span>
                  </div>
                  <div className="text-2xl font-bold text-secondary-dark flex items-baseline gap-1 mb-3">
                    -- <span className="text-xs font-normal">/100</span>
                  </div>
                  <div className="h-1.5 w-full bg-[#2A2E37] rounded-full overflow-hidden" />
                </div>
              </>
            )}
          </motion.div>

          {/* METRIC RATINGS (Only if rubric exists) */}
          {rubric && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="bg-[#13151A] border border-[#2A2E37] rounded-2xl flex flex-col shadow-lg overflow-hidden"
            >
              <div className="p-5 border-b border-[#2A2E37] flex items-center justify-between bg-[#1A1D23]/50">
                <h3 className="font-bold flex items-center gap-2 text-white">
                  <Network size={16} className="text-primary-brand" /> 
                  Codebase Metrics Breakdown
                </h3>
              </div>
              <div className="p-5 overflow-x-auto">
                {rubric.metric_ratings.dit === null || rubric.metric_ratings.lcom === null ? (
                  <div className="mb-4 text-xs text-status-structure bg-status-structure/10 border border-status-structure/20 p-3 rounded-lg flex items-center gap-2">
                    <AlertTriangle size={14} /> Limited class-based structure detected — some OOP metrics (DIT, LCOM) are less applicable to this codebase.
                  </div>
                ) : null}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {[
                    { key: 'cof', label: 'Coupling Factor', tip: 'How interconnected your files are overall — lower means easier to change one thing without breaking others' },
                    { key: 'afferent_couplings', label: 'Afferent Couplings', tip: 'How many other files depend on this one — high values mean changes here ripple outward' },
                    { key: 'public_fields', label: 'Public Fields', tip: 'How much internal state is exposed directly — more exposure means easier to accidentally misuse' },
                    { key: 'public_methods', label: 'Public Methods', tip: 'How many responsibilities a class/module exposes — very high counts often mean it is doing too much' },
                    { key: 'dit', label: 'Depth of Inheritance', tip: 'How deep the class hierarchy goes — deep chains are harder to trace and reason about' },
                    { key: 'lcom', label: 'Cohesion (LCOM)', tip: 'Whether a class\'s methods actually work together — low cohesion means the class may need to be split' },
                  ].map((m) => {
                    const rating = rubric.metric_ratings[m.key as keyof typeof rubric.metric_ratings] || 'good';
                    return (
                      <div key={m.key} className="group relative bg-[#0D0F12] border border-[#2A2E37] p-4 rounded-xl flex items-center justify-between hover:border-[#6D5EF0]/50 transition-colors cursor-help">
                        <span className="text-sm font-semibold text-secondary-dark group-hover:text-primary-dark transition-colors">{m.label}</span>
                        <span className={`text-[10px] uppercase tracking-wider font-bold px-2.5 py-1 rounded-full border ${getRatingStyle(rating)}`}>
                          {rating}
                        </span>
                        {/* Tooltip */}
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-[#1A1D23] border border-[#2A2E37] text-xs text-primary-dark rounded shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 text-center pointer-events-none">
                          {m.tip}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          )}

          {/* TWO COLUMNS: Issues & Tree */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {/* Issues List */}
            <div id="issues" className="bg-[#13151A] border border-[#2A2E37] rounded-2xl flex flex-col shadow-lg overflow-hidden h-[400px]">
              <div className="p-5 border-b border-[#2A2E37] flex items-center justify-between bg-[#1A1D23]/50">
                <h3 className="font-bold flex items-center gap-2 text-white">
                  <AlertTriangle size={16} className="text-status-structure" /> 
                  Structural Issues
                </h3>
                <span className="text-xs bg-[#2A2E37] px-2 py-1 rounded text-secondary-dark font-medium">{issues.length} Issues Found</span>
              </div>
              <div className="p-5 flex-1 overflow-y-auto">
                <ul className="space-y-4">
                  {issues.length === 0 && (
                    <div className="text-center text-secondary-dark py-10 text-sm">No structural issues found!</div>
                  )}
                  {issues.map((issue: any, i: number) => {
                    const style = getSeverityColor(issue.severity);
                    return (
                      <li key={i} className={`flex items-center justify-between p-3 rounded-lg bg-[#0D0F12] border border-[#2A2E37] border-l-4 ${style.border}`}>
                        <div className="flex items-start gap-3">
                          <div className={`mt-0.5 ${style.color}`}><AlertTriangle size={14} /></div>
                          <div>
                            <div className="font-semibold text-sm text-primary-dark">{issue.title}</div>
                            <div className="text-xs text-secondary-dark mt-0.5">{issue.desc || issue.description}</div>
                          </div>
                        </div>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#1A1D23] border border-[#2A2E37] ${style.color}`}>
                          {issue.severity || 'Unknown'}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            </div>

            {/* Project Structure Tree */}
            <div id="files" className="bg-[#13151A] border border-[#2A2E37] rounded-2xl flex flex-col shadow-lg overflow-hidden h-[400px]">
              <div className="p-5 border-b border-[#2A2E37] flex items-center justify-between bg-[#1A1D23]/50">
                <h3 className="font-bold flex items-center gap-2 text-white">
                  <Network size={16} className="text-primary-brand" /> 
                  Project Structure
                </h3>
              </div>
              
              <div className="p-5 flex-1 font-mono text-xs overflow-auto bg-[#0D0F12] m-4 rounded-xl border border-[#2A2E37]">
                {tree.length === 0 && (
                  <div className="text-secondary-dark">No files detected.</div>
                )}
                {tree.map((node: string, i: number) => (
                  <div key={i} className="whitespace-pre text-secondary-dark hover:text-primary-brand transition-colors cursor-default">
                    {node}
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
          
          {/* TIMELINE */}
          <motion.div 
            id="timeline"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="w-full bg-[#13151A] border border-[#2A2E37] rounded-xl p-6 shadow-lg mb-8"
          >
            <div className="flex items-center gap-2 mb-6">
              <Clock size={16} className="text-primary-brand" /> 
              <h3 className="font-bold text-sm text-white">Analysis Timeline</h3>
            </div>
            
            <div className="flex items-start justify-between relative">
              <div className="absolute top-2 left-4 right-4 h-0.5 bg-[#2A2E37] -z-10" />
              <div className="absolute top-2 left-4 w-4/5 h-0.5 bg-primary-brand -z-10" />
              
              {[
                { label: 'Upload', sub: 'Completed', status: 'done' },
                { label: 'Detect Language', sub: language, status: 'done' },
                { label: 'Detect Framework', sub: framework, status: 'done' },
                { label: 'Parse with Tree-sitter', sub: `${filesCount} files parsed`, status: 'done' },
                { label: 'Analyze Structure', sub: `${issues.length} issues found`, status: 'done' },
                { label: 'Score Calculated', sub: `${score}/100`, status: 'current' },
              ].map((step, i) => (
                <div key={i} className="flex flex-col items-center">
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center mb-3 text-[10px] font-bold ${
                    step.status === 'done' ? 'bg-primary-brand text-white' : 
                    step.status === 'current' ? 'bg-[#05050A] border-2 border-primary-brand text-primary-brand' :
                    'bg-[#1A1D23] border-2 border-[#2A2E37] text-secondary-dark'
                  }`}>
                    {step.status === 'done' ? '✓' : i + 1}
                  </div>
                  <div className="text-xs font-semibold text-primary-dark whitespace-nowrap">{step.label}</div>
                  <div className="text-[10px] text-secondary-dark mt-1">{step.sub}</div>
                </div>
              ))}
            </div>
          </motion.div>

        </div>
      </div>
    </div>
  );
};
