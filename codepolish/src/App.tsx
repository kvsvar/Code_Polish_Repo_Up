import { useState } from 'react';
import { Landing } from './components/Landing';
import { Progress } from './components/Progress';
import { Results } from './components/Results';
import { DependencyGraphBackground } from './components/DependencyGraphBackground';
import { Code2 } from 'lucide-react';

type Screen = 'landing' | 'progress' | 'results';

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
      
      const data = await res.json();
      setAnalysisData(data);
      setCurrentScreen('results');
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
          
          <div className="px-4 py-1.5 rounded-full border border-[#2A2E37] bg-[#1A1D23]/50 text-secondary-dark text-xs font-medium font-mono backdrop-blur-md">
            Phase 1 prototype
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
