import React, { useState, useEffect } from 'react';
import { Users, RotateCcw, Shield, Clock, Hash } from 'lucide-react';
import { soundEngine } from '../components/AudioEngine';
import { api } from '../services/api';

export default function Teams() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTeams = async () => {
    try {
      setLoading(true);
      const res = await api.getAdminLeaderboard();
      if (res.leaderboard) {
        setTeams(res.leaderboard);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTeams();
  }, []);

  return (
    <div className="space-y-6 font-space text-[var(--text-body)]">
      <div className="flex items-center justify-between pb-4 border-b border-white/15">
        <div className="flex items-center gap-3">
          <Users className="w-7 h-7 text-[var(--neon-light)]" />
          <div>
            <h2 className="font-orbitron font-black text-2xl text-white">
              REGISTERED SQUADS ({teams.length})
            </h2>
            <p className="text-sm font-mono text-[var(--text-muted)]">
              Real-time directory of participating engineering units
            </p>
          </div>
        </div>
        
        <button
          onClick={() => {
            soundEngine.playClick();
            fetchTeams();
          }}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 border border-white/15 text-sm font-mono text-[var(--text-muted)] hover:text-white hover:border-[var(--neon-primary)] transition-all cursor-pointer"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {loading && teams.length === 0 ? (
        <div className="text-center py-16 text-[var(--text-muted)] font-mono text-sm">
          Loading team directory...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {teams.map((t) => (
            <div 
              key={t.team_id} 
              className="game-card p-6 border-white/15 space-y-4 bg-[var(--bg-surface)] hover:border-[var(--neon-primary)] transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[var(--text-dim)] flex items-center gap-1">
                  <Hash className="w-3.5 h-3.5" /> ID: {t.team_id}
                </span>
                <span 
                  className="text-xs font-mono px-3 py-1 rounded-lg border font-bold uppercase tracking-wider"
                  style={{
                    backgroundColor: t.current_state === 'COMPLETED' ? 'rgba(16, 185, 129, 0.15)' : 'var(--theme-accent-badge-bg)',
                    borderColor: t.current_state === 'COMPLETED' ? 'rgba(16, 185, 129, 0.4)' : 'var(--theme-accent-badge-border)',
                    color: t.current_state === 'COMPLETED' ? '#34D399' : 'var(--neon-light)'
                  }}
                >
                  {t.current_state}
                </span>
              </div>

              <h3 className="font-orbitron font-black text-xl text-white">
                {t.team_name}
              </h3>

              <div className="text-sm font-mono space-y-1.5 bg-black/50 p-4 rounded-xl border border-white/10">
                <div className="text-[var(--text-body)]">
                  1: <strong className="text-white">{t.member_1_name}</strong> {t.member_1_prn && <span className="text-xs text-[var(--text-dim)]">({t.member_1_prn})</span>}
                </div>
                <div className="text-[var(--text-body)]">
                  2: <strong className="text-white">{t.member_2_name}</strong> {t.member_2_prn && <span className="text-xs text-[var(--text-dim)]">({t.member_2_prn})</span>}
                </div>
              </div>

              <div className="pt-3 border-t border-white/10 flex items-center justify-between text-sm font-mono">
                <span className="text-[var(--text-muted)]">SCORE: <strong className="text-emerald-400 font-orbitron font-bold text-base">{t.total_score} pts</strong></span>
                <span className="text-xs text-[var(--text-dim)]">
                  {t.round3_completed_at ? `${t.round3_completed_at.slice(11, 19)} UTC` : "In Progress"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

