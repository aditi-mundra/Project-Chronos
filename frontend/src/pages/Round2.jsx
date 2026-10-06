import { useState, useEffect } from 'react';
import { Terminal, ArrowRight, ShieldCheck, FileText, AlertTriangle, Database, Lock } from 'lucide-react';
import { soundFx } from '../utils/audio.js';
import api from '../services/api.js';

/**
 * Project Chronos — Round 2: CHRONOS Terminal Investigation
 * Displays timeline audit logs and evidence convergence for Round 3.
 */
export default function Round2({ team, onAdvanceToRound3 }) {
  const [files, setFiles] = useState([]);
  const [activeFileId, setActiveFileId] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadFiles() {
      try {
        setLoading(true);
        const res = await api.getRound2Files(team?.team_id);
        const fileList = Array.isArray(res) ? res : (res?.files || res?.data || []);
        setFiles(fileList);
        if (fileList.length > 0) {
          setActiveFileId(fileList[0].file_id);
        }
      } catch (err) {
        console.error('Failed to load Round 2 files:', err);
      } finally {
        setLoading(false);
      }
    }
    loadFiles();
  }, [team?.team_id]);

  const activeFile = files.find((f) => f.file_id === activeFileId) || files[0];

  const handleSelectFile = (fileId) => {
    soundFx.playKeystroke();
    setActiveFileId(fileId);
  };

  const handleProceed = () => {
    soundFx.playAccessGranted();
    if (onAdvanceToRound3) {
      onAdvanceToRound3();
    }
  };

  return (
    <div className="relative min-h-[calc(100vh-2.5rem)] flex flex-col items-center justify-center p-3 sm:p-5 lg:p-6">
      <div className="absolute inset-0 cyber-grid opacity-30 pointer-events-none" />
      <div className="absolute inset-0 bg-radial from-transparent via-[#05070c]/85 to-[#05070c] pointer-events-none" />

      <div className="relative w-full max-w-5xl z-10 space-y-5 my-auto">
        {/* Header Bar */}
        <div className="bg-[#070c18]/95 border border-cyan-800/60 rounded-2xl p-5 sm:p-6 shadow-[0_0_40px_rgba(6,182,212,0.15)] backdrop-blur-xl">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-b border-cyan-900/50 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-cyan-950/80 border border-cyan-700/80 text-cyan-300">
                <Terminal className="w-6 h-6 text-cyan-400" />
              </div>
              <div>
                <span className="text-[11px] font-mono uppercase tracking-[0.25em] text-slate-400">
                  SECTOR INVESTIGATION MATRIX
                </span>
                <h2 className="text-2xl sm:text-3xl font-extrabold font-tech text-cyan-300 tracking-wide">
                  ROUND 2 // <span className="text-pink-400">CHRONOS TERMINAL</span>
                </h2>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-lg bg-emerald-950/80 border border-emerald-700/70 text-emerald-300 text-xs font-mono font-bold tracking-wider">
                UNIT: {team?.team_name || 'ENGINEER'}
              </span>
            </div>
          </div>

          {/* Evidence Grid & Reader */}
          <div className="mt-5 grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Left Column: File Tabs */}
            <div className="space-y-2.5">
              <span className="text-xs font-mono uppercase tracking-widest text-slate-400 block px-1">
                AVAILABLE AUDIT LOGS
              </span>
              {files.map((file) => {
                const isActive = file.file_id === activeFileId;
                return (
                  <button
                    key={file.file_id}
                    onClick={() => handleSelectFile(file.file_id)}
                    className={`w-full text-left p-3.5 rounded-xl border transition cursor-pointer flex items-center justify-between ${
                      isActive
                        ? 'bg-cyan-950/80 border-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.3)] text-white'
                        : 'bg-[#03060f]/80 border-cyan-900/40 hover:border-cyan-700 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <FileText className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                      <div>
                        <div className="font-mono font-bold text-xs uppercase tracking-wider text-cyan-300">
                          {file.project_name || file.file_id}
                        </div>
                        <div className="text-[11px] font-mono text-slate-400">{file.filename}</div>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-black/50 border border-cyan-900/60 text-slate-400">
                      {file.timeline_tag || 'LOG'}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Right 2 Columns: Terminal Content Preview */}
            <div className="lg:col-span-2 bg-[#03060f]/95 border border-cyan-900/70 rounded-xl p-4 sm:p-5 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between border-b border-cyan-950 pb-2 mb-3">
                  <span className="text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <Database className="w-3.5 h-3.5 text-cyan-400" />
                    DECRYPTED BUFFER: {activeFile?.filename || 'audit_log.txt'}
                  </span>
                  <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/60">
                    STATUS: VERIFIED
                  </span>
                </div>
                <pre className="font-mono text-xs sm:text-sm text-slate-300 whitespace-pre-wrap leading-relaxed max-h-[300px] overflow-y-auto p-3 bg-black/60 rounded-lg border border-cyan-950">
                  {loading ? 'Retrieving forensic packets...' : activeFile?.content_text || 'No data stream available.'}
                </pre>
              </div>

              <div className="pt-2 border-t border-cyan-950">
                <button
                  onClick={handleProceed}
                  className="w-full py-3.5 px-6 rounded-xl font-tech font-bold text-base tracking-widest uppercase transition-all duration-300 text-slate-950 bg-gradient-to-r from-pink-500 via-cyan-400 to-emerald-400 hover:from-pink-400 hover:to-emerald-300 shadow-[0_0_25px_rgba(6,182,212,0.4)] hover:shadow-[0_0_40px_rgba(6,182,212,0.7)] flex items-center justify-center gap-2 cursor-pointer"
                >
                  <span>ADVANCE TO ROUND 3: FINAL ACCUSATION</span>
                  <ArrowRight className="w-5 h-5 text-slate-950" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="text-xs font-mono text-slate-500 text-center">
          Project Chronos Security Classification: Level-4 Forensic Authority
        </div>
      </div>
    </div>
  );
}
