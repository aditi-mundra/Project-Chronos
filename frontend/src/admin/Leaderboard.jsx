import React, { useState, useEffect, useMemo } from 'react';
import { Trophy, Download, RotateCcw, Search, Medal, CheckCircle2, Clock } from 'lucide-react';
import { soundEngine } from '../components/AudioEngine';
import { api } from '../services/api';

export default function Leaderboard() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      const res = await api.getAdminLeaderboard();
      if (res.leaderboard) {
        setLeaderboard(res.leaderboard);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
    const interval = setInterval(fetchLeaderboard, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleExportCsv = () => {
    soundEngine.playClick();
    window.location.href = api.getExportCsvUrl();
  };

  const filteredLeaderboard = useMemo(() => {
    if (!searchQuery.trim()) return leaderboard;
    const q = searchQuery.toLowerCase();
    return leaderboard.filter(t => 
      t.team_name.toLowerCase().includes(q) ||
      (t.member_1_name && t.member_1_name.toLowerCase().includes(q)) ||
      (t.member_2_name && t.member_2_name.toLowerCase().includes(q)) ||
      (t.member_1_prn && t.member_1_prn.toLowerCase().includes(q)) ||
      (t.member_2_prn && t.member_2_prn.toLowerCase().includes(q))
    );
  }, [leaderboard, searchQuery]);

  return (
    <div className="space-y-6 font-space text-[var(--text-body)]">
      
      {/* Top Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-white/15">
        <div className="flex items-center gap-3">
          <Trophy className="w-7 h-7 text-[var(--neon-light)]" />
          <div>
            <h2 className="font-orbitron font-black text-2xl text-white">
              MASTER LEADERBOARD
            </h2>
            <p className="text-sm font-mono text-[var(--text-muted)]">
              Ranked by cumulative points & completion timestamps (Auto-refresh: 10s)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-4 h-4 text-[var(--text-dim)] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search team or PRN..."
              className="pl-9 pr-4 py-2.5 rounded-xl bg-black/60 border border-white/15 text-sm text-white font-mono focus:border-[var(--neon-primary)] outline-none w-56 sm:w-64"
            />
          </div>

          <button
            onClick={() => {
              soundEngine.playClick();
              fetchLeaderboard();
            }}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 border border-white/15 text-sm font-mono text-[var(--text-muted)] hover:text-white hover:border-[var(--neon-primary)] transition-all cursor-pointer"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleExportCsv}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-orbitron font-bold text-sm text-white tracking-wider transition-all shadow-lg cursor-pointer"
            style={{
              background: 'var(--neon-gradient)',
              boxShadow: '0 0 20px var(--neon-glow)'
            }}
          >
            <Download className="w-4 h-4" />
            <span>EXPORT CSV</span>
          </button>
        </div>
      </div>

      {loading && leaderboard.length === 0 ? (
        <div className="text-center py-16 text-[var(--text-muted)] font-mono text-sm">
          Loading leaderboard records from SQLite ledger...
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-white/10">
          <table className="w-full text-left border-collapse font-mono text-sm">
            <thead>
              <tr className="bg-black/60 border-b border-white/15 text-[var(--text-dim)] uppercase text-xs">
                <th className="p-4">Rank</th>
                <th className="p-4">Team Designation</th>
                <th className="p-4">Engineers</th>
                <th className="p-4 text-center">R1</th>
                <th className="p-4 text-center">R2</th>
                <th className="p-4 text-center">R3</th>
                <th className="p-4 text-center text-white font-bold">Total Score</th>
                <th className="p-4 text-center">Completed Time</th>
                <th className="p-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredLeaderboard.map((team, idx) => {
                const isGold = idx === 0;
                const isSilver = idx === 1;
                const isBronze = idx === 2;

                return (
                  <tr 
                    key={team.team_id} 
                    className={`transition-all hover:bg-white/[0.03] ${
                      isGold ? 'bg-amber-500/[0.04]' : ''
                    }`}
                  >
                    {/* Rank */}
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        {isGold && <span className="text-lg">🥇</span>}
                        {isSilver && <span className="text-lg">🥈</span>}
                        {isBronze && <span className="text-lg">🥉</span>}
                        <span className={`font-orbitron font-black text-base ${
                          isGold ? 'text-amber-400' : isSilver ? 'text-slate-300' : isBronze ? 'text-amber-600' : 'text-[var(--neon-light)]'
                        }`}>
                          #{idx + 1}
                        </span>
                      </div>
                    </td>

                    {/* Team Name */}
                    <td className="p-4">
                      <div className="font-space font-bold text-base text-white">
                        {team.team_name}
                      </div>
                      <div className="text-xs text-[var(--text-dim)] font-mono mt-0.5">
                        ID: #{team.team_id}
                      </div>
                    </td>

                    {/* Members */}
                    <td className="p-4 text-sm text-[var(--text-muted)] font-space">
                      <div>1: <strong className="text-white">{team.member_1_name}</strong> {team.member_1_prn && <span className="text-xs text-[var(--text-dim)] font-mono">({team.member_1_prn})</span>}</div>
                      <div>2: <strong className="text-white">{team.member_2_name}</strong> {team.member_2_prn && <span className="text-xs text-[var(--text-dim)] font-mono">({team.member_2_prn})</span>}</div>
                    </td>

                    {/* Round Scores */}
                    <td className="p-4 text-center font-orbitron text-white text-base">
                      {team.round1_score} <span className="text-xs text-[var(--text-dim)]">/50</span>
                    </td>
                    <td className="p-4 text-center font-orbitron text-white text-base">
                      {team.round2_score} <span className="text-xs text-[var(--text-dim)]">/50</span>
                    </td>
                    <td className="p-4 text-center font-orbitron font-bold text-base" style={{ color: 'var(--neon-light)' }}>
                      +{team.round3_score} <span className="text-xs text-[var(--text-dim)]">/30</span>
                    </td>

                    {/* Total Score */}
                    <td className="p-4 text-center">
                      <div className="font-orbitron font-black text-2xl text-emerald-400">
                        {team.total_score}
                      </div>
                      <div className="w-24 bg-black/60 rounded-full h-1.5 mx-auto mt-1 border border-white/10 overflow-hidden">
                        <div 
                          className="h-full bg-emerald-400 rounded-full"
                          style={{ width: `${Math.min(100, Math.round(((team.total_score || 0) / 130) * 100))}%` }}
                        ></div>
                      </div>
                    </td>

                    {/* Completed Time */}
                    <td className="p-4 text-center text-xs text-[var(--text-dim)]">
                      {team.round3_completed_at ? (
                        <span className="font-mono text-white bg-black/50 px-2.5 py-1 rounded-md border border-white/10">
                          {team.round3_completed_at.slice(11, 19)} UTC
                        </span>
                      ) : (
                        <span className="text-[var(--text-dim)]">In Progress</span>
                      )}
                    </td>

                    {/* Status Badge */}
                    <td className="p-4 text-right">
                      <span 
                        className="px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-wider border inline-block"
                        style={{
                          backgroundColor: team.current_state === 'COMPLETED' ? 'rgba(16, 185, 129, 0.15)' : 'var(--theme-accent-badge-bg)',
                          borderColor: team.current_state === 'COMPLETED' ? 'rgba(16, 185, 129, 0.4)' : 'var(--theme-accent-badge-border)',
                          color: team.current_state === 'COMPLETED' ? '#34D399' : 'var(--neon-light)'
                        }}
                      >
                        {team.current_state}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

