import { useState } from 'react';
import { Landing } from './components/Landing';
import { Progress } from './components/Progress';
import { Results } from './components/Results';
import { DependencyGraphBackground } from './components/DependencyGraphBackground';
import { Code2 } from 'lucide-react';

import { FileGraph } from './components/FileGraph';

type Screen = 'landing' | 'progress' | 'graph-reveal' | 'results';

function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('landing');
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (file?: File) => {
    if (!file) {
      setError("Please select a ZIP file first.");
      setTimeout(() => setError(null), 3000);
      return;
    }
    
    setCurrentScreen('progress');
    setError(null);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      setCurrentScreen('graph-reveal');
      
      const res = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData,
      });
      
      if (!res.ok) {
        let msg = "Analysis failed";
        try {
          const errData = await res.json();
          msg = errData.detail || msg;
        } catch(e) {}
        throw new Error(msg);
      }
      
      const reader = res.body!.getReader();
      const decoder = new TextDecoder("utf-8");
      
      setAnalysisData({ graph: { nodes: [], edges: [] } });
      const liveNodes: any[] = [];
      const liveEdges: any[] = [];
      
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || "";
        
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.replace("data: ", "");
            try {
              const event = JSON.parse(dataStr);
              if (event.type === "file") {
                liveNodes.push({ id: event.path, label: event.path.split('/').pop() });
                setAnalysisData((prev: any) => ({ ...prev, graph: { nodes: [...liveNodes], edges: [...liveEdges] } }));
              } else if (event.type === "edge") {
                liveEdges.push({ source: event.source, target: event.target });
                setAnalysisData((prev: any) => ({ ...prev, graph: { nodes: [...liveNodes], edges: [...liveEdges] } }));
              } else if (event.type === "done") {
                setAnalysisData(event.result);
                setTimeout(() => setCurrentScreen('results'), 1000);
              }
            } catch (e) {
               console.error("Failed to parse SSE line", e);
            }
          }
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to connect to the backend.");
      setCurrentScreen('landing');
      setTimeout(() => setError(null), 5000);
    }
  };

  return (
    <div className="h-screen flex flex-col font-sans bg-[#05050A] text-primary-dark selection:bg-primary-brand/30 selection:text-primary-brand relative overflow-hidden">
      
      {/* Toast Error */}
      {error && (
        <div className="absolute top-6 left-1/2 -translate-x-1/2 z-50 bg-[#FF5F56]/10 border border-[#FF5F56]/50 text-[#FF5F56] px-6 py-3 rounded-lg shadow-2xl flex items-center gap-3 backdrop-blur-md font-medium text-sm">
          <div className="w-2 h-2 rounded-full bg-[#FF5F56] shadow-[0_0_8px_rgba(255,95,86,0.8)]" />
          {error}
        </div>
      )}

      {/* Animated Dependency Graph Background */}
      <div className={`absolute inset-0 z-0 transition-opacity duration-1000 pointer-events-none ${currentScreen === 'results' ? 'opacity-15' : 'opacity-100'}`}>
        <DependencyGraphBackground />
      </div>

      {/* Global Header */}
      {currentScreen !== 'results' && (
        <header className="w-full py-6 px-8 flex items-center justify-between relative z-20">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setCurrentScreen('landing')}>
            <div className="w-9 h-9 rounded-full bg-[#13151A] border border-[#6D5EF0]/30 flex items-center justify-center text-primary-brand shadow-[0_0_15px_rgba(109,94,240,0.15)]">
              <Code2 size={18} />
            </div>
            {currentScreen !== 'landing' && (
              <span className="font-bold text-lg tracking-tight text-white">CodePolish</span>
            )}
          </div>
          

        </header>
      )}

      {/* Main Content Area */}
      <main className={`flex-1 min-h-0 overflow-hidden flex flex-col relative z-10 w-full ${currentScreen !== 'results' ? 'items-center justify-center' : ''}`}>
        {currentScreen === 'landing' && (
          <Landing onAnalyze={handleAnalyze} />
        )}
        
        {currentScreen === 'progress' && (
          <Progress />
        )}
        
        {currentScreen === 'graph-reveal' && (
          <div className="w-full max-w-5xl h-[70vh] min-h-[500px] p-8 flex flex-col items-center justify-center relative z-20">
            <h2 className="text-2xl font-bold text-white mb-6 animate-pulse">Mapping Codebase Architecture...</h2>
            {analysisData?.graph ? (
              <FileGraph 
                mode="streaming" 
                nodes={analysisData.graph.nodes} 
                edges={analysisData.graph.edges} 
              />
            ) : (
              <div className="text-red-500">
                Failed to load graph data.
                <button className="ml-4 underline" onClick={() => setCurrentScreen('results')}>Continue</button>
              </div>
            )}
          </div>
        )}
        
        {currentScreen === 'results' && (
          <Results 
            data={analysisData}
            onReset={() => {
              setCurrentScreen('landing');
              setAnalysisData(null);
            }} 
          />
        )}
      </main>
      
    </div>
  );
}

export default App;
