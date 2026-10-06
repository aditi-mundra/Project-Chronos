import { useState, useEffect } from 'react';
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
  FileCheck2,
  AlertCircle
} from 'lucide-react';
import api from '../services/api.js';
import { soundFx } from '../utils/audio.js';

/**
 * Project Chronos — Final Mission Debrief & Completion Screen
 * High-readability cyberpunk layout.
 * Note: Final scores and rankings are calculated on the backend and revealed during the closing awards.
 */
export default function Completion({ 
  teamId, 
  onRestart 
}) {
  const [loading, setLoading] = useState(true);
  const [verdictData, setVerdictData] = useState(null);

  useEffect(() => {
    async function loadVerdict() {
      try {
        setLoading(true);
        if (teamId) {
          const res = await api.getRound3Verdict(teamId);
          if (res.status === 'success') {
            setVerdictData(res);
          }
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
      <div className="min-h-[calc(100vh-2.5rem)] flex flex-col items-center justify-center p-6 text-center">
        <div className="w-14 h-14 rounded-full border-4 border-emerald-500 border-t-transparent animate-spin mb-4" />
        <p className="font-mono text-emerald-300 tracking-widest text-sm animate-pulse">
          SYNCHRONIZING TIMELINE AUDIT LEDGER...
        </p>
      </div>
    );
  }

  const teamName = verdictData?.team_name || "Temporal Engineers";
  const submission = verdictData?.submission || {};
  const verdictDetails = verdictData?.verdict_details || {};

  return (
    <div className="relative min-h-[calc(100vh-2.5rem)] flex flex-col items-center justify-center p-3 sm:p-5 lg:p-6">
      <div className="absolute inset-0 cyber-grid opacity-30 pointer-events-none" />
      <div className="absolute inset-0 bg-radial from-transparent via-[#05070c]/85 to-[#05070c] pointer-events-none" />

      <div className="relative w-full max-w-4xl z-10 space-y-5 my-auto text-center">
        
        {/* Main Completion Card */}
        <div className="bg-[#070c18]/95 border border-emerald-800/60 rounded-3xl p-6 sm:p-8 shadow-[0_0_50px_rgba(16,185,129,0.2)] backdrop-blur-xl space-y-6">
          
          {/* Trophy Header */}
          <div className="inline-flex p-4 rounded-2xl bg-emerald-950/80 border border-emerald-600/80 text-emerald-400 shadow-[0_0_30px_rgba(16,185,129,0.4)]">
            <Trophy className="w-12 h-12 text-emerald-300 animate-pulse" />
          </div>

          <div className="space-y-1">
            <span className="text-xs font-mono uppercase tracking-[0.3em] text-emerald-400">
              MISSION STATUS // FULLY COMMITTED
            </span>
            <h1 className="text-3xl sm:text-5xl font-black font-tech text-white tracking-wide">
              PROJECT CHRONOS <span className="text-emerald-400">COMPLETED</span>
            </h1>
            <p className="text-xs sm:text-sm font-mono text-slate-400 pt-1">
              Unit: <strong className="text-cyan-300">{teamName}</strong> • Event: TECH FEST 2140
            </p>
          </div>

          {/* Submission Summary Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left">
            <div className="p-4 rounded-xl bg-[#03060f]/90 border border-cyan-900/60 space-y-2">
              <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase font-bold tracking-wider">
                <FileCheck2 className="w-4 h-4" />
                <span>ACCUSED SUSPECT</span>
              </div>
              <div className="text-lg font-bold font-mono text-white">
                {submission.selected_candidate_name || submission.selected_candidate_id || "RECORDED"}
              </div>
              <div className="text-[11px] font-mono text-slate-400">
                Submitted at: {submission.submitted_at ? new Date(submission.submitted_at).toLocaleTimeString() : "CONFIRMED"}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#03060f]/90 border border-emerald-900/60 space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs uppercase font-bold tracking-wider">
                <ShieldCheck className="w-4 h-4" />
                <span>TIMELINE CONTINUUM</span>
              </div>
              <div className="text-lg font-bold font-mono text-emerald-300">
                STABILIZATION ENGAGED
              </div>
              <div className="text-[11px] font-mono text-slate-400">
                All rounds concluded. Awaiting leaderboard reveal.
              </div>
            </div>
          </div>

          {/* Forensic Debrief Dossier */}
          {verdictDetails.narrative_summary && (
            <div className="p-5 rounded-2xl bg-black/60 border border-cyan-950 text-left space-y-2">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 block">
                FORENSIC NARRATIVE RESOLUTION:
              </span>
              <p className="text-xs sm:text-sm font-mono text-slate-300 leading-relaxed whitespace-pre-wrap">
                {verdictDetails.narrative_summary}
              </p>
            </div>
          )}

          {/* CTA Actions */}
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => {
                soundFx.playAccessGranted();
                if (onRestart) onRestart();
              }}
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl border border-cyan-800/80 bg-cyan-950/60 hover:bg-cyan-900/60 text-cyan-300 font-mono font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition cursor-pointer"
            >
              <RotateCcw className="w-4 h-4" />
              <span>RETURN TO MAIN TERMINAL</span>
            </button>
          </div>

        </div>

        <div className="text-xs font-mono text-slate-500">
          Terminal Status: Mission Concluded • Stand by for physical awards announcement
        </div>

      </div>
    </div>
  );
}
