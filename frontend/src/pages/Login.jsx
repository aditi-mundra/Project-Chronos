import React, { useState } from 'react';
import { Shield, Users, ArrowRight, Sparkles, Cpu, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';
import { soundEngine } from '../components/AudioEngine';

/**
 * Project Chronos — Team Registration / Login Screen
 * Black-heavy surface with neon purple glowing inputs and cyber buttons.
 */
export default function Login({ onLoginSuccess }) {
  const [teamName, setTeamName] = useState('');
  const [member1Name, setMember1Name] = useState('');
  const [member2Name, setMember2Name] = useState('');
  const [member1Prn, setMember1Prn] = useState('');
  const [member2Prn, setMember2Prn] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!teamName || !member1Name || !member2Name) {
      setError('Please fill in Team Name and Member names.');
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
        setError(res.message || 'Login failed.');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || 'Failed to authenticate team.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-obsidian text-[#F5F0FF] relative overflow-x-hidden font-space flex flex-col items-center justify-center p-4 lg:p-8">
      <div className="fixed inset-0 crt-overlay pointer-events-none opacity-30 z-40"></div>

      <div className="fixed top-1/4 left-1/3 w-[500px] h-[500px] bg-neon-purple/15 rounded-full blur-[160px] pointer-events-none"></div>

      <div className="max-w-md w-full game-card p-6 lg:p-8 border-neon-purple/40 relative z-10 space-y-6 bg-surface-card shadow-neon-active">
        
        {/* Title */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-neon-purple/20 text-neon-light border border-neon-purple/50 shadow-neon-glow">
            <Cpu className="w-8 h-8" />
          </div>
          <h1 className="font-orbitron font-black text-2xl lg:text-3xl text-white tracking-wider">
            PROJECT <span className="text-neon-purple">CHRONOS</span>
          </h1>
          <p className="font-mono text-xs text-dusty-lavender uppercase tracking-widest">
            YEAR 2140 // TEMPORAL ENGINEER PORTAL
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-danger-crimson/20 border border-danger-crimson text-xs text-[#FCA5A5] flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs font-mono">
          <div>
            <label className="block text-dusty-lavender mb-1">TEAM DESIGNATION (NAME) *</label>
            <input
              type="text"
              required
              value={teamName}
              onChange={(e) => setTeamName(e.target.value)}
              placeholder="e.g. Temporal Pioneers"
              className="w-full px-4 py-3 rounded-xl bg-void-black border border-neon-purple/30 focus:border-neon-purple text-white font-space outline-none transition-all focus:ring-1 focus:ring-neon-purple"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-dusty-lavender mb-1">MEMBER 1 NAME *</label>
              <input
                type="text"
                required
                value={member1Name}
                onChange={(e) => setMember1Name(e.target.value)}
                placeholder="First Member"
                className="w-full px-3 py-2.5 rounded-xl bg-void-black border border-neon-purple/30 focus:border-neon-purple text-white font-space outline-none text-xs transition-all focus:ring-1 focus:ring-neon-purple"
              />
            </div>
            <div>
              <label className="block text-dusty-lavender mb-1">MEMBER 1 PRN</label>
              <input
                type="text"
                value={member1Prn}
                onChange={(e) => setMember1Prn(e.target.value)}
                placeholder="Optional PRN"
                className="w-full px-3 py-2.5 rounded-xl bg-void-black border border-neon-purple/30 focus:border-neon-purple text-white font-space outline-none text-xs transition-all focus:ring-1 focus:ring-neon-purple"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-dusty-lavender mb-1">MEMBER 2 NAME *</label>
              <input
                type="text"
                required
                value={member2Name}
                onChange={(e) => setMember2Name(e.target.value)}
                placeholder="Second Member"
                className="w-full px-3 py-2.5 rounded-xl bg-void-black border border-neon-purple/30 focus:border-neon-purple text-white font-space outline-none text-xs transition-all focus:ring-1 focus:ring-neon-purple"
              />
            </div>
            <div>
              <label className="block text-dusty-lavender mb-1">MEMBER 2 PRN</label>
              <input
                type="text"
                value={member2Prn}
                onChange={(e) => setMember2Prn(e.target.value)}
                placeholder="Optional PRN"
                className="w-full px-3 py-2.5 rounded-xl bg-void-black border border-neon-purple/30 focus:border-neon-purple text-white font-space outline-none text-xs transition-all focus:ring-1 focus:ring-neon-purple"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 rounded-xl bg-neon-gradient font-orbitron font-black text-sm text-white tracking-wider hover:opacity-95 transition-all shadow-neon-glow flex items-center justify-center gap-2 mt-4"
          >
            {loading ? (
              <span>AUTHENTICATING WITH CHRONOS...</span>
            ) : (
              <>
                <span>ENTER CHRONOS INVESTIGATION</span>
                <ArrowRight className="w-4 h-4 text-neon-light" />
              </>
            )}
          </button>
        </form>

      </div>
    </div>
  );
}
