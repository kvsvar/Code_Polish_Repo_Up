import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Network, File, ArrowLeft, Search, ZoomIn, Maximize } from 'lucide-react';
import { FileGraph } from './FileGraph';

interface GraphViewProps {
  nodes: { id: string; label: string }[];
  edges: { source: string; target: string }[];
  onClose: () => void;
}

export const GraphView: React.FC<GraphViewProps> = ({ nodes, edges, onClose }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [resetTrigger, setResetTrigger] = useState(0);

  // Compute stats
  const stats = useMemo(() => {
    const totalFiles = nodes.length;
    const totalEdges = edges.length;
    
    // Find most connected node
    const degs: Record<string, number> = {};
    nodes.forEach(n => degs[n.id] = 0);
    edges.forEach(e => {
      if (degs[e.target] !== undefined) degs[e.target]++;
      if (degs[e.source] !== undefined) degs[e.source]++;
    });

    let maxNode = { id: '', degree: -1 };
    for (const [id, deg] of Object.entries(degs)) {
      if (deg > maxNode.degree) {
        maxNode = { id, degree: deg };
      }
    }
    const coreNode = nodes.find(n => n.id === maxNode.id)?.label || 'None';

    return { totalFiles, totalEdges, coreNode };
  }, [nodes, edges]);

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      className="fixed inset-0 z-50 bg-[#05050A] flex flex-col font-sans"
    >
      {/* HEADER */}
      <header className="h-16 border-b border-[#2A2E37] bg-[#0F1115]/80 backdrop-blur-md flex items-center justify-between px-6 shrink-0 relative z-20">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-[#1A1D23] border border-[#2A2E37] flex items-center justify-center text-primary-brand shadow-inner">
            <Network size={20} />
          </div>
          <div>
            <h1 className="font-bold text-white text-lg tracking-tight">Dependency Graph</h1>
            <p className="text-xs text-secondary-dark">Interactive architecture map</p>
          </div>
        </div>

        {/* Search */}
        <div className="flex-1 max-w-md mx-8 relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary-dark" />
          <input 
            type="text" 
            placeholder="Search files to highlight..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#13151A] border border-[#2A2E37] rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder:text-secondary-dark focus:outline-none focus:border-primary-brand/50 transition-colors"
          />
        </div>

        <button 
          onClick={onClose}
          className="flex items-center gap-2 text-sm font-medium text-secondary-dark hover:text-white bg-[#1A1D23] border border-[#2A2E37] hover:border-primary-brand/50 px-4 py-2 rounded-lg transition-all"
        >
          <ArrowLeft size={16} /> Back to results
        </button>
      </header>

      {/* GRAPH CANVAS */}
      <div className="flex-1 relative overflow-hidden bg-gradient-to-br from-[#0B0C10] to-[#0F1115]">
        <FileGraph 
          mode="static" 
          nodes={nodes} 
          edges={edges} 
          searchQuery={searchQuery}
          resetTrigger={resetTrigger}
        />

        {/* Legend Panel (Bottom Left) */}
        <div className="absolute bottom-6 left-6 bg-[#0F1115]/80 backdrop-blur-md border border-[#2A2E37] p-4 rounded-xl shadow-2xl pointer-events-none">
          <h4 className="text-[10px] font-bold text-secondary-dark uppercase tracking-wider mb-3">Directory Legend</h4>
          <ul className="space-y-2 text-xs font-medium text-gray-300">
            <li className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-[#2DD4A7]" /> components/</li>
            <li className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-[#6D5EF0]" /> services/ | api/</li>
            <li className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-[#3B82F6]" /> utils/ | helpers/</li>
            <li className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-[#9CA3AF]" /> tests/</li>
            <li className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-[#4B5563]" /> other files</li>
          </ul>
        </div>

        {/* Stats Panel (Top Right) */}
        <div className="absolute top-6 right-6 bg-[#0F1115]/80 backdrop-blur-md border border-[#2A2E37] p-4 rounded-xl shadow-2xl flex gap-6">
          <div>
            <div className="text-[10px] font-bold text-secondary-dark uppercase tracking-wider mb-1">Total Files</div>
            <div className="text-xl font-bold text-white flex items-center gap-2">
              <File size={16} className="text-primary-brand" /> {stats.totalFiles}
            </div>
          </div>
          <div className="w-px bg-[#2A2E37]" />
          <div>
            <div className="text-[10px] font-bold text-secondary-dark uppercase tracking-wider mb-1">Dependencies</div>
            <div className="text-xl font-bold text-white flex items-center gap-2">
              <Network size={16} className="text-[#3B82F6]" /> {stats.totalEdges}
            </div>
          </div>
          <div className="w-px bg-[#2A2E37]" />
          <div>
            <div className="text-[10px] font-bold text-secondary-dark uppercase tracking-wider mb-1">Core Node</div>
            <div className="text-sm font-mono font-bold text-[#6D5EF0] bg-[#6D5EF0]/10 px-2 py-0.5 rounded border border-[#6D5EF0]/20 mt-1">
              {stats.coreNode}
            </div>
          </div>
        </div>

        {/* Controls (Bottom Right) */}
        <div className="absolute bottom-6 right-6 flex flex-col gap-2">
          <div className="bg-[#0F1115]/80 backdrop-blur-md border border-[#2A2E37] p-3 rounded-xl shadow-2xl flex flex-col gap-3">
            <div className="text-[10px] font-bold text-secondary-dark uppercase tracking-wider text-center">Controls</div>
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <div className="px-1.5 py-0.5 bg-[#1A1D23] border border-[#2A2E37] rounded">Scroll</div>
              <span>to zoom</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <div className="px-1.5 py-0.5 bg-[#1A1D23] border border-[#2A2E37] rounded">Drag</div>
              <span>to pan</span>
            </div>
            <button 
              onClick={() => setResetTrigger(prev => prev + 1)}
              className="mt-2 w-full py-1.5 bg-[#1A1D23] hover:bg-[#2A2E37] border border-[#2A2E37] rounded-lg text-xs font-medium text-white transition-colors flex items-center justify-center gap-1.5"
            >
              <Maximize size={12} /> Reset View
            </button>
          </div>
        </div>

      </div>
    </motion.div>
  );
};
