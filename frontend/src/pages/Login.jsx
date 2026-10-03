import React, { useState } from 'react';
import { Shield, ShieldAlert, Users, ArrowRight, Sparkles, Cpu, AlertTriangle, KeyRound } from 'lucide-react';
import { api } from '../services/api';
import { soundEngine } from '../components/AudioEngine';
import ThemeSelector from '../components/ThemeSelector';
import { useTheme } from '../context/ThemeContext';

/**
 * Project Chronos — Team Registration / Login Screen
 * Large, high-readability 24" display typography with universal theme support.
 */
export default function Login({ onLoginSuccess, onOpenAdmin }) {
  const [teamName, setTeamName] = useState('');
  const [member1Name, setMember1Name] = useState('');
  const [member2Name, setMember2Name] = useState('');
  const [member1Prn, setMember1Prn] = useState('');
  const [member2Prn, setMember2Prn] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { themeConfig } = useTheme();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!teamName || !member1Name || !member2Name) {
      setError('Please provide Team Name and both Member names.');
      return;
    }

    try {
      setLoading(true);
      setError('');
      soundEngine.playClick();

      const res = await api.login({
        team_name: teamName.trim(),
        member_1_name: member1Name.trim(),
        member_2_name: member2Name.trim(),
        member_1_prn: member1Prn.trim(),
        member_2_prn: member2Prn.trim()
      });

      if (res.status === 'success') {
        soundEngine.playPurgeConfirm();
        onLoginSuccess(res);
      } else {
        setError(res.message || 'Authentication failed.');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || 'Failed to authenticate team.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-body)] relative overflow-x-hidden font-space flex flex-col items-center justify-center p-6 lg:p-12">
      {/* Scanline CRT overlay */}
      <div className="fixed inset-0 crt-overlay pointer-events-none opacity-25 z-40"></div>

      {/* Atmospheric dynamic glow */}
      <div 
        className="fixed top-1/4 left-1/3 w-[600px] h-[600px] rounded-full blur-[180px] pointer-events-none opacity-20"
        style={{ backgroundColor: 'var(--neon-primary)' }}
      ></div>

      {/* Top Right Header Controls: Theme Selector + Host Page Login */}
      <div className="fixed top-6 right-6 z-50 flex items-center gap-3">
        <ThemeSelector />
        
        {onOpenAdmin && (
          <button
            onClick={() => {
              soundEngine.playClick();
              onOpenAdmin();
            }}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-black/60 border border-white/15 hover:border-[var(--neon-primary)] text-xs font-mono font-semibold text-[var(--text-muted)] hover:text-white transition-all backdrop-blur-md hover:shadow-[0_0_15px_var(--neon-glow)]"
            title="Host / Admin Console Access"
          >
            <KeyRound className="w-4 h-4 text-[var(--neon-light)]" />
            <span className="hidden sm:inline">HOST LOGIN</span>
          </button>
        )}
      </div>

      {/* Main Registration Card */}
      <div className="max-w-xl w-full game-card p-8 lg:p-10 relative z-10 space-y-8 bg-[var(--bg-surface)]">
        
        {/* Title Header */}
        <div className="text-center space-y-3">
          <div 
            className="inline-flex p-4 rounded-2xl border shadow-lg"
            style={{ 
              backgroundColor: 'var(--theme-accent-badge-bg)', 
              borderColor: 'var(--theme-accent-badge-border)',
              boxShadow: '0 0 20px var(--neon-glow)'
            }}
          >
            <Cpu className="w-10 h-10 text-[var(--neon-light)]" />
          </div>
          
          <h1 className="font-orbitron font-black text-3xl lg:text-4xl text-white tracking-wider">
            PROJECT <span style={{ color: 'var(--neon-primary)' }}>CHRONOS</span>
          </h1>
          
          <p className="font-mono text-xs sm:text-sm text-[var(--text-dim)] uppercase tracking-widest">
            YEAR 2140 • TEMPORAL ENGINEER PORTAL
          </p>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/50 text-sm text-red-200 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form with larger 24" font sizing */}
        <form onSubmit={handleSubmit} className="space-y-6 text-sm font-mono">
          <div>
            <label className="block text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider mb-2">
              TEAM DESIGNATION (NAME) *
            </label>
            <input
              type="text"
              required
              value={teamName}
              onChange={(e) => setTeamName(e.target.value)}
              placeholder="e.g. Temporal Pioneers"
              className="w-full px-4 py-3.5 rounded-xl bg-[var(--bg-void)] border border-white/15 focus:border-[var(--neon-primary)] text-white text-base font-space outline-none transition-all focus:ring-2 focus:ring-[var(--neon-primary)]"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider mb-2">
                MEMBER 1 NAME *
              </label>
              <input
                type="text"
                required
                value={member1Name}
                onChange={(e) => setMember1Name(e.target.value)}
                placeholder="First Member"
                className="w-full px-4 py-3 rounded-xl bg-[var(--bg-void)] border border-white/15 focus:border-[var(--neon-primary)] text-white text-base font-space outline-none transition-all focus:ring-2 focus:ring-[var(--neon-primary)]"
              />
            </div>
            <div>
              <label className="block text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider mb-2">
                MEMBER 1 PRN
              </label>
              <input
                type="text"
                value={member1Prn}
                onChange={(e) => setMember1Prn(e.target.value)}
                placeholder="Optional PRN"
                className="w-full px-4 py-3 rounded-xl bg-[var(--bg-void)] border border-white/15 focus:border-[var(--neon-primary)] text-white text-base font-space outline-none transition-all focus:ring-2 focus:ring-[var(--neon-primary)]"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider mb-2">
                MEMBER 2 NAME *
              </label>
              <input
                type="text"
                required
                value={member2Name}
                onChange={(e) => setMember2Name(e.target.value)}
                placeholder="Second Member"
                className="w-full px-4 py-3 rounded-xl bg-[var(--bg-void)] border border-white/15 focus:border-[var(--neon-primary)] text-white text-base font-space outline-none transition-all focus:ring-2 focus:ring-[var(--neon-primary)]"
              />
            </div>
            <div>
              <label className="block text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider mb-2">
                MEMBER 2 PRN
              </label>
              <input
                type="text"
                value={member2Prn}
                onChange={(e) => setMember2Prn(e.target.value)}
                placeholder="Optional PRN"
                className="w-full px-4 py-3 rounded-xl bg-[var(--bg-void)] border border-white/15 focus:border-[var(--neon-primary)] text-white text-base font-space outline-none transition-all focus:ring-2 focus:ring-[var(--neon-primary)]"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 rounded-xl font-orbitron font-black text-base text-white tracking-wider hover:opacity-95 transition-all flex items-center justify-center gap-2 mt-6 cursor-pointer shadow-lg"
            style={{ 
              background: 'var(--neon-gradient)',
              boxShadow: '0 0 25px var(--neon-glow)'
            }}
          >
            {loading ? (
              <span>AUTHENTICATING WITH CHRONOS...</span>
            ) : (
              <>
                <span>ENTER CHRONOS INVESTIGATION</span>
                <ArrowRight className="w-5 h-5 text-white" />
              </>
            )}
          </button>
        </form>

        <div className="text-center pt-2">
          <span className="text-xs text-[var(--text-dim)] font-mono">
            SYMBIOSIS INSTITUTE OF TECHNOLOGY (SIT), PUNE • SYMBI-TECH 2026
          </span>
        </div>

      </div>
    </div>
  );
}

