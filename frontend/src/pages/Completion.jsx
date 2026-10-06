import { useState, useEffect } from 'react';
import { RotateCcw } from 'lucide-react';
import { soundFx } from '../utils/audio.js';
import ThemeSelector from '../components/ThemeSelector';

/**
 * Project Chronos — Final Mission Debrief & Completion Screen
 * High-readability 24" layout with universal theme support.
 * Note: Final points are kept secret for closing ceremony announcement.
 */
export default function Completion({ 
  onRestart = null 
}) {

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-body)] relative overflow-x-hidden font-space p-6 lg:p-12 flex flex-col items-center justify-center">
      {/* Scanline CRT overlay */}
      <div className="fixed inset-0 crt-overlay pointer-events-none opacity-20 z-40"></div>

      {/* Atmospheric Glow */}
      <div 
        className="fixed top-1/4 left-1/4 w-[600px] h-[600px] rounded-full blur-[180px] pointer-events-none opacity-20"
        style={{ backgroundColor: 'var(--neon-primary)' }}
      ></div>

      {/* Top Right Header Theme Selector */}
      <div className="fixed top-6 right-6 z-50">
        <ThemeSelector />
      </div>

      <div className="max-w-4xl w-full game-card p-8 lg:p-12 border-white/15 relative z-10 space-y-8 bg-[var(--bg-surface)] flex flex-col items-center justify-center text-center">
        
        <h1 className="font-orbitron font-black text-4xl lg:text-6xl text-white tracking-wider">
          THANK YOU FOR <span style={{ color: 'var(--neon-primary)' }}>PLAYING</span>
        </h1>
        
        <p className="font-mono text-sm lg:text-base text-[var(--text-dim)] uppercase tracking-widest mt-2 mb-8">
          PROJECT CHRONOS • TEMPORAL STABILIZATION PROTOCOL 2140 HAS BEEN CONCLUDED.
        </p>

        {/* 3D Video Conclusion */}
        <div className="w-full aspect-video rounded-2xl overflow-hidden border-2 border-white/20 shadow-[0_0_40px_var(--neon-glow)] relative">
          <video 
            className="w-full h-full object-cover"
            autoPlay 
            loop 
            muted 
            playsInline
          >
            <source src="https://assets.mixkit.co/videos/preview/mixkit-abstract-technology-connection-with-a-blue-and-pink-light-glow-32367-large.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
          <div className="absolute inset-0 bg-black/20 pointer-events-none"></div>
        </div>

        {/* Return Button */}
        {onRestart && (
          <button
            onClick={() => {
              soundFx.playKeystroke();
              onRestart();
            }}
            className="w-full py-4 mt-8 rounded-xl bg-white/5 border border-white/15 hover:border-[var(--neon-primary)] font-orbitron font-bold text-sm text-[var(--text-muted)] hover:text-white transition-all flex items-center justify-center gap-2 cursor-pointer hover:shadow-lg"
          >
            <RotateCcw className="w-4 h-4 text-[var(--neon-light)]" />
            <span>RETURN TO PORTAL LOGIN</span>
          </button>
        )}

      </div>
    </div>
  );
}
