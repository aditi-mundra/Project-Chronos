import React, { useState, useEffect } from 'react';
import { 
  Trophy, 
  Sparkles, 
  CheckCircle2, 
  RotateCcw, 
  Cpu, 
  ShieldCheck, 
  Award,
  Lock,
  Radio,
  FileCheck2
} from 'lucide-react';
import { api } from '../services/api';
import { soundEngine } from '../components/AudioEngine';
import ThemeSelector from '../components/ThemeSelector';
import { useTheme } from '../context/ThemeContext';

/**
 * Project Chronos — Final Mission Debrief & Completion Screen
 * High-readability 24" layout with universal theme support.
 * Note: Final points are kept secret for closing ceremony announcement.
 */
export default function Completion({ 
  teamId = 1, 
  onRestart = null 
}) {
  const [loading, setLoading] = useState(true);
  const [verdictData, setVerdictData] = useState(null);
  const { themeConfig } = useTheme();

  useEffect(() => {
    async function loadVerdict() {
      try {
        setLoading(true);
        const res = await api.getRound3Verdict(teamId);
        if (res.status === 'success') {
          setVerdictData(res);
        }
      } catch (err) {
        console.error("Failed to load completion verdict:", err);
      } finally {
        setLoading(false);
      }
    }
    loadVerdict();
  }, [teamId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex flex-col items-center justify-center p-8 text-center">
        <div 
          className="w-16 h-16 rounded-full border-4 border-t-transparent animate-spin mb-4"
          style={{ borderColor: 'var(--neon-primary)', borderTopColor: 'transparent' }}
        ></div>
        <p className="font-orbitron text-white tracking-widest text-base animate-pulse">
          SYNCHRONIZING TIMELINE AUDIT LEDGER...
        </p>
      </div>
    );
  }

  const teamName = verdictData?.team_name || "Temporal Engineers";
  const completedAt = verdictData?.round3_completed_at || new Date().toISOString();

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

      <div className="max-w-4xl w-full game-card p-8 lg:p-12 border-white/15 relative z-10 space-y-8 bg-[var(--bg-surface)]">
        
        {/* Top Header Badge */}
        <div className="text-center space-y-4">
          <div 
            className="inline-flex p-5 rounded-3xl border shadow-xl"
            style={{ 
              backgroundColor: 'var(--theme-accent-badge-bg)', 
              borderColor: 'var(--theme-accent-badge-border)',
              boxShadow: '0 0 30px var(--neon-glow)'
            }}
          >
            <Trophy className="w-12 h-12 text-[var(--neon-light)]" />
          </div>

          <h1 className="font-orbitron font-black text-3xl lg:text-5xl text-white tracking-wider">
            MISSION <span style={{ color: 'var(--neon-primary)' }}>CONCLUDED</span>
          </h1>
          <p className="font-mono text-sm lg:text-base text-[var(--text-dim)] uppercase tracking-widest">
            PROJECT CHRONOS • TEMPORAL STABILIZATION PROTOCOL 2140
          </p>
        </div>

        {/* Team Identity Badge */}
        <div className="bg-black/60 rounded-2xl p-6 border border-white/10 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-xs font-mono text-[var(--text-dim)] uppercase tracking-wider">
              INVESTIGATING UNIT
            </div>
            <div className="font-orbitron font-black text-2xl text-white mt-1">
              {teamName}
            </div>
            <div className="text-sm text-[var(--neon-light)] mt-1 font-mono">
              {verdictData?.member_1_name} & {verdictData?.member_2_name}
            </div>
          </div>

          <div className="flex items-center gap-2.5 text-sm font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-4 py-2 rounded-xl">
            <ShieldCheck className="w-5 h-5" />
            <span className="font-bold tracking-wider">TIMELINE ANCHOR SECURED</span>
          </div>
        </div>

        {/* Official Forensic Resolution & Narrative Debrief */}
        {verdictData?.verdict_details && (
          <div className="bg-black/50 rounded-2xl p-6 lg:p-8 border border-white/10 space-y-4 text-sm leading-relaxed font-space">
            <div className="font-orbitron font-black text-lg text-white flex items-center gap-3">
              <Award className="w-6 h-6 text-[var(--neon-light)]" />
              <span>OFFICIAL FORENSIC NARRATIVE RESOLUTION</span>
            </div>
            <p className="text-base text-[var(--text-body)] leading-relaxed">
              {verdictData.verdict_details.narrative_summary}
            </p>
            <div className="pt-4 border-t border-white/10 flex flex-wrap items-center justify-between text-xs font-mono text-[var(--text-dim)] gap-2">
              <span>TRUE SECTOR: <strong className="text-white font-orbitron">{verdictData.verdict_details.true_culprit_name}</strong></span>
              <span>TIME LOGGED: {completedAt}</span>
            </div>
          </div>
        )}

        {/* Central Ledger Encrypted Notification Box */}
        <div 
          className="rounded-2xl p-6 border text-center space-y-2 bg-[var(--bg-surface-elevated)]"
          style={{ borderColor: 'var(--theme-accent-badge-border)' }}
        >
          <div className="inline-flex items-center gap-2 text-sm font-mono font-bold text-[var(--neon-light)] uppercase tracking-wider">
            <FileCheck2 className="w-4 h-4" />
            <span>VERDICT SAFELY ENCRYPTED ON MAINFRAME LEDGER</span>
          </div>
          <p className="text-sm text-[var(--text-muted)] max-w-2xl mx-auto leading-relaxed">
            Your final investigation report has been securely registered in the central event database. Final cumulative scores, round-by-round statistics, and winning podium rankings will be revealed during the event closing ceremony.
          </p>
        </div>

        {/* Footer Acknowledgement */}
        <div className="text-center text-xs text-[var(--text-dim)] font-mono space-y-1 pt-2">
          <p>Thank you for participating in Project Chronos — Symbi-Tech 2026.</p>
          <p>Organized by AI Club, Symbiosis Institute of Technology (SIT), Pune.</p>
        </div>

        {/* Return Button */}
        {onRestart && (
          <button
            onClick={() => {
              soundEngine.playClick();
              onRestart();
            }}
            className="w-full py-4 rounded-xl bg-white/5 border border-white/15 hover:border-[var(--neon-primary)] font-orbitron font-bold text-sm text-[var(--text-muted)] hover:text-white transition-all flex items-center justify-center gap-2 cursor-pointer hover:shadow-lg"
          >
            <RotateCcw className="w-4 h-4 text-[var(--neon-light)]" />
            <span>RETURN TO PORTAL LOGIN</span>
          </button>
        )}

      </div>
    </div>
  );
}

