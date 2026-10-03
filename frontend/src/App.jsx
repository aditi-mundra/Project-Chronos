import { useState, useEffect, useCallback } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext.jsx';
import api from './services/api.js';
import LandingGlitch from './pages/LandingGlitch.jsx';
import CrtShutdown from './components/CrtShutdown.jsx';
import ChronosIntro from './components/ChronosIntro.jsx';
import Login from './pages/Login.jsx';
import Round1PreLobby from './pages/Round1PreLobby.jsx';
import Round1 from './pages/Round1.jsx';
import Round2Lobby from './pages/Round2Lobby.jsx';

// View order:
//  'landing'  -> Glitch title page  (START MISSION button)
//  'intro'    -> Full-screen GSAP HTML cinematic intro
//  'login'    -> Team authentication form
//  'prelobby' -> Post-login lobby: START ROUND 1 -> 5 second countdown -> Round 1
//  'round1'   -> Round 1 (timeline classification)
//  'round2lobby' -> Lobby after Round 1: PLAY ROUND 2 -> waiting state
//
// A logged-in team (session in localStorage) is routed by its server-side state on reload
// ('resuming'): READY -> prelobby, ROUND1_ACTIVE -> round1, ROUND1_COMPLETED -> round2lobby.
// It stays logged in until LOGOUT.

const LOGGED_IN_VIEWS = ['resuming', 'prelobby', 'round1', 'round2lobby'];
const PRE_ROUND_STATES = ['READY', 'LOGGED_IN'];

function AppContent() {
  const { team, logoutTeam } = useAuth();
  const [currentView, setCurrentView] = useState(() => (team ? 'resuming' : 'landing'));
  const [isCrtActive, setIsCrtActive] = useState(false);
  const [round1Result, setRound1Result] = useState(null);

  // Session ended (logout, or server says the team no longer exists) -> back to landing.
  useEffect(() => {
    if (!team && LOGGED_IN_VIEWS.includes(currentView)) {
      setCurrentView('landing');
    }
  }, [team, currentView]);

  // Put a team on the right screen for its server-side state (login and page reload).
  const routeForState = useCallback(async (teamId, state) => {
    if (state === 'ROUND1_ACTIVE') {
      setCurrentView('round1');
      return;
    }
    if (!state || PRE_ROUND_STATES.includes(state)) {
      setCurrentView('prelobby');
      return;
    }
    // Round 1 is finished: the lobby shows its result.
    try {
      const status = await api.getRound1Status(teamId);
      setRound1Result(status.result || null);
    } catch {
      setRound1Result(null);
    }
    setCurrentView('round2lobby');
  }, []);

  useEffect(() => {
    if (currentView !== 'resuming' || !team) return undefined;
    let cancelled = false;

    (async () => {
      const session = await api.getSession(team.team_id);
      if (cancelled) return;
      if (session?.notFound) return; // AuthContext ends the session; the effect above returns to landing
      await routeForState(team.team_id, session?.current_state || team.current_state);
    })();

    return () => { cancelled = true; };
  }, [currentView, team, routeForState]);

  const handleRound1Complete = useCallback((result) => {
    setRound1Result(result || null);
    setCurrentView('round2lobby');
  }, []);

  const handleStartMission = () => {
    if (isCrtActive) return;
    setIsCrtActive(true);
  };

  const handleCrtComplete = () => {
    setIsCrtActive(false);
    setCurrentView('intro');
  };

  const handleLogout = () => {
    logoutTeam();
    setRound1Result(null);
    setCurrentView('landing');
  };

  return (
    <div className="min-h-screen bg-[#05070c] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      <main className="flex-1 relative">

        {/* Black CRT chassis backdrop behind the collapsing screen */}
        {isCrtActive && (
          <div className="fixed inset-0 bg-black z-30 pointer-events-none" />
        )}

        {/* Landing page — stays mounted during the intro so it keeps its state */}
        <div
          className={isCrtActive ? 'crt-screen-collapse' : ''}
          style={{
            display:       currentView === 'landing' || currentView === 'intro' ? 'block' : 'none',
            pointerEvents: currentView === 'intro' || isCrtActive ? 'none' : 'auto',
            opacity:       currentView === 'intro' ? 0 : 1,
          }}
        >
          <LandingGlitch
            onStart={handleStartMission}
            isStarting={isCrtActive}
          />
        </div>

        {/* CRT TV shutdown transition overlay */}
        {isCrtActive && (
          <CrtShutdown onComplete={handleCrtComplete} />
        )}

        {/* GSAP cinematic intro (full-screen, fixed overlay) */}
        {currentView === 'intro' && (
          <ChronosIntro onComplete={() => setCurrentView('login')} />
        )}

        {/* Team authentication */}
        {currentView === 'login' && (
          <Login
            onLoginSuccess={(res) => routeForState(res.team_id, res.current_state)}
            onBackToLanding={() => setCurrentView('landing')}
          />
        )}

        {/* Session sync after a page reload */}
        {currentView === 'resuming' && team && (
          <div className="min-h-[calc(100vh-2.5rem)] flex items-center justify-center font-mono text-sm tracking-widest text-cyan-400 animate-pulse">
            SYNCHRONIZING SESSION...
          </div>
        )}

        {/* Post-login pre-lobby (5 second countdown, then Round 1) */}
        {currentView === 'prelobby' && team && (
          <Round1PreLobby
            onStartRound1={() => setCurrentView('round1')}
            onLogout={handleLogout}
          />
        )}

        {/* Round 1 — full-screen; the backend owns the clock, scoring and completion */}
        {currentView === 'round1' && team && (
          <Round1 onComplete={handleRound1Complete} />
        )}

        {/* Lobby after Round 1: PLAY ROUND 2 -> waiting */}
        {currentView === 'round2lobby' && team && (
          <Round2Lobby
            result={round1Result}
            onStartRound2={() => {
              // Hand-over point: the Round 2 page plugs in here (the team waits meanwhile).
            }}
            onLogout={handleLogout}
          />
        )}

      </main>

      <footer className="border-t border-slate-900 bg-[#04060c] py-2 px-4 text-center font-mono text-[10px] text-slate-600">
        PROJECT CHRONOS // THE GLITCH • TECH FEST EVENT 2140
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
