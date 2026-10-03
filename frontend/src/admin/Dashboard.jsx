import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Download, 
  LogOut, 
  Users, 
  Trophy, 
  Activity, 
  ShieldCheck, 
  Terminal,
  RefreshCw,
  Award,
  BarChart3,
  ArrowLeft
} from 'lucide-react';
import Leaderboard from './Leaderboard';
import Logs from './Logs';
import Teams from './Teams';
import ThemeSelector from '../components/ThemeSelector';
import { soundEngine } from '../components/AudioEngine';
import { api } from '../services/api';

export default function Dashboard({ onLogout }) {
  const [activeTab, setActiveTab] = useState('leaderboard'); // 'leaderboard', 'teams', 'logs'
  const [stats, setStats] = useState({
    totalTeams: 0,
    activeTeams: 0,
    finishedTeams: 0,
    topScore: 0,
    avgScore: 0
  });

  const fetchStats = async () => {
    try {
      const res = await api.getAdminLeaderboard();
      if (res.leaderboard) {
        const list = res.leaderboard;
        const total = list.length;
        const finished = list.filter(t => t.current_state === 'COMPLETED' || t.status === 'FINISHED').length;
        const active = total - finished;
        const scores = list.map(t => t.total_score || 0);
        const top = scores.length ? Math.max(...scores) : 0;
        const avg = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / total) : 0;

        setStats({
          totalTeams: total,
          activeTeams: active,
          finishedTeams: finished,
          topScore: top,
          avgScore: avg
        });
      }
    } catch (e) {
      console.error("Failed to fetch dashboard stats", e);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleExportCsv = () => {
    soundEngine.playClick();
    window.location.href = api.getExportCsvUrl();
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-body)] font-space p-6 lg:p-12 pb-24">
      {/* Scanline CRT overlay */}
      <div className="fixed inset-0 crt-overlay pointer-events-none opacity-20 z-40"></div>

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        
        {/* =====================================================================
            1. TOP HEADER & CONTROLS
        ====================================================================== */}
        <header className="game-card p-6 lg:p-8 border-white/15 flex flex-wrap items-center justify-between gap-6 bg-[var(--bg-surface)] shadow-2xl">
          <div className="flex items-center gap-4">
            <div 
              className="p-3.5 rounded-2xl border shadow-lg"
              style={{ 
                backgroundColor: 'var(--theme-accent-badge-bg)', 
                borderColor: 'var(--theme-accent-badge-border)',
                boxShadow: '0 0 20px var(--neon-glow)'
              }}
            >
              <LayoutDashboard className="w-8 h-8 text-[var(--neon-light)]" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="font-orbitron font-black text-2xl lg:text-3xl text-white tracking-wide">
                  CHRONOS <span style={{ color: 'var(--neon-primary)' }}>COMMAND</span>
                </h1>
                <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 font-bold">
                  LIVE TELEMETRY
                </span>
              </div>
              <p className="text-sm font-mono text-[var(--text-muted)] mt-1">
                Central Event Management & Score Consolidation System
              </p>
            </div>
          </div>

          <div className="flex items-center flex-wrap gap-3">
            <ThemeSelector />

            {/* Navigation Tabs */}
            <div className="flex items-center bg-black/60 p-1.5 rounded-xl border border-white/15 text-sm font-mono backdrop-blur-md">
              <button
                onClick={() => {
                  soundEngine.playClick();
                  setActiveTab('leaderboard');
                }}
                className={`px-4 py-2 rounded-lg transition-all cursor-pointer ${
                  activeTab === 'leaderboard'
                    ? 'text-white font-bold shadow-lg'
                    : 'text-[var(--text-muted)] hover:text-white'
                }`}
                style={{
                  background: activeTab === 'leaderboard' ? 'var(--neon-gradient)' : undefined,
                  boxShadow: activeTab === 'leaderboard' ? '0 0 15px var(--neon-glow)' : undefined
                }}
              >
                Leaderboard
              </button>
              <button
                onClick={() => {
                  soundEngine.playClick();
                  setActiveTab('teams');
                }}
                className={`px-4 py-2 rounded-lg transition-all cursor-pointer ${
                  activeTab === 'teams'
                    ? 'text-white font-bold shadow-lg'
                    : 'text-[var(--text-muted)] hover:text-white'
                }`}
                style={{
                  background: activeTab === 'teams' ? 'var(--neon-gradient)' : undefined,
                  boxShadow: activeTab === 'teams' ? '0 0 15px var(--neon-glow)' : undefined
                }}
              >
                Teams ({stats.totalTeams})
              </button>
              <button
                onClick={() => {
                  soundEngine.playClick();
                  setActiveTab('logs');
                }}
                className={`px-4 py-2 rounded-lg transition-all cursor-pointer ${
                  activeTab === 'logs'
                    ? 'text-white font-bold shadow-lg'
                    : 'text-[var(--text-muted)] hover:text-white'
                }`}
                style={{
                  background: activeTab === 'logs' ? 'var(--neon-gradient)' : undefined,
                  boxShadow: activeTab === 'logs' ? '0 0 15px var(--neon-glow)' : undefined
                }}
              >
                Audit Stream
              </button>
            </div>

            <button
              onClick={handleExportCsv}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-black/60 border border-white/15 hover:border-[var(--neon-primary)] text-sm font-mono text-[var(--text-muted)] hover:text-white transition-all cursor-pointer hover:shadow-lg backdrop-blur-md"
              title="Download Leaderboard as CSV"
            >
              <Download className="w-4 h-4 text-[var(--neon-light)]" />
              <span>Export CSV</span>
            </button>

            {onLogout && (
              <button
                onClick={() => {
                  soundEngine.playClick();
                  onLogout();
                }}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 hover:bg-red-900/60 transition-all text-sm font-mono cursor-pointer"
                title="Exit Host Console"
              >
                <LogOut className="w-4 h-4" />
                <span>Exit</span>
              </button>
            )}
          </div>
        </header>

        {/* =====================================================================
            2. LIVE EVENT KPI METRIC CARDS (24" Optimized)
        ====================================================================== */}
        <section className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="game-card p-5 border-white/10 bg-[var(--bg-surface)] space-y-1">
            <div className="flex items-center justify-between text-xs font-mono text-[var(--text-dim)] uppercase">
              <span>TOTAL TEAMS</span>
              <Users className="w-4 h-4 text-[var(--neon-light)]" />
            </div>
            <div className="font-orbitron font-black text-3xl text-white">
              {stats.totalTeams}
            </div>
          </div>

          <div className="game-card p-5 border-white/10 bg-[var(--bg-surface)] space-y-1">
            <div className="flex items-center justify-between text-xs font-mono text-[var(--text-dim)] uppercase">
              <span>ACTIVE IN RUN</span>
              <Activity className="w-4 h-4 text-amber-400" />
            </div>
            <div className="font-orbitron font-black text-3xl text-amber-400">
              {stats.activeTeams}
            </div>
          </div>

          <div className="game-card p-5 border-white/10 bg-[var(--bg-surface)] space-y-1">
            <div className="flex items-center justify-between text-xs font-mono text-[var(--text-dim)] uppercase">
              <span>CONCLUDED</span>
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="font-orbitron font-black text-3xl text-emerald-400">
              {stats.finishedTeams}
            </div>
          </div>

          <div className="game-card p-5 border-white/10 bg-[var(--bg-surface)] space-y-1">
            <div className="flex items-center justify-between text-xs font-mono text-[var(--text-dim)] uppercase">
              <span>TOP SCORE</span>
              <Trophy className="w-4 h-4 text-[var(--neon-primary)]" />
            </div>
            <div className="font-orbitron font-black text-3xl text-white">
              {stats.topScore} <span className="text-xs text-[var(--text-dim)] font-normal">/ 130</span>
            </div>
          </div>

          <div className="game-card p-5 border-white/10 bg-[var(--bg-surface)] space-y-1">
            <div className="flex items-center justify-between text-xs font-mono text-[var(--text-dim)] uppercase">
              <span>AVERAGE SCORE</span>
              <BarChart3 className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="font-orbitron font-black text-3xl text-white">
              {stats.avgScore} <span className="text-xs text-[var(--text-dim)] font-normal">pts</span>
            </div>
          </div>
        </section>

        {/* =====================================================================
            3. DYNAMIC TAB VIEW BODY
        ====================================================================== */}
        <main className="game-card p-6 lg:p-8 border-white/15 bg-[var(--bg-surface)] shadow-2xl">
          {activeTab === 'leaderboard' && <Leaderboard />}
          {activeTab === 'teams' && <Teams />}
          {activeTab === 'logs' && <Logs />}
        </main>

      </div>
    </div>
  );
}

