import React, { useState, useEffect } from 'react';
import { 
  Trophy, 
  Sparkles, 
  Clock, 
  CheckCircle2, 
  RotateCcw, 
  Cpu, 
  ShieldCheck, 
  Layers, 
  Flame,
  Award
} from 'lucide-react';
import { api } from '../services/api';
import { soundEngine } from '../components/AudioEngine';

/**
 * Project Chronos — Final Completion & Reveal Screen
 * Black-heavy surface with neon purple victory highlights and forensic narrative debrief.
 */
export default function Completion({ 
  teamId = 1, 
  onRestart = null 
}) {
  const [loading, setLoading] = useState(true);
  const [verdictData, setVerdictData] = useState(null);

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
      <div className="min-h-screen bg-obsidian flex flex-col items-center justify-center p-6 text-center">
        <div className="w-16 h-16 rounded-full border-4 border-neon-purple border-t-white animate-spin mb-4 glow-neon"></div>
        <p className="font-orbitron text-neon-light tracking-widest text-sm animate-pulse">
          SYNCHRONIZING TIMELINE AUDIT LEDGER...
        </p>
      </div>
    );
  }

  const teamName = verdictData?.team_name || "Temporal Engineers";
  const r1Score = verdictData?.round1_score || 0;
  const r2Score = verdictData?.round2_score || 0;
  const r3Score = verdictData?.round3_score || 0;
  const totalScore = verdictData?.total_score || (r1Score + r2Score + r3Score);
  const completedAt = verdictData?.round3_completed_at || new Date().toISOString();

  return (
    <div className="min-h-screen bg-obsidian text-[#F5F0FF] relative overflow-x-hidden font-space p-4 lg:p-12 flex flex-col items-center justify-center">
      {/* CRT Scanline Overlay */}
      <div className="fixed inset-0 crt-overlay pointer-events-none opacity-30 z-40"></div>

      {/* Atmospheric Neon Violet Glows */}
      <div className="fixed top-1/4 left-1/4 w-[500px] h-[500px] bg-neon-purple/15 rounded-full blur-[140px] pointer-events-none"></div>
      <div className="fixed bottom-1/4 right-1/4 w-[500px] h-[500px] bg-deep-violet/40 rounded-full blur-[140px] pointer-events-none"></div>

      <div className="max-w-3xl w-full game-card p-6 lg:p-10 border-neon-purple/50 shadow-neon-active relative z-10 space-y-8 animate-fadeIn bg-surface-card">
        
        {/* Top Header Badge */}
        <div className="text-center space-y-3">
          <div className="inline-flex p-4 rounded-3xl bg-neon-gradient shadow-neon-glow text-white">
            <Trophy className="w-10 h-10" />
          </div>

          <h1 className="font-orbitron font-black text-3xl lg:text-4xl text-white tracking-wider">
            MISSION <span className="text-neon-purple">CONCLUDED</span>
          </h1>
          <p className="font-mono text-xs text-dusty-lavender uppercase tracking-widest">
            PROJECT CHRONOS // TEMPORAL STABILIZATION PROTOCOL 2140
          </p>
        </div>

        {/* Team Identity Badge */}
        <div className="bg-void-black rounded-2xl p-4 border border-neon-purple/20 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-[10px] font-mono text-dusty-lavender">ENGINEERING UNIT</div>
            <div className="font-orbitron font-bold text-xl text-white">{teamName}</div>
            <div className="text-xs text-neon-light mt-0.5 font-mono">
              {verdictData?.member_1_name} & {verdictData?.member_2_name}
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1.5 rounded-xl">
            <ShieldCheck className="w-4 h-4" />
            <span>TIMELINE ANCHOR SECURED</span>
          </div>
        </div>

        {/* Total Score & Round Score Breakdown */}
        <div className="space-y-3">
          <div className="text-center bg-gradient-to-r from-void-black via-surface-dark to-void-black p-6 rounded-2xl border border-neon-purple/60 shadow-neon-glow">
            <div className="text-xs font-mono text-neon-light tracking-widest uppercase">
              CUMULATIVE EVENT SCORE
            </div>
            <div className="font-orbitron font-black text-5xl lg:text-6xl text-white my-2">
              {totalScore} <span className="text-2xl text-dusty-lavender font-normal">/ 130</span>
            </div>
            <div className="text-xs text-dusty-lavender font-mono">
              MAXIMUM POSSIBLE: 130 POINTS
            </div>
          </div>

          {/* Individual Round Breakdown */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-void-black p-3.5 rounded-xl border border-neon-purple/20 text-center">
              <div className="text-[10px] font-mono text-dusty-lavender uppercase">ROUND 1 (PUZZLE)</div>
              <div className="font-orbitron font-bold text-xl text-white mt-1">
                {r1Score} <span className="text-xs text-dusty-lavender">/ 50</span>
              </div>
            </div>

            <div className="bg-void-black p-3.5 rounded-xl border border-neon-purple/20 text-center">
              <div className="text-[10px] font-mono text-dusty-lavender uppercase">ROUND 2 (TERMINAL)</div>
              <div className="font-orbitron font-bold text-xl text-white mt-1">
                {r2Score} <span className="text-xs text-dusty-lavender">/ 50</span>
              </div>
            </div>

            <div className="bg-void-black p-3.5 rounded-xl border border-neon-purple/50 text-center bg-neon-purple/10">
              <div className="text-[10px] font-mono text-neon-light uppercase">ROUND 3 (DECISION)</div>
              <div className="font-orbitron font-bold text-xl text-neon-light mt-1">
                +{r3Score} <span className="text-xs text-neon-purple/70">/ 30</span>
              </div>
            </div>
          </div>
        </div>

        {/* Official Forensic Debrief */}
        {verdictData?.verdict_details && (
          <div className="bg-void-black rounded-2xl p-5 border border-neon-purple/25 space-y-2 text-xs leading-relaxed font-space">
            <div className="font-orbitron font-bold text-sm text-neon-light flex items-center gap-2">
              <Award className="w-4 h-4 text-neon-purple" />
              <span>OFFICIAL FORENSIC NARRATIVE RESOLUTION</span>
            </div>
            <p className="text-dusty-lavender/90">
              {verdictData.verdict_details.narrative_summary}
            </p>
            <div className="pt-2 border-t border-neon-purple/20 flex flex-wrap items-center justify-between text-[11px] font-mono text-dusty-lavender">
              <span>TRUE CULPRIT: <strong className="text-white">{verdictData.verdict_details.true_culprit_name}</strong></span>
              <span>COMPLETED: {completedAt}</span>
            </div>
          </div>
        )}

        {/* Event Thank-you Message */}
        <div className="text-center text-xs text-dusty-lavender font-mono space-y-1">
          <p>Thank you for participating in Project Chronos — Symbitech 2026.</p>
          <p className="text-[11px] text-dusty-lavender/60">Organized by AI Club, Symbiosis Institute of Technology (SIT), Pune.</p>
        </div>

        {/* Return Button */}
        {onRestart && (
          <button
            onClick={() => {
              soundEngine.playClick();
              onRestart();
            }}
            className="w-full py-3 rounded-xl bg-surface-dark border border-neon-purple/30 hover:border-neon-purple font-orbitron font-bold text-xs text-dusty-lavender hover:text-white transition-all flex items-center justify-center gap-2"
          >
            <RotateCcw className="w-4 h-4 text-neon-purple" />
            <span>RETURN TO PORTAL LOGIN</span>
          </button>
        )}

      </div>
    </div>
  );
}
