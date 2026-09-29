import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Code2, Home, Network, AlertTriangle, Archive, Clock, 
  Download, Moon, Sun, Lock, ChevronRight, File, ShieldAlert,
  Activity, CheckCircle2, ShieldCheck, Database, LayoutDashboard, Zap
} from 'lucide-react';
import { GraphView } from './GraphView';
import { DependencyGraphBackground } from './DependencyGraphBackground';

interface Finding {
  category: string;
  title: string;
  description: string;
  severity: "High" | "Medium" | "Low";
  file?: string;
}

interface Rubric {
  final_score: number;
  structural_score: number;
  metrics_score: number;
  security_score: number;
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
  const [filterCategory, setFilterCategory] = useState<string>("All");

  const d = data || {};
  const rubric: Rubric | undefined = d.rubric;
  
  const score = rubric?.final_score ?? (d.score ?? 0);
  const structuralScore = rubric?.structural_score ?? 0;
  const metricsScore = rubric?.metrics_score ?? 0;
  const securityScore = rubric?.security_score ?? 100;
  
  const language = d.language || 'Unknown';
  const framework = d.framework || 'Unknown';
  const filesCount = d.files || 0;
  const issues: Finding[] = d.issues || [];
  const tree = d.tree || [];

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
    a.download = 'code-polish-report.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const scrollToSection = (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  const getScoreColor = (val: number) => {
    if (val >= 80) return 'text-[#10B981]'; // Soft green-teal
    if (val >= 50) return 'text-[#F59E0B]'; // Amber
    return 'text-[#EF4444]'; // Red
  };

  const getSeverityStyle = (sev: string) => {
    switch (sev?.toLowerCase()) {
      case 'high': return 'bg-[#EF4444]/20 text-[#EF4444] border-[#EF4444]/30';
      case 'medium': return 'bg-[#F59E0B]/20 text-[#F59E0B] border-[#F59E0B]/30';
      default: return 'bg-[#3B82F6]/20 text-[#3B82F6] border-[#3B82F6]/30'; // Blue for Low/Style
    }
  };

  const getRatingStyle = (rating: string) => {
    switch (rating) {
      case 'good': return 'bg-[#059669]/20 text-[#34D399] border-[#34D399]/30';
      case 'regular': return 'bg-[#D97706]/20 text-[#FBBF24] border-[#FBBF24]/30';
      case 'bad': return 'bg-[#991B1B]/20 text-[#F87171] border-[#F87171]/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getCategoryIcon = (cat: string) => {
    switch(cat) {
      case 'Structural': return <Network size={16} className="text-[#6D5EF0]" />;
      case 'Metrics': return <Activity size={16} className="text-[#6D5EF0]" />;
      case 'Security': return <ShieldAlert size={16} className="text-[#EF4444]" />;
      default: return <AlertTriangle size={16} className="text-[#F59E0B]" />;
    }
  };

  const filteredIssues = issues
    .filter(i => filterCategory === "All" || i.category === filterCategory)
    .sort((a, b) => {
      const rank: Record<string, number> = { "High": 3, "Medium": 2, "Low": 1 };
      return (rank[b.severity] || 0) - (rank[a.severity] || 0);
    });

  const maskSecret = (desc: string) => {
    // Basic mask for UI display if needed, but the backend description should ideally not contain the raw secret anyway.
    return desc.replace(/([A-Za-z0-9_]{4})[A-Za-z0-9_]{8,}([A-Za-z0-9_]{4})/g, '$1••••••••$2');
  };

  const displayScore = Math.round(score);

  return (
    <div className="flex h-full w-full bg-[#05050A] text-white overflow-hidden font-sans relative">
      {/* Background Texture - SVG dependency graph from landing page, masked */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-[0.08]" style={{ maskImage: 'radial-gradient(ellipse at center, black, transparent 80%)', WebkitMaskImage: 'radial-gradient(ellipse at center, black, transparent 80%)' }}>
        <DependencyGraphBackground />
      </div>

      {/* SIDEBAR */}
      <div className="w-64 border-r border-white/5 bg-[#05050A]/80 backdrop-blur-xl p-4 flex flex-col shrink-0 relative z-20 overflow-y-auto overflow-x-hidden">
        <div className="flex items-center gap-2 mb-8 px-2 cursor-pointer group" onClick={onReset}>
          <div className="text-transparent bg-clip-text bg-gradient-to-r from-[#6D5EF0] to-[#3B82F6]">
            <Code2 size={24} className="text-[#6D5EF0]" />
          </div>
          <span className="font-bold text-xl tracking-tight text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r from-[#6D5EF0] to-[#3B82F6] transition-all">
            Repo-Up
          </span>
        </div>

        <nav className="space-y-1 mb-8">
          <a href="#overview" onClick={(e) => scrollToSection(e, 'overview')} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors focus:bg-[#6D5EF0]/10 focus:text-[#6D5EF0]">
            <LayoutDashboard size={18} /> Dashboard
          </a>
          <a href="#iso" onClick={(e) => scrollToSection(e, 'iso')} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors focus:bg-[#6D5EF0]/10 focus:text-[#6D5EF0]">
            <Activity size={18} /> ISO 25010
          </a>
          <a href="#findings" onClick={(e) => scrollToSection(e, 'findings')} className="flex items-center justify-between px-3 py-2.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors focus:bg-[#6D5EF0]/10 focus:text-[#6D5EF0]">
            <div className="flex items-center gap-3"><ShieldAlert size={18} /> Findings</div>
            <span className="bg-[#EF4444]/20 text-[#EF4444] text-xs px-2 py-0.5 rounded-full font-bold">{issues.length}</span>
          </a>
          <a href="#architecture" onClick={(e) => scrollToSection(e, 'architecture')} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors focus:bg-[#6D5EF0]/10 focus:text-[#6D5EF0]">
            <Network size={18} /> Architecture
          </a>
        </nav>

        <div className="mt-4 px-3 mb-auto">
          <div className="text-[10px] font-bold text-gray-500 tracking-wider mb-3 uppercase">Session Details</div>
          <div className="flex items-center gap-2 mb-3">
            <span className="font-medium text-sm text-gray-300">Target</span>
            <span className="bg-[#6D5EF0]/20 border border-[#6D5EF0]/30 text-[#8B5CF6] text-[10px] px-1.5 py-0.5 rounded">{language}</span>
          </div>
          <div className="space-y-2 text-xs text-gray-400">
            <div className="flex items-center gap-2"><File size={12} /> {filesCount} Files Parsed</div>
            <div className="flex items-center gap-2"><Clock size={12} /> Live Telemetry</div>
          </div>
        </div>

        {/* CTA Phase 4 */}
        <div className="mt-8 bg-gradient-to-b from-white/5 to-transparent border border-white/10 rounded-xl p-4 text-center relative overflow-hidden group">
          <div className="absolute inset-0 bg-[#6D5EF0]/5 group-hover:bg-[#6D5EF0]/10 transition-colors" />
          <h4 className="font-bold text-sm mb-2 text-white relative z-10 flex items-center justify-center gap-2"><Zap size={14} className="text-[#F59E0B]" /> Auto-Fix</h4>
          <p className="text-xs text-gray-400 mb-4 relative z-10">Deploy fixes to secure sandbox</p>
          <button className="w-full py-2 bg-black/40 border border-white/10 rounded-lg text-xs font-medium text-gray-400 flex items-center justify-center gap-2 cursor-not-allowed relative z-10">
            <Lock size={12} /> Phase 4 Feature
          </button>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 flex flex-col min-w-0 relative z-10 h-full">
        
        {/* Header */}
        <header className="h-16 border-b border-white/5 bg-[#05050A]/70 backdrop-blur-md flex items-center justify-between px-8 shrink-0">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span>Repo-Up</span> <ChevronRight size={14} /> <span className="text-white font-medium">Dashboard</span>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setShowGraph(!showGraph)}
              className="flex items-center gap-2 text-xs font-medium transition-all px-4 py-2 border rounded-lg bg-gradient-to-r from-[#6D5EF0] to-[#3B82F6] text-white border-transparent hover:shadow-[0_0_15px_rgba(109,94,240,0.4)]"
            >
              <Network size={14} /> Full Graph Explorer
            </button>
            <button 
              onClick={handleDownloadReport}
              className="flex items-center gap-2 text-xs font-medium text-gray-300 hover:text-white transition-colors px-3 py-2 border border-white/10 rounded-lg hover:border-white/30 bg-white/5"
            >
              <Download size={14} /> Export Report
            </button>
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#6D5EF0] to-[#3B82F6] text-white flex items-center justify-center text-xs font-bold shadow-lg ml-2">
              US
            </div>
          </div>
        </header>

        {/* Scrollable Dashboard */}
        <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8 scroll-smooth">
          
          <AnimatePresence>
            {showGraph && d.graph && (
              <GraphView 
                nodes={d.graph.nodes} 
                edges={d.graph.edges}
                issues={issues}
                sessionId={d.session_id}
                onClose={() => setShowGraph(false)} 
              />
            )}
          </AnimatePresence>
          
          {/* TOP SUMMARY BAR */}
          <motion.div 
            id="overview"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
          >
            {/* BIG SCORE CARD */}
            <div className="col-span-1 md:col-span-2 bg-[#0B0C10]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-8 relative flex items-center gap-8 shadow-2xl">
              {/* Circular Progress */}
              <div className="relative w-40 h-40 shrink-0">
                <svg className="w-full h-full transform -rotate-90 overflow-visible" viewBox="0 0 100 100">
                  <defs>
                    <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#6D5EF0" />
                      <stop offset="100%" stopColor="#3B82F6" />
                    </linearGradient>
                  </defs>
                  <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                  <circle cx="50" cy="50" r="45" fill="none" stroke="url(#scoreGrad)" strokeWidth="8" strokeDasharray="282.7" strokeDashoffset={282.7 - (282.7 * score) / 100} className="drop-shadow-[0_0_10px_rgba(109,94,240,0.6)] transition-all duration-1000" />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400">{displayScore}</span>
                </div>
              </div>

              {/* Info */}
              <div className="flex-1">
                <div className="text-[10px] font-bold text-[#6D5EF0] tracking-wider mb-2 uppercase flex items-center gap-2"><Activity size={12}/> Overall Readiness</div>
                <h2 className="text-3xl font-bold mb-2 text-white">
                  {score >= 85 ? 'Production Ready' : score >= 60 ? 'Needs Refactoring' : 'Critical Issues'}
                </h2>
                
                <p className="text-sm text-gray-400 mb-6 max-w-md leading-relaxed">
                  Your codebase structure and metrics have been analyzed. Review the findings below to address architectural debt and security risks.
                </p>

                {/* Sub-scores */}
                {rubric && (
                  <div className="flex gap-4">
                    <div className="bg-white/5 border border-white/10 px-4 py-2 rounded-lg flex flex-col min-w-[100px]">
                      <span className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Structure</span>
                      <span className={`text-xl font-bold ${getScoreColor(structuralScore)}`}>{structuralScore}</span>
                    </div>
                    <div className="bg-white/5 border border-white/10 px-4 py-2 rounded-lg flex flex-col min-w-[100px]">
                      <span className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Metrics</span>
                      <span className={`text-xl font-bold ${getScoreColor(metricsScore)}`}>{metricsScore}</span>
                    </div>
                    <div className="bg-white/5 border border-white/10 px-4 py-2 rounded-lg flex flex-col min-w-[100px]">
                      <span className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Security</span>
                      <span className={`text-xl font-bold ${getScoreColor(securityScore)}`}>{securityScore}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* TIMELINE */}
            <div className="col-span-1 bg-[#0B0C10]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-xl flex flex-col">
              <div className="flex items-center gap-2 mb-6">
                <Clock size={16} className="text-[#3B82F6]" /> 
                <h3 className="font-bold text-sm text-white">Analysis Pipeline</h3>
              </div>
              <div className="flex-1 flex flex-col justify-center space-y-4 relative">
                <div className="absolute left-2.5 top-2 bottom-2 w-[1px] bg-white/10 -z-10" />
                {[
                  { label: 'Parse AST', status: 'done' },
                  { label: 'Extract Entities', status: 'done' },
                  { label: 'Build Dependency Graph', status: 'done' },
                  { label: 'Run Security Rules', status: 'done' },
                  { label: 'Compute ISO Metrics', status: 'done' },
                ].map((step, i) => (
                  <div key={i} className="flex items-center gap-4">
                    <div className="w-5 h-5 rounded-full bg-gradient-to-r from-[#6D5EF0] to-[#3B82F6] flex items-center justify-center shrink-0">
                      <CheckCircle2 size={12} className="text-white" />
                    </div>
                    <span className="text-sm text-gray-300 font-medium">{step.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* ISO 25010 BREAKDOWN */}
          {rubric && (
            <motion.div 
              id="iso"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Database size={18} className="text-[#6D5EF0]" /> ISO/IEC 25010 Code Quality</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {['Modularity', 'Analysability', 'Modifiability', 'Testability'].map((cat, idx) => {
                  const val = rubric.category_breakdown[cat.toLowerCase() as keyof typeof rubric.category_breakdown];
                  return (
                    <div key={idx} className="bg-[#0B0C10]/60 backdrop-blur-xl border border-white/10 rounded-xl p-5 relative overflow-hidden group hover:border-[#6D5EF0]/40 transition-colors">
                      <div className="flex items-center justify-between mb-4">
                        <span className="font-semibold text-sm text-gray-200">{cat}</span>
                        <Activity size={14} className="text-gray-500 group-hover:text-[#6D5EF0] transition-colors" />
                      </div>
                      <div className="text-3xl font-black text-white flex items-baseline gap-1 mb-3">
                        {val} <span className="text-xs font-medium text-gray-500">/100</span>
                      </div>
                      <div className="h-1.5 w-full bg-black/50 rounded-full overflow-hidden">
                         <div className={`h-full bg-gradient-to-r from-[#6D5EF0] to-[#3B82F6] rounded-full`} style={{ width: `${val}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          )}

          {/* METRIC RATINGS */}
          {rubric && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="bg-[#0B0C10]/60 backdrop-blur-xl border border-white/10 rounded-2xl flex flex-col shadow-xl overflow-hidden"
            >
              <div className="p-5 border-b border-white/10 flex items-center justify-between bg-black/20">
                <h3 className="font-bold flex items-center gap-2 text-white">
                  <Activity size={16} className="text-[#3B82F6]" /> 
                  Codebase Metrics
                </h3>
              </div>
              <div className="p-5 overflow-x-auto">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {[
                    { key: 'cof', label: 'Coupling Factor (COF)', tip: 'Thresholds: Good < 0.1, Regular 0.1-0.2, Bad > 0.2' },
                    { key: 'afferent_couplings', label: 'Afferent Couplings', tip: 'Thresholds: Good < 5, Regular 5-10, Bad > 10' },
                    { key: 'public_fields', label: 'Public Fields', tip: 'Thresholds: Good 0, Regular 1-3, Bad > 3' },
                    { key: 'public_methods', label: 'Weighted Methods/Class', tip: 'Thresholds: Good < 7, Regular 7-15, Bad > 15' },
                    { key: 'dit', label: 'Depth of Inheritance', tip: 'Thresholds: Good < 2, Regular = 2, Bad > 2' },
                    { key: 'lcom', label: 'Lack of Cohesion (LCOM)', tip: 'Thresholds: Good < 5, Regular 5-10, Bad > 10' },
                  ].map((m) => {
                    const rating = rubric.metric_ratings[m.key as keyof typeof rubric.metric_ratings] || 'good';
                    return (
                      <div key={m.key} className="bg-black/30 border border-white/5 p-4 rounded-xl flex items-center justify-between hover:bg-white/5 transition-colors">
                        <span className="text-sm font-semibold text-gray-300">{m.label}</span>
                        <span className={`text-[10px] uppercase tracking-wider font-bold px-2.5 py-1 rounded-full border ${getRatingStyle(rating)}`}>
                          {rating}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          )}

          {/* FINDINGS LIST */}
          <motion.div 
            id="findings"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex flex-col xl:flex-row gap-6"
          >
            {/* Findings Section */}
            <div className="flex-1 bg-[#0B0C10]/60 backdrop-blur-xl border border-white/10 rounded-2xl flex flex-col shadow-xl overflow-hidden min-h-[500px]">
              <div className="p-5 border-b border-white/10 flex items-center justify-between bg-black/20">
                <h3 className="font-bold flex items-center gap-2 text-white">
                  <ShieldAlert size={16} className="text-[#F59E0B]" /> 
                  Analysis Findings
                </h3>
                
                {/* Filters */}
                <div className="flex gap-2">
                  {["All", "Structural", "Metrics", "Security"].map(cat => (
                    <button 
                      key={cat}
                      onClick={() => setFilterCategory(cat)}
                      className={`text-xs px-3 py-1.5 rounded-full font-medium transition-all ${filterCategory === cat ? 'bg-gradient-to-r from-[#6D5EF0] to-[#3B82F6] text-white shadow-md border border-transparent' : 'bg-white/5 border border-white/10 text-gray-400 hover:text-white hover:bg-white/10'}`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-5 flex-1 overflow-y-auto">
                <ul className="space-y-4">
                  {filteredIssues.length === 0 && (
                    <div className="text-center text-gray-500 py-20 text-sm flex flex-col items-center">
                      <ShieldCheck size={48} className="text-[#10B981] mb-4 opacity-50" />
                      No findings detected for this category!
                    </div>
                  )}
                  {filteredIssues.map((issue, i) => (
                    <li key={i} className="flex flex-col p-4 rounded-xl bg-black/40 border border-white/5 hover:border-white/10 transition-colors">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-3">
                          {getCategoryIcon(issue.category)}
                          <span className="font-bold text-sm text-gray-100">{issue.title}</span>
                        </div>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getSeverityStyle(issue.severity)}`}>
                          {issue.severity || 'Medium'}
                        </span>
                      </div>
                      
                      <div className="text-sm text-gray-400 pl-7 leading-relaxed">
                        {maskSecret(issue.description || '')}
                      </div>
                      
                      {issue.file && (
                        <div className="mt-3 pl-7 flex gap-2">
                          <span className="px-2.5 py-1 rounded-md bg-white/5 border border-white/10 text-xs text-gray-400 font-mono flex items-center gap-1.5">
                            <File size={10} className="text-[#6D5EF0]"/> {issue.file}
                          </span>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Architecture Preview */}
            <div id="architecture" className="w-full xl:w-80 bg-[#0B0C10]/60 backdrop-blur-xl border border-white/10 rounded-2xl flex flex-col shadow-xl overflow-hidden h-[500px] shrink-0">
              <div className="p-5 border-b border-white/10 flex items-center justify-between bg-black/20">
                <h3 className="font-bold flex items-center gap-2 text-white">
                  <Network size={16} className="text-[#6D5EF0]" /> 
                  Architecture Preview
                </h3>
              </div>
              
              {/* Static Graph Preview Portal */}
              <div 
                className="h-48 bg-[#05050A] border-b border-white/5 relative overflow-hidden group cursor-pointer"
                onClick={() => setShowGraph(true)}
              >
                <div className="absolute inset-0 z-0 opacity-50 blur-[1px]">
                   <DependencyGraphBackground />
                </div>
                <div className="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-all z-10 flex items-center justify-center">
                  <span className="bg-black/60 text-white backdrop-blur-md px-3 py-1.5 rounded-lg text-xs font-semibold border border-white/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
                    <Network size={14}/> Click to Expand Full Graph
                  </span>
                </div>
              </div>

              {/* Tree View */}
              <div className="p-5 flex-1 font-mono text-xs overflow-auto bg-transparent">
                <div className="text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-3">Project File Tree</div>
                {tree.length === 0 && (
                  <div className="text-gray-600">No files detected.</div>
                )}
                {tree.map((node: string, i: number) => (
                  <div key={i} className="whitespace-pre text-gray-400 hover:text-[#6D5EF0] transition-colors cursor-default py-0.5">
                    {node}
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
          
        </div>
      </div>
    </div>
  );
};
