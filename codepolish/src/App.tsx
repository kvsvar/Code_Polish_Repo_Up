import { useState } from 'react';
import { Landing } from './components/Landing';
import { Progress } from './components/Progress';
import { Results } from './components/Results';
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
    <div className="h-screen flex flex-col font-sans bg-[#0B0C10] text-primary-dark selection:bg-primary-brand/30 selection:text-primary-brand relative overflow-hidden">
      
      {/* Toast Error */}
      {error && (
        <div className="absolute top-6 left-1/2 -translate-x-1/2 z-50 bg-[#FF5F56]/10 border border-[#FF5F56]/50 text-[#FF5F56] px-6 py-3 rounded-lg shadow-2xl flex items-center gap-3 backdrop-blur-md font-medium text-sm">
          <div className="w-2 h-2 rounded-full bg-[#FF5F56] shadow-[0_0_8px_rgba(255,95,86,0.8)]" />
          {error}
        </div>
      )}

      {/* Background Grid & Glows */}
      <div className="absolute inset-0 z-0 opacity-[0.03] pointer-events-none" 
           style={{ backgroundImage: 'linear-gradient(#2DD4A7 1px, transparent 1px), linear-gradient(90deg, #2DD4A7 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary-brand/20 blur-[120px] rounded-full z-0 pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-blue-500/10 blur-[120px] rounded-full z-0 pointer-events-none" />

      {/* Global Header */}
      {currentScreen !== 'results' && (
        <header className="w-full py-6 px-8 flex items-center justify-between relative z-20">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setCurrentScreen('landing')}>
            <div className="w-9 h-9 rounded-full bg-[#162025] border border-[#2DD4A7]/30 flex items-center justify-center text-primary-brand">
              <Code2 size={18} />
            </div>
            <span className="font-bold text-lg tracking-tight text-white">CodePolish</span>
          </div>
          
          <div className="px-4 py-1.5 rounded-full border border-[#2A2E37] bg-[#1A1D23]/50 text-secondary-dark text-xs font-medium font-mono backdrop-blur-md">
            Phase 1 prototype
          </div>
        </header>
      )}

      {/* Main Content Area */}
      <main className={`flex-1 flex flex-col relative z-10 w-full ${currentScreen !== 'results' ? 'items-center justify-center' : ''}`}>
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
