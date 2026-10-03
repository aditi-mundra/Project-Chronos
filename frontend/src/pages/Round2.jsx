import React from 'react';
import { Terminal, ArrowRight, ShieldCheck, FileSearch } from 'lucide-react';
import { soundEngine } from '../components/AudioEngine';
import ThemeSelector from '../components/ThemeSelector';

/**
 * Project Chronos — Round 2: CHRONOS Terminal Investigation
 */
export default function Round2({ teamId, onAdvanceToRound3 }) {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-body)] relative overflow-x-hidden font-space p-6 lg:p-12 flex flex-col items-center justify-center">
      <div className="fixed inset-0 crt-overlay pointer-events-none opacity-20 z-40"></div>

      {/* Top Right Theme Selector */}
      <div className="fixed top-6 right-6 z-50">
        <ThemeSelector />
      </div>

      <div className="max-w-3xl w-full game-card p-8 lg:p-10 border-white/15 space-y-6 text-center relative z-10 bg-[var(--bg-surface)] shadow-2xl">
        <div 
          className="inline-flex p-4 rounded-2xl border shadow-lg"
          style={{ 
            backgroundColor: 'var(--theme-accent-badge-bg)', 
            borderColor: 'var(--theme-accent-badge-border)',
            boxShadow: '0 0 20px var(--neon-glow)'
          }}
        >
          <Terminal className="w-10 h-10 text-[var(--neon-light)]" />
        </div>

        <h1 className="font-orbitron font-black text-2xl lg:text-4xl text-white tracking-wide">
          ROUND 2: <span style={{ color: 'var(--neon-primary)' }}>CHRONOS TERMINAL</span>
        </h1>

        <p className="text-xs sm:text-sm font-mono text-[var(--text-dim)] uppercase tracking-widest">
          STATUS: AUDIT LOGS ANALYZED • SECTOR CORRELATION READY
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
          <div className="bg-black/60 p-4 rounded-xl border border-white/10">
            <div className="text-white font-bold text-sm">PROJECT ALPHA</div>
            <div className="text-xs text-[var(--neon-light)] mt-1">future_audit.log</div>
          </div>
          <div className="bg-black/60 p-4 rounded-xl border border-white/10">
            <div className="text-white font-bold text-sm">PROJECT BETA</div>
            <div className="text-xs text-[var(--neon-light)] mt-1">incident_report.txt</div>
          </div>
          <div className="bg-black/60 p-4 rounded-xl border border-white/10">
            <div className="text-white font-bold text-sm">PROJECT GAMMA</div>
            <div className="text-xs text-[var(--neon-light)] mt-1">access_history.log</div>
          </div>
        </div>

        <div className="bg-black/60 p-6 rounded-2xl border border-white/10 text-sm text-[var(--text-body)] text-left leading-relaxed">
          <span className="text-[var(--neon-light)] font-bold font-mono text-xs block mb-1 uppercase tracking-wider">
            EVIDENCE SYNTHESIS COMPLETE:
          </span>
          All audit trails, incident timestamps, and biometric tokens have converged. The core CHRONOS mainframe requires your immediate final determination in Round 3.
        </div>

        <button
          onClick={() => {
            soundEngine.playPurgeConfirm();
            onAdvanceToRound3();
          }}
          className="w-full py-4 rounded-xl font-orbitron font-black text-base text-white tracking-wider hover:opacity-95 transition-all flex items-center justify-center gap-2 cursor-pointer shadow-lg"
          style={{
            background: 'var(--neon-gradient)',
            boxShadow: '0 0 25px var(--neon-glow)'
          }}
        >
          <span>ENTER ROUND 3: FINAL DECISION TERMINAL</span>
          <ArrowRight className="w-5 h-5 text-white" />
        </button>

      </div>
    </div>
  );
}

