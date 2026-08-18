import React, { useMemo, useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import * as d3Force from 'd3-force';
import * as d3Zoom from 'd3-zoom';
import { select } from 'd3-selection';

export interface FileGraphProps {
  nodes: { id: string; label: string }[];
  edges: { source: string; target: string }[];
  mode: 'animated-reveal' | 'static' | 'streaming';
  searchQuery?: string;
  resetTrigger?: number;
  onRevealComplete?: () => void;
}

interface ForceNode extends d3Force.SimulationNodeDatum {
  id: string;
  label: string;
  inDegree: number;
  outDegree: number;
  degree: number;
  color: string;
  radius: number;
  bfsDistance: number;
}

interface ForceEdge extends d3Force.SimulationLinkDatum<ForceNode> {
  source: ForceNode | string;
  target: ForceNode | string;
}

export const FileGraph: React.FC<FileGraphProps> = ({ nodes, edges, mode, searchQuery, resetTrigger, onRevealComplete }) => {
  const VIEWBOX_WIDTH = 1200;
  const VIEWBOX_HEIGHT = 800;

  const isAnimated = mode === 'animated-reveal';
  const isStreaming = mode === 'streaming';
  
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [zoomScale, setZoomScale] = useState<number>(1);
  const svgRef = useRef<SVGSVGElement>(null);
  const gRef = useRef<SVGGElement>(null);

  const getFolderColor = (path: string) => {
    if (path.includes('components/')) return '#2DD4A7'; // Teal
    if (path.includes('services/') || path.includes('api/')) return '#6D5EF0'; // Purple
    if (path.includes('utils/') || path.includes('helpers/')) return '#3B82F6'; // Blue
    if (path.includes('tests/')) return '#9CA3AF'; // Gray
    return '#4B5563'; // Slate
  };

  const layoutData = useMemo(() => {
    if (!nodes || nodes.length === 0) return { positionedNodes: [], edgeMap: [], nodeMap: {}, maxDist: 1, coreNode: null };

    // 1. Calculate degrees
    const degs: Record<string, { in: number, out: number }> = {};
    nodes.forEach(n => degs[n.id] = { in: 0, out: 0 });
    edges.forEach(e => {
      if (degs[e.target]) degs[e.target].in += 1;
      if (degs[e.source]) degs[e.source].out += 1;
    });

    // 2. Prepare nodes for D3
    const forceNodes: ForceNode[] = nodes.map(n => {
      const d = degs[n.id] || { in: 0, out: 0 };
      const degree = d.in + d.out;
      return {
        ...n,
        inDegree: d.in,
        outDegree: d.out,
        degree,
        color: getFolderColor(n.id),
        radius: degree === 0 ? 3 : Math.min(14, 4 + (degree * 0.6)),
        bfsDistance: 0
      };
    });

    const nodeMap = forceNodes.reduce((acc, curr) => { 
      acc[curr.id] = curr; 
      return acc; 
    }, {} as Record<string, ForceNode>);

    // 3. BFS for reveal animation
    const sortedByDegree = [...forceNodes].sort((a, b) => b.degree - a.degree);
    const coreNode = sortedByDegree[0];
    
    const adj: Record<string, string[]> = {};
    edges.forEach(e => {
       if (!adj[e.source]) adj[e.source] = [];
       if (!adj[e.target]) adj[e.target] = [];
       adj[e.source].push(e.target);
       adj[e.target].push(e.source);
    });

    if (coreNode && edges.length > 0) {
       const visited = new Set<string>();
       const queue = [{ id: coreNode.id, dist: 0 }];
       visited.add(coreNode.id);
       
       while (queue.length > 0) {
           const curr = queue.shift()!;
           if (nodeMap[curr.id]) {
               nodeMap[curr.id].bfsDistance = curr.dist;
           }
           const neighbors = adj[curr.id] || [];
           for (const nbr of neighbors) {
               if (!visited.has(nbr)) {
                   visited.add(nbr);
                   queue.push({ id: nbr, dist: curr.dist + 1 });
               }
           }
       }
       const maxDistFound = Math.max(0, ...forceNodes.map(n => n.bfsDistance));
       forceNodes.forEach(n => {
           if (!visited.has(n.id)) n.bfsDistance = maxDistFound + 1;
       });
    }
    
    const maxDist = Math.max(1, ...forceNodes.map(n => n.bfsDistance));

    // 4. Prepare edges for D3
    const forceEdges: ForceEdge[] = edges
      .filter(e => nodeMap[e.source] && nodeMap[e.target])
      .map(e => ({ source: e.source, target: e.target }));

    // 5. Run static force simulation
    const repulsionStrength = forceNodes.length < 15 ? -200 : forceNodes.length < 50 ? -400 : -600;
    
    const simulation = d3Force.forceSimulation(forceNodes)
      .force("link", d3Force.forceLink(forceEdges).id((d: any) => d.id).distance(80))
      .force("charge", d3Force.forceManyBody().strength(repulsionStrength))
      .force("center", d3Force.forceCenter(VIEWBOX_WIDTH / 2, VIEWBOX_HEIGHT / 2))
      .force("collide", d3Force.forceCollide().radius((d: any) => d.radius + 20))
      .stop();

    // Run statically to cache positions
    const iterations = Math.min(200, Math.max(50, forceNodes.length * 2));
    for (let i = 0; i < iterations; i++) {
      simulation.tick();
    }

    return { positionedNodes: forceNodes, edgeMap: forceEdges, nodeMap, maxDist, coreNode };
  }, [nodes, edges]);

  const { positionedNodes, edgeMap, maxDist } = layoutData;

  const maxNodeStagger = 1.5;
  const nodeStaggerStep = maxNodeStagger / maxDist;

  useEffect(() => {
    if (isAnimated && onRevealComplete && nodes.length > 0) {
      const totalAnimationTime = maxNodeStagger + 1.5;
      const timer = setTimeout(() => {
        onRevealComplete();
      }, totalAnimationTime * 1000);
      return () => clearTimeout(timer);
    }
  }, [isAnimated, onRevealComplete, nodes.length, maxNodeStagger]);

  // Handle D3 Zoom
  useEffect(() => {
    if (!svgRef.current || !gRef.current) return;

    const svg = select(svgRef.current);
    const g = select(gRef.current);

    const zoom = d3Zoom.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 5])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
        setZoomScale(event.transform.k);
      });

    svg.call(zoom);
    
    if (resetTrigger && resetTrigger > 0) {
      svg.transition().duration(750).call(zoom.transform, d3Zoom.zoomIdentity);
    }
  }, [resetTrigger, nodes.length]);

  return (
    <div className="w-full h-full relative overflow-hidden flex items-center justify-center">
      {nodes.length === 0 ? (
        <div className="text-secondary-dark text-sm z-10 absolute">No graph data available</div>
      ) : (
        <svg 
          ref={svgRef}
          viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`} 
          className="w-full h-full z-10 drop-shadow-md cursor-grab active:cursor-grabbing"
        >
          <defs>
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          <g ref={gRef}>
            {/* EDGES */}
            <g className="edges">
              {edgeMap.map((e, idx) => {
                const src = e.source as ForceNode;
                const tgt = e.target as ForceNode;
                if (!src || !tgt || src.x === undefined || src.y === undefined || tgt.x === undefined || tgt.y === undefined) return null;

                const dx = tgt.x - src.x;
                const dy = tgt.y - src.y;
                const cx = src.x + dx/2 + dy*0.15;
                const cy = src.y + dy/2 - dx*0.15;
                const path = `M${src.x},${src.y} Q${cx},${cy} ${tgt.x},${tgt.y}`;

                const isConnectedToHovered = hoveredNode === src.id || hoveredNode === tgt.id;
                const isSearched = searchQuery && (src.label.toLowerCase().includes(searchQuery.toLowerCase()) || tgt.label.toLowerCase().includes(searchQuery.toLowerCase()));
                
                let isFaded = false;
                if (hoveredNode) {
                  isFaded = !isConnectedToHovered;
                } else if (searchQuery) {
                  isFaded = !isSearched;
                }

                const edgeDelay = isAnimated ? Math.max(src.bfsDistance, tgt.bfsDistance) * nodeStaggerStep + 0.2 : 0;

                return (
                  <motion.path
                    key={`edge-${src.id}-${tgt.id}`}
                    d={path}
                    fill="none"
                    stroke="#2DD4A7"
                    strokeWidth="1.5"
                    className="transition-all duration-300 pointer-events-none"
                    initial={(isAnimated || isStreaming) ? { pathLength: 0, opacity: 0 } : { pathLength: 1, opacity: isFaded ? 0.05 : 0.25 }}
                    animate={{ 
                      pathLength: 1, 
                      opacity: isFaded ? 0.05 : isConnectedToHovered ? 0.9 : searchQuery ? 0.1 : 0.25,
                      d: path 
                    }}
                    transition={{ 
                      delay: edgeDelay, 
                      duration: 0.6,
                      ease: "easeInOut"
                    }}
                  />
                );
              })}
            </g>

            {/* NODES */}
            <g className="nodes">
              {positionedNodes.map((n) => {
                const isHovered = hoveredNode === n.id;
                const isSearched = searchQuery && n.label.toLowerCase().includes(searchQuery.toLowerCase());
                
                let isFaded = false;
                if (hoveredNode) {
                  isFaded = !isHovered && !edgeMap.some(e => {
                    const s = e.source as ForceNode;
                    const t = e.target as ForceNode;
                    return (s.id === n.id && t.id === hoveredNode) || (t.id === n.id && s.id === hoveredNode);
                  });
                } else if (searchQuery) {
                  isFaded = !isSearched;
                }

                // Hide labels if dense, unless highly connected, hovered, or zoomed in
                const showLabel = nodes.length <= 20 || n.degree > 4 || isHovered || isSearched || zoomScale > 1.4;
                const isIsolated = n.degree === 0;

                return (
                  <motion.g 
                    key={`node-${n.id}`} 
                    className="cursor-pointer"
                    onMouseEnter={() => setHoveredNode(n.id)}
                    onMouseLeave={() => setHoveredNode(null)}
                    initial={(isAnimated || isStreaming) ? { scale: 0, opacity: 0, x: n.x, y: n.y } : { scale: 1, opacity: isIsolated ? 0.4 : 1, x: n.x, y: n.y }}
                    animate={{ 
                      scale: isHovered || isSearched ? 1.4 : 1, 
                      opacity: isFaded ? 0.15 : isIsolated ? 0.4 : 1,
                      x: n.x,
                      y: n.y
                    }}
                    transition={{ 
                      delay: isAnimated ? n.bfsDistance * nodeStaggerStep : 0,
                      type: "spring",
                      stiffness: 260,
                      damping: 20
                    }}
                  >
                    <circle
                      r={n.radius}
                      fill={n.color}
                      filter={n.degree >= 10 ? "url(#glow)" : undefined}
                      stroke="#0B0C10"
                      strokeWidth={isHovered || isSearched ? 2 : 1.5}
                      className="transition-colors duration-300"
                    />
                    <text
                      y={n.radius + 14}
                      textAnchor="middle"
                      fill="#9CA3AF"
                      fontSize={Math.max(8, 12 / zoomScale)}
                      className={`font-mono transition-all duration-300 pointer-events-none drop-shadow-md ${showLabel ? 'opacity-100' : 'opacity-0'} ${isHovered || isSearched ? 'fill-white font-bold z-50' : 'opacity-80'}`}
                    >
                      {n.label}
                    </text>
                  </motion.g>
                );
              })}
            </g>
          </g>
        </svg>
      )}
    </div>
  );
};
