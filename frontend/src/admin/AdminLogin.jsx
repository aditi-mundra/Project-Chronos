import React, { useState } from 'react';
import { ShieldCheck, Lock, ArrowRight } from 'lucide-react';

export default function AdminLogin({ onLoginSuccess }) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (password === 'chronos2140' || password === 'admin') {
      onLoginSuccess();
    } else {
      setError('Invalid Admin Security Key.');
    }
  };

  return (
    <div className="min-h-screen bg-obsidian flex items-center justify-center p-6 text-[#F5F0FF] font-space">
      <div className="max-w-md w-full game-card p-8 border-neon-purple/40 space-y-6 bg-surface-card shadow-neon-active">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-neon-purple/20 text-neon-light border border-neon-purple/50 glow-neon">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h2 className="font-orbitron font-bold text-2xl text-white">
            ADMINISTRATOR <span className="text-neon-purple">ACCESS</span>
          </h2>
          <p className="text-xs font-mono text-dusty-lavender">
            PROJECT CHRONOS // EVENT COMMAND CENTER
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-danger-crimson/20 border border-danger-crimson text-xs text-[#FCA5A5] text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-dusty-lavender mb-1">
              SECURITY PASSPHRASE
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter Admin Key (default: admin)"
              className="w-full px-4 py-3 rounded-xl bg-void-black border border-neon-purple/30 text-white font-mono text-sm outline-none focus:border-neon-purple focus:ring-1 focus:ring-neon-purple"
            />
          </div>

          <button
            type="submit"
            className="w-full py-3.5 rounded-xl bg-neon-gradient hover:opacity-95 text-white font-orbitron font-bold text-xs tracking-wider transition-all flex items-center justify-center gap-2 shadow-neon-glow"
          >
            <span>ACCESS CONTROL CONSOLE</span>
            <ArrowRight className="w-4 h-4 text-neon-light" />
          </button>
        </form>
      </div>
    </div>
  );
}
