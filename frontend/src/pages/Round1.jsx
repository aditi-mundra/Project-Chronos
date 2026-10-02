import React from 'react';
import { Layers, ArrowRight, CheckCircle2, Clock } from 'lucide-react';
import { soundEngine } from '../components/AudioEngine';

/**
 * Project Chronos — Round 1: Timeline Fragmentation
 */
export default function Round1({ teamId, onAdvanceToRound2, onDirectToRound3 }) {
  return (
    <div className="min-h-screen bg-obsidian text-[#F5F0FF] relative overflow-x-hidden font-space p-6 lg:p-12 flex flex-col items-center justify-center">
      <div className="fixed inset-0 crt-overlay pointer-events-none opacity-30 z-40"></div>
      
      <div className="max-w-2xl w-full game-card p-8 border-neon-purple/40 space-y-6 text-center relative z-10 bg-surface-card shadow-neon-active">
        <div className="inline-flex p-3 rounded-2xl bg-neon-purple/20 text-neon-light border border-neon-purple/50 glow-neon">
          <Layers className="w-8 h-8" />
        </div>

        <h1 className="font-orbitron font-black text-2xl lg:text-3xl text-white tracking-wide">
          ROUND 1: <span className="text-neon-purple">TIMELINE FRAGMENTATION</span>
        </h1>
        
        <p className="text-xs font-mono text-dusty-lavender uppercase tracking-widest">
          STATUS: COMPLETED & VERIFIED // CODE: CHRONOS-42
        </p>

        <div className="bg-void-black p-4 rounded-xl border border-neon-purple/20 text-xs text-dusty-lavender leading-relaxed text-left space-y-2">
          <div className="text-neon-light font-bold font-mono">RECONSTRUCTED TIMELINE CLUE:</div>
          <p className="italic text-white/90">
            "The timeline was not broken at the point of failure. Find the system that changed first."
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          {onAdvanceToRound2 && (
            <button
              onClick={() => {
                soundEngine.playClick();
                onAdvanceToRound2();
              }}
              className="flex-1 py-3.5 rounded-xl bg-surface-dark border border-neon-purple/40 font-orbitron font-bold text-xs text-neon-light tracking-wider hover:bg-neon-purple hover:text-white transition-all flex items-center justify-center gap-2 glow-neon-subtle"
            >
              <span>PROCEED TO ROUND 2</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}

          {onDirectToRound3 && (
            <button
              onClick={() => {
                soundEngine.playClick();
                onDirectToRound3();
              }}
              className="flex-1 py-3.5 rounded-xl bg-neon-gradient font-orbitron font-bold text-xs text-white tracking-wider hover:opacity-95 transition-all shadow-neon-glow flex items-center justify-center gap-2"
            >
              <span>ADVANCE TO ROUND 3 (FINAL DECISION)</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
