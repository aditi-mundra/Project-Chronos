import React, { useState } from 'react';
import { LayoutDashboard, Trophy, Terminal, Users, LogOut } from 'lucide-react';
import Leaderboard from './Leaderboard';
import Logs from './Logs';
import Teams from './Teams';

export default function Dashboard({ onLogout }) {
  const [activeTab, setActiveTab] = useState('leaderboard'); // 'leaderboard', 'teams', 'logs'

  return (
    <div className="min-h-screen bg-obsidian text-[#F5F0FF] font-space p-4 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <header className="game-card p-4 lg:p-6 border-neon-purple/30 flex flex-wrap items-center justify-between gap-4 bg-surface-card shadow-neon-active">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-neon-purple/20 text-neon-light border border-neon-purple/50 shadow-neon-glow">
              <LayoutDashboard className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-orbitron font-black text-xl lg:text-2xl text-white">
                CHRONOS <span className="text-neon-purple">COMMAND CENTER</span>
              </h1>
              <p className="text-xs font-mono text-dusty-lavender">
                ADMINISTRATIVE OPERATIONS // LIVE TELEMETRY
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('leaderboard')}
              className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all ${
                activeTab === 'leaderboard'
                  ? 'bg-neon-purple text-white shadow-neon-glow'
                  : 'bg-void-black text-dusty-lavender hover:text-white border border-neon-purple/20'
              }`}
            >
              LEADERBOARD
            </button>
            <button
              onClick={() => setActiveTab('teams')}
              className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all ${
                activeTab === 'teams'
                  ? 'bg-neon-purple text-white shadow-neon-glow'
                  : 'bg-void-black text-dusty-lavender hover:text-white border border-neon-purple/20'
              }`}
            >
              TEAMS
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all ${
                activeTab === 'logs'
                  ? 'bg-neon-purple text-white shadow-neon-glow'
                  : 'bg-void-black text-dusty-lavender hover:text-white border border-neon-purple/20'
              }`}
            >
              LOGS
            </button>
            {onLogout && (
              <button
                onClick={onLogout}
                className="p-2 rounded-xl bg-danger-crimson/20 border border-danger-crimson/40 text-danger-crimson hover:bg-danger-crimson/30 transition-all ml-2"
                title="Exit Admin"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        </header>

        {/* Dynamic Admin Body */}
        <main className="game-card p-6 lg:p-8 border-neon-purple/30 bg-surface-card shadow-neon-subtle">
          {activeTab === 'leaderboard' && <Leaderboard />}
          {activeTab === 'teams' && <Teams />}
          {activeTab === 'logs' && <Logs />}
        </main>

      </div>
    </div>
  );
}
