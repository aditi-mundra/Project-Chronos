import React, { useState, useEffect } from 'react';
import { Users, RotateCcw } from 'lucide-react';
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
    <div className="space-y-4 font-space text-[#F5F0FF]">
      <div className="flex items-center justify-between pb-3 border-b border-neon-purple/20">
        <div className="flex items-center gap-2">
          <Users className="w-6 h-6 text-neon-light" />
          <h2 className="font-orbitron font-bold text-xl text-white">
            REGISTERED <span className="text-neon-purple">TEAMS</span>
          </h2>
        </div>
        <button
          onClick={fetchTeams}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-void-black border border-neon-purple/30 text-xs font-mono text-dusty-lavender hover:text-neon-light hover:border-neon-purple transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>REFRESH</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {teams.map((t) => (
          <div key={t.team_id} className="game-card p-5 border-neon-purple/25 space-y-3 bg-surface-dark hover:border-neon-purple transition-all">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-dusty-lavender">TEAM #{t.team_id}</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-neon-purple/20 border border-neon-purple/40 text-neon-light font-bold">
                {t.status}
              </span>
            </div>
            <h3 className="font-orbitron font-bold text-lg text-white">{t.team_name}</h3>
            <div className="text-xs font-mono text-dusty-lavender space-y-1">
              <div>1: {t.member_1_name} {t.member_1_prn ? `(${t.member_1_prn})` : ''}</div>
              <div>2: {t.member_2_name} {t.member_2_prn ? `(${t.member_2_prn})` : ''}</div>
            </div>
            <div className="pt-2 border-t border-neon-purple/15 flex items-center justify-between text-xs font-mono">
              <span className="text-dusty-lavender">SCORE: <strong className="text-neon-light">{t.total_score}</strong></span>
              <span className="text-dusty-lavender">STATE: <strong className="text-emerald-400">{t.current_state}</strong></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
