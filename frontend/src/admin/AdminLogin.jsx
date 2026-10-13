import React, { useState } from 'react';
import { ShieldCheck, Lock, ArrowRight, ArrowLeft } from 'lucide-react';
import { soundEngine } from '../components/AudioEngine';
import ThemeSelector from '../components/ThemeSelector';
import { api } from '../services/api';

export default function AdminLogin({ onLoginSuccess }) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const [busy, setBusy] = useState(false);

  // The password is checked by the server; nothing about it lives in this bundle.
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError('');
    try {
      await api.adminLogin(password);
      soundEngine.playPurgeConfirm();
      onLoginSuccess();
    } catch (err) {
      soundEngine.playError();
      setError(err?.status === 503
        ? 'Admin access is not configured on this server.'
        : err?.message || 'Invalid Admin Security Key.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-2.5rem)] bg-[var(--bg-primary)] flex items-center justify-center p-6 text-[var(--text-body)] font-space relative">
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
            ADMINISTRATOR <span style={{ color: 'var(--neon-primary)' }}>ACCESS</span>
          </h2>
          
          <p className="text-xs font-mono text-[var(--text-dim)] uppercase tracking-wider">
            PROJECT CHRONOS • EVENT COMMAND CENTER
          </p>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/40 text-sm text-red-200 text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5 font-mono">
          <div>
            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">
              SECURITY PASSPHRASE
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter admin password"
              className="w-full px-4 py-3.5 rounded-xl bg-black/60 border border-white/15 text-white font-mono text-base outline-none focus:border-[var(--neon-primary)] focus:ring-2 focus:ring-[var(--neon-primary)] transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={busy}
            className="w-full py-4 rounded-xl text-white font-orbitron font-bold text-sm tracking-wider transition-all flex items-center justify-center gap-2 cursor-pointer shadow-lg"
            style={{
              background: 'var(--neon-gradient)',
              boxShadow: '0 0 25px var(--neon-glow)'
            }}
          >
            <span>ACCESS CONTROL CONSOLE</span>
            <ArrowRight className="w-5 h-5 text-white" />
          </button>
        </form>
      </div>
    </div>
  );
}

