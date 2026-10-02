import React from 'react';
import { Terminal, ArrowRight, ShieldCheck, FileSearch } from 'lucide-react';
import { soundEngine } from '../components/AudioEngine';

/**
 * Project Chronos — Round 2: CHRONOS Terminal Investigation
 */
export default function Round2({ teamId, onAdvanceToRound3 }) {
  return (
    <div className="min-h-screen bg-obsidian text-[#F5F0FF] relative overflow-x-hidden font-space p-6 lg:p-12 flex flex-col items-center justify-center">
      <div className="fixed inset-0 crt-overlay pointer-events-none opacity-30 z-40"></div>

      <div className="max-w-2xl w-full game-card p-8 border-neon-purple/40 space-y-6 text-center relative z-10 bg-surface-card shadow-neon-active">
        <div className="inline-flex p-3 rounded-2xl bg-neon-purple/20 text-neon-light border border-neon-purple/50 glow-neon">
          <Terminal className="w-8 h-8" />
        </div>

        <h1 className="font-orbitron font-black text-2xl lg:text-3xl text-white tracking-wide">
          ROUND 2: <span className="text-neon-purple">CHRONOS TERMINAL</span>
        </h1>

        <p className="text-xs font-mono text-dusty-lavender uppercase tracking-widest">
          STATUS: AUDIT LOGS ANALYZED // PROJECT OMEGA DETECTED
        </p>

        <div className="grid grid-cols-3 gap-3 text-xs font-mono">
          <div className="bg-void-black p-3 rounded-xl border border-neon-purple/20">
            <div className="text-neon-light font-bold">PROJECT ALPHA</div>
            <div className="text-[10px] text-dusty-lavender">Future Audit Log</div>
          </div>
          <div className="bg-void-black p-3 rounded-xl border border-neon-purple/20">
            <div className="text-neon-light font-bold">PROJECT BETA</div>
            <div className="text-[10px] text-dusty-lavender">Incident Telemetry</div>
          </div>
          <div className="bg-void-black p-3 rounded-xl border border-neon-purple/20">
            <div className="text-neon-light font-bold">PROJECT GAMMA</div>
            <div className="text-[10px] text-dusty-lavender">Access History</div>
          </div>
        </div>

        <div className="bg-void-black p-4 rounded-xl border border-neon-purple/20 text-xs text-dusty-lavender text-left">
          <span className="text-neon-light font-bold font-mono block mb-1">EVIDENCE SYNTHESIS COMPLETE:</span>
          All audit trails, incident timestamps, and biometric tokens have converged. The core CHRONOS mainframe requires your immediate final determination.
        </div>

        <button
          onClick={() => {
            soundEngine.playPurgeConfirm();
            onAdvanceToRound3();
          }}
          className="w-full py-4 rounded-xl bg-neon-gradient font-orbitron font-black text-sm text-white tracking-wider hover:opacity-95 transition-all shadow-neon-glow flex items-center justify-center gap-2"
        >
          <span>ENTER ROUND 3: FINAL DECISION TERMINAL</span>
          <ArrowRight className="w-4 h-4 text-neon-light" />
        </button>

      </div>
    </div>
  );
}
