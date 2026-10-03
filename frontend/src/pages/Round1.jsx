import React from 'react';
import { Layers, ArrowRight, CheckCircle2, Clock } from 'lucide-react';
import { soundEngine } from '../components/AudioEngine';
import ThemeSelector from '../components/ThemeSelector';

/**
 * Project Chronos — Round 1: Timeline Fragmentation
 */
export default function Round1({ teamId, onAdvanceToRound2, onDirectToRound3 }) {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-body)] relative overflow-x-hidden font-space p-6 lg:p-12 flex flex-col items-center justify-center">
      <div className="fixed inset-0 crt-overlay pointer-events-none opacity-20 z-40"></div>
      
      {/* Top Right Theme Selector */}
      <div className="fixed top-6 right-6 z-50">
        <ThemeSelector />
      </div>

      <div className="max-w-2xl w-full game-card p-8 lg:p-10 border-white/15 space-y-6 text-center relative z-10 bg-[var(--bg-surface)] shadow-2xl">
        <div 
          className="inline-flex p-4 rounded-2xl border shadow-lg"
          style={{ 
            backgroundColor: 'var(--theme-accent-badge-bg)', 
            borderColor: 'var(--theme-accent-badge-border)',
            boxShadow: '0 0 20px var(--neon-glow)'
          }}
        >
          <Layers className="w-10 h-10 text-[var(--neon-light)]" />
        </div>

        <h1 className="font-orbitron font-black text-2xl lg:text-4xl text-white tracking-wide">
          ROUND 1: <span style={{ color: 'var(--neon-primary)' }}>TIMELINE FRAGMENTATION</span>
        </h1>
        
        <p className="text-xs sm:text-sm font-mono text-[var(--text-dim)] uppercase tracking-widest">
          STATUS: COMPLETED & VERIFIED • CODE: CHRONOS-42
        </p>

        <div className="bg-black/60 p-6 rounded-2xl border border-white/10 text-sm text-[var(--text-body)] leading-relaxed text-left space-y-2">
          <div className="text-[var(--neon-light)] font-bold font-mono text-xs uppercase tracking-wider">
            RECONSTRUCTED TIMELINE CLUE:
          </div>
          <p className="italic text-white text-base">
            "The timeline was not broken at the point of failure. Find the system that changed first."
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 pt-2">
          {onAdvanceToRound2 && (
            <button
              onClick={() => {
                soundEngine.playClick();
                onAdvanceToRound2();
              }}
              className="flex-1 py-4 rounded-xl bg-white/5 border border-white/15 hover:border-[var(--neon-primary)] font-orbitron font-bold text-sm text-[var(--text-muted)] hover:text-white transition-all flex items-center justify-center gap-2 cursor-pointer"
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
              className="flex-1 py-4 rounded-xl font-orbitron font-bold text-sm text-white tracking-wider hover:opacity-95 transition-all flex items-center justify-center gap-2 cursor-pointer shadow-lg"
              style={{
                background: 'var(--neon-gradient)',
                boxShadow: '0 0 20px var(--neon-glow)'
              }}
            >
              <span>ADVANCE TO ROUND 3 (FINAL DECISION)</span>
              <ArrowRight className="w-4 h-4 text-white" />
            </button>
          )}
        </div>

      </div>
    </div>
  );
}

