import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { X, FileCode } from 'lucide-react';
import Editor from '@monaco-editor/react';

interface CodeViewerProps {
  sessionId: string;
  filePath: string;
  line?: number;
  fileIssues?: any[];
  onClose: () => void;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({ sessionId, filePath, line, fileIssues = [], onClose }) => {
  const [content, setContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [editorInstance, setEditorInstance] = useState<any>(null);
  const [monacoInstance, setMonacoInstance] = useState<any>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    
    fetch(`http://localhost:8000/file-content?session_id=${sessionId}&path=${encodeURIComponent(filePath)}`)
      .then(res => {
        if (!res.ok) throw new Error("Could not load file content");
        return res.json();
      })
      .then(data => {
        if (isMounted) {
          setContent(data.content);
          setLoading(false);
        }
      })
      .catch(err => {
        if (isMounted) {
          setError(err.message);
          setLoading(false);
        }
      });
      
    return () => { isMounted = false; };
  }, [sessionId, filePath]);

  useEffect(() => {
    if (editorInstance && line) {
      editorInstance.revealLineInCenter(line);
      // We will rely on the markers (squigglies) instead of full line background highlighting
      // for a cleaner IDE-like experience, but we can still flash the line if wanted.
    }
  }, [editorInstance, line]);

  useEffect(() => {
    if (editorInstance && monacoInstance && fileIssues.length > 0) {
      const model = editorInstance.getModel();
      if (!model) return;

      const markers = fileIssues
        .filter(i => i.line)
        .map(issue => {
          let severityLevel = monacoInstance.MarkerSeverity.Info;
          if (issue.severity === 'High') severityLevel = monacoInstance.MarkerSeverity.Error;
          else if (issue.severity === 'Medium') severityLevel = monacoInstance.MarkerSeverity.Warning;

          return {
            startLineNumber: issue.line,
            startColumn: 1,
            endLineNumber: issue.line,
            endColumn: 1000,
            message: `${issue.title}\n\n${issue.description}\n\nSuggestion: Consider refactoring or adding appropriate checks as highlighted by Repo-Up.`,
            severity: severityLevel,
            source: 'Repo-Up'
          };
        });

      monacoInstance.editor.setModelMarkers(model, "repo-up", markers);
    }
  }, [editorInstance, monacoInstance, fileIssues]);

  const handleEditorDidMount = (editor: any, monaco: any) => {
    setEditorInstance(editor);
    setMonacoInstance(monaco);
    if (line) {
      editor.revealLineInCenter(line);
    }
  };

  const getLanguage = (path: string) => {
    const ext = path.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'ts': case 'tsx': return 'typescript';
      case 'js': case 'jsx': return 'javascript';
      case 'py': return 'python';
      case 'java': return 'java';
      case 'cpp': case 'cc': case 'h': case 'hpp': return 'cpp';
      case 'json': return 'json';
      case 'html': return 'html';
      case 'css': return 'css';
      default: return 'plaintext';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 z-40 bg-black/60 backdrop-blur-sm flex items-center justify-center p-8"
    >
      <motion.div 
        initial={{ y: 20, opacity: 0, scale: 0.95 }}
        animate={{ y: 0, opacity: 1, scale: 1 }}
        exit={{ y: 20, opacity: 0, scale: 0.95 }}
        className="w-full max-w-5xl h-full max-h-[85vh] bg-[#0B0C10] border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden relative"
      >
        {/* Header */}
        <div className="h-14 border-b border-white/10 bg-white/5 flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center gap-3">
            <FileCode size={18} className="text-[#6D5EF0]" />
            <span className="font-mono text-sm text-white font-medium">{filePath}</span>
            {line && (
              <span className="bg-white/10 text-gray-300 px-2 py-0.5 rounded text-xs font-mono">
                Line {line}
              </span>
            )}
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Editor Area */}
        <div className="flex-1 relative bg-[#05050A]">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
              <div className="animate-pulse flex items-center gap-2">
                Loading source code...
              </div>
            </div>
          )}
          
          {error && (
            <div className="absolute inset-0 flex items-center justify-center text-red-400 text-sm p-6 text-center">
              Failed to load file content: {error}
            </div>
          )}

          {!loading && !error && content && (
            <Editor
              height="100%"
              language={getLanguage(filePath)}
              theme="vs-dark"
              value={content}
              onMount={handleEditorDidMount}
              options={{
                readOnly: true,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                fontSize: 13,
                fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                lineHeight: 24,
                padding: { top: 24, bottom: 24 },
                renderLineHighlight: 'none',
                scrollbar: {
                  useShadows: false,
                  verticalScrollbarSize: 10,
                  horizontalScrollbarSize: 10
                }
              }}
            />
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};
