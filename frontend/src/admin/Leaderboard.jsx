import React, { useState, useEffect } from 'react';
import { Trophy, Clock, RotateCcw } from 'lucide-react';
import { api } from '../services/api';

export default function Leaderboard() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

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

  return (
    <div className="space-y-4 font-space text-[#F5F0FF]">
      <div className="flex items-center justify-between pb-3 border-b border-neon-purple/20">
        <div className="flex items-center gap-2">
          <Trophy className="w-6 h-6 text-neon-light" />
          <h2 className="font-orbitron font-bold text-xl text-white">
            EVENT LEADERBOARD <span className="text-neon-purple">(ADMIN)</span>
          </h2>
        </div>
        <button
          onClick={fetchLeaderboard}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-void-black border border-neon-purple/30 text-xs font-mono text-dusty-lavender hover:text-neon-light hover:border-neon-purple transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>REFRESH</span>
        </button>
      </div>

      {loading && leaderboard.length === 0 ? (
        <div className="text-center py-12 text-dusty-lavender font-mono text-xs animate-pulse">
          FETCHING LIVE LEADERBOARD TELEMETRY...
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="border-b border-neon-purple/25 text-dusty-lavender uppercase">
                <th className="p-3">Rank</th>
                <th className="p-3">Team Name</th>
                <th className="p-3">Members</th>
                <th className="p-3">R1</th>
                <th className="p-3">R2</th>
                <th className="p-3">R3</th>
                <th className="p-3 text-neon-light font-bold">Total</th>
                <th className="p-3">R3 Completed Time</th>
                <th className="p-3">State</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neon-purple/15">
              {leaderboard.map((team, idx) => (
                <tr key={team.team_id} className="hover:bg-neon-purple/10 transition-all">
                  <td className="p-3 font-orbitron font-bold text-neon-light">
                    #{idx + 1}
                  </td>
                  <td className="p-3 font-space font-bold text-white">
                    {team.team_name}
                  </td>
                  <td className="p-3 text-dusty-lavender">
                    {team.member_1_name} & {team.member_2_name}
                  </td>
                  <td className="p-3">{team.round1_score}</td>
                  <td className="p-3">{team.round2_score}</td>
                  <td className="p-3 text-neon-light font-bold">+{team.round3_score}</td>
                  <td className="p-3 font-orbitron font-bold text-emerald-400 text-sm">
                    {team.total_score}
                  </td>
                  <td className="p-3 text-dusty-lavender">
                    {team.round3_completed_at ? team.round3_completed_at.slice(11, 19) : "—"}
                  </td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded bg-neon-purple/20 border border-neon-purple/40 text-[10px] text-neon-light">
                      {team.current_state}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
