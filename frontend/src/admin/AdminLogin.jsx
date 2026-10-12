import React, { useState } from 'react';
import { ShieldCheck, Lock, ArrowRight, ArrowLeft } from 'lucide-react';
import { soundEngine } from '../components/AudioEngine';
import ThemeSelector from '../components/ThemeSelector';
import api from '../services/api.js';

export default function AdminLogin({ onLoginSuccess, onBack }) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const result = await api.adminLogin(password);
      sessionStorage.setItem('chronos_admin_token', result.token);
      soundEngine.playPurgeConfirm();
      onLoginSuccess();
    } catch (_) {
      setError('Invalid Security Key. Access Denied.');
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center p-6 text-[var(--text-body)] font-space relative">
      {/* Top Right Theme Selector */}
      <div className="fixed top-6 right-6 z-50">
        <ThemeSelector />
      </div>

      <div className="max-w-md w-full game-card p-8 lg:p-10 border-white/15 space-y-6 bg-[var(--bg-surface)] shadow-2xl">
        <div className="text-center space-y-3">
          <div 
            className="inline-flex p-4 rounded-2xl border shadow-lg"
            style={{ 
              backgroundColor: 'var(--theme-accent-badge-bg)', 
              borderColor: 'var(--theme-accent-badge-border)',
              boxShadow: '0 0 20px var(--neon-glow)'
            }}
          >
            <ShieldCheck className="w-8 h-8 text-[var(--neon-light)]" />
          </div>
          
          <h2 className="font-orbitron font-black text-2xl lg:text-3xl text-white">
            LEADERBOARD <span style={{ color: 'var(--neon-primary)' }}>ACCESS</span>
          </h2>
          
          <p className="text-xs font-mono text-[var(--text-dim)] uppercase tracking-wider">
            PROJECT CHRONOS • SUPERVISOR AUTHENTICATION
          </p>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/40 text-sm text-red-200 text-center font-mono">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 font-mono">
          <div>
            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">
              SECURITY PASSPHRASE
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter supervisor password"
              autoFocus
              className="w-full px-4 py-3.5 rounded-xl bg-black/60 border border-white/15 text-white font-mono text-base outline-none focus:border-[var(--neon-primary)] focus:ring-2 focus:ring-[var(--neon-primary)] transition-all"
            />
          </div>

          <button
            type="submit"
            className="w-full py-4 rounded-xl text-white font-orbitron font-bold text-sm tracking-wider transition-all flex items-center justify-center gap-2 cursor-pointer shadow-lg"
            style={{
              background: 'var(--neon-gradient)',
              boxShadow: '0 0 25px var(--neon-glow)'
            }}
          >
            <span>VIEW LEADERBOARD</span>
            <ArrowRight className="w-5 h-5 text-white" />
          </button>

          {onBack && (
            <button
              type="button"
              onClick={onBack}
              className="w-full py-3 rounded-xl border border-white/10 hover:border-cyan-500/50 text-slate-400 hover:text-white font-mono text-xs tracking-wider transition-all flex items-center justify-center gap-2 cursor-pointer bg-black/30"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>RETURN TO MISSION</span>
            </button>
          )}
        </form>
      </div>
    </div>
  );
}

