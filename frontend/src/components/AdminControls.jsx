import { useState } from 'react';
import { 
  Zap, 
  X, 
  ChevronRight, 
  LayoutDashboard, 
  Play, 
  LogIn, 
  Hourglass, 
  Flame, 
  Terminal, 
  Target, 
  Trophy, 
  UserCheck, 
  LogOut,
  Palette,
  ExternalLink
} from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';
import { useTheme } from '../context/ThemeContext.jsx';
import { soundFx } from '../utils/audio.js';

/**
 * Temporary Admin & Developer Control Panel
 * Allows jumping across all rounds, toggling themes, and viewing the master leaderboard.
 */
export default function AdminControls({ currentView, onSelectView }) {
  const [isOpen, setIsOpen] = useState(false);
  const { team, loginTeamSession, logoutTeam } = useAuth();
  const { theme, setTheme, selectRandomTheme, availableThemes } = useTheme();

  const handleJump = (view) => {
    soundFx.playKeystroke();
    // If selecting a gameplay round and no team session is active, auto-login a mock test team
    if (!team && ['prelobby', 'round1', 'round2lobby', 'round2', 'round3', 'completion'].includes(view)) {
      loginTeamSession({
        team_id: 1,
        team_name: 'TEST-DEV-UNIT',
        member_1_name: 'Lead Engineer',
        member_2_name: 'Systems Specialist',
        member_1_prn: 'PRN-99999',
        member_2_prn: 'PRN-88888',
        current_state: 'READY'
      });
    }
    onSelectView(view);
  };

  const handleMockLogin = () => {
    soundFx.playAccessGranted();
    loginTeamSession({
      team_id: 1,
      team_name: 'TEST-DEV-UNIT',
      member_1_name: 'Lead Engineer',
      member_2_name: 'Systems Specialist',
      member_1_prn: 'PRN-99999',
      member_2_prn: 'PRN-88888',
      current_state: 'READY'
    });
  };

  const handleClearSession = () => {
    soundFx.playError();
    logoutTeam();
    onSelectView('landing');
  };

  const cycleTheme = () => {
    soundFx.playKeystroke();
    selectRandomTheme();
  };

  const views = [
    { id: 'landing', label: '1. Landing Glitch', icon: Play },
    { id: 'intro', label: '2. Cinematic Intro', icon: Zap },
    { id: 'login', label: '3. Team Login', icon: LogIn },
    { id: 'prelobby', label: '4. Pre-Lobby Countdown', icon: Hourglass },
    { id: 'round1', label: '5. Round 1 (Classify)', icon: Flame },
    { id: 'round2lobby', label: '6. Round 2 Lobby', icon: LayoutDashboard },
    { id: 'round2', label: '7. Round 2 Terminal', icon: Terminal },
    { id: 'round3', label: '8. Round 3 Final Accusation', icon: Target },
    { id: 'completion', label: '9. Completion / Debrief', icon: Trophy },
    { id: 'leaderboard', label: '📊 Master Leaderboard', icon: Trophy },
  ];

  if (!window.location.search.includes('admin=1')) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 font-mono text-xs">
      {!isOpen ? (
        <button
          onClick={() => {
            soundFx.playWhoosh();
            setIsOpen(true);
          }}
          className="px-3.5 py-2 rounded-xl bg-purple-950/90 hover:bg-purple-900 border border-purple-500/80 text-purple-200 hover:text-white shadow-[0_0_25px_rgba(168,85,247,0.5)] flex items-center gap-2 font-bold tracking-wider cursor-pointer transition-all active:scale-95"
          title="Open Developer & Admin Round Explorer"
        >
          <Zap className="w-4 h-4 text-purple-400 animate-pulse" />
          <span>⚡ ADMIN EXPLORER</span>
        </button>
      ) : (
        <div className="bg-[#070b14]/95 border-2 border-purple-600/90 rounded-2xl p-4 sm:p-5 shadow-[0_0_50px_rgba(168,85,247,0.4)] backdrop-blur-2xl max-w-sm w-[90vw] sm:w-80 space-y-3.5 animate-in fade-in slide-in-from-bottom-5">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-purple-900/60 pb-2.5">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-purple-400" />
              <span className="font-bold text-purple-300 font-tech text-sm tracking-wider">
                ADMIN ROUND EXPLORER
              </span>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-purple-950/60 transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Theme Selector Controls */}
          <div className="p-2.5 rounded-xl bg-black/60 border border-purple-950 flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-[11px] text-slate-300">
              <Palette className="w-3.5 h-3.5 text-purple-400" />
              <span>THEME:</span>
            </div>
            <div className="flex items-center gap-1.5">
              <select
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                className="bg-slate-900 border border-purple-800/80 rounded-lg px-2 py-1 text-[11px] text-purple-200 outline-none cursor-pointer"
              >
                {availableThemes.map((t) => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
              <button
                onClick={cycleTheme}
                className="px-2 py-1 rounded-lg bg-purple-950 border border-purple-700 hover:bg-purple-900 text-purple-300 text-[10px] cursor-pointer"
                title="Pick Random Theme"
              >
                🎲 Random
              </button>
            </div>
          </div>

          {/* Session Status & Quick Actions */}
          <div className="p-2.5 rounded-xl bg-black/60 border border-purple-950 space-y-2">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-slate-400">SESSION:</span>
              <span className="font-bold text-cyan-300">
                {team ? `${team.team_name}` : 'NO ACTIVE TEAM'}
              </span>
            </div>
            <div className="flex gap-2">
              {!team ? (
                <button
                  onClick={handleMockLogin}
                  className="flex-1 py-1.5 px-2 rounded-lg bg-cyan-950/80 border border-cyan-700/80 hover:bg-cyan-900 text-cyan-300 font-bold text-[10px] flex items-center justify-center gap-1 cursor-pointer transition"
                >
                  <UserCheck className="w-3 h-3" />
                  <span>SET MOCK TEAM</span>
                </button>
              ) : (
                <button
                  onClick={handleClearSession}
                  className="flex-1 py-1.5 px-2 rounded-lg bg-rose-950/80 border border-rose-700/80 hover:bg-rose-900 text-rose-300 font-bold text-[10px] flex items-center justify-center gap-1 cursor-pointer transition"
                >
                  <LogOut className="w-3 h-3" />
                  <span>LOGOUT / CLEAR</span>
                </button>
              )}
            </div>
          </div>

          {/* Direct Screen Navigation */}
          <div className="space-y-1 max-h-[260px] overflow-y-auto pr-1">
            <span className="text-[10px] text-slate-500 uppercase tracking-widest block px-1">
              DIRECT SCREEN JUMP
            </span>
            {views.map((v) => {
              const Icon = v.icon;
              const isActive = currentView === v.id;
              return (
                <button
                  key={v.id}
                  onClick={() => handleJump(v.id)}
                  className={`w-full py-2 px-3 rounded-lg border text-left flex items-center justify-between transition cursor-pointer ${
                    isActive
                      ? 'bg-purple-950/90 border-purple-500 text-white font-bold shadow-[0_0_12px_rgba(168,85,247,0.3)]'
                      : 'bg-[#03060f]/60 border-purple-950/50 hover:border-purple-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-purple-400' : 'text-slate-500'}`} />
                    <span className="text-xs">{v.label}</span>
                  </div>
                  {isActive && <ChevronRight className="w-3.5 h-3.5 text-purple-400" />}
                </button>
              );
            })}
          </div>

          {/* Standalone Leaderboard HTML Link */}
          <div className="pt-1 border-t border-purple-950 text-center">
            <a
              href="/leaderboard.html"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] text-purple-300 hover:text-white inline-flex items-center gap-1 underline"
            >
              <span>Open Standalone Host Leaderboard</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
