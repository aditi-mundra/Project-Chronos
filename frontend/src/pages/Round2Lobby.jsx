import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext.jsx';
import api from '../services/api.js';
import { soundFx } from '../utils/audio.js';
import {
  Play,
  LogOut,
  ShieldCheck,
  Timer,
  Lock,
  Unlock,
  Key,
  Check,
  AlertTriangle,
  ArrowRight,
  Compass,
  History,
  Sparkles,
  Terminal,
  RefreshCw,
} from 'lucide-react';

/**
 * Transition Round (Physical Split & Sector Reconnaissance)
 * Sits between Round 1 and Round 2.
 *
 * Requirements:
 * 1. Exactly 6 teams in gameplay: 2 teams get PAST, 2 teams get PRESENT, 2 teams get FUTURE (compulsory).
 * 2. Clues dynamically extracted and presented from docs/clues.md for the assigned zone.
 * 3. Stopwatch option:
 *    - Start Stopwatch button initiates the timer.
 *    - Timer runs continuously until the security password is submitted.
 *    - Default/Placeholder password: "Chronos@123".
 *    - Entering the password stops the stopwatch and unlocks Round 2 (Chronos Terminal).
 */
export default function Round2Lobby({ result, onStartRound2, onLogout }) {
  const { team, logoutTeam } = useAuth();
  const teamId = team?.team_id ?? team?.id;

  const [transition, setTransition] = useState(null);
  const [loading, setLoading] = useState(true);
  const [stopwatchElapsed, setStopwatchElapsed] = useState(0);
  const [passwordInput, setPasswordInput] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState(null);
  const [proceeding, setProceeding] = useState(false);
  const inputRef = useRef(null);

  // Fetch transition status and clue from backend on mount
  useEffect(() => {
    if (!teamId) return undefined;
    let cancelled = false;

    const fetchInfo = async () => {
      try {
        const data = await api.getTransitionInfo(teamId);
        if (cancelled) return;
        setTransition(data);
        if (data.stopwatch_status === 'COMPLETED') {
          setStopwatchElapsed(data.elapsed_seconds || 0);
        }
      } catch (err) {
        console.error('Failed to load transition round state:', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchInfo();
    return () => { cancelled = true; };
  }, [teamId]);

  // Live stopwatch tick effect when RUNNING
  useEffect(() => {
    if (transition?.stopwatch_status !== 'RUNNING' || !transition?.start_time) return undefined;

    const startMs = new Date(transition.start_time).getTime();

    const tick = () => {
      const now = Date.now();
      const elapsed = Math.max(0, (now - startMs) / 1000);
      setStopwatchElapsed(elapsed);
    };

    tick();
    const interval = setInterval(tick, 50); // 50ms updates for smooth precision display
    return () => clearInterval(interval);
  }, [transition?.stopwatch_status, transition?.start_time]);

  const handleLogout = () => {
    soundFx.playKeystroke();
    logoutTeam();
    if (onLogout) onLogout();
  };

  const handleStartStopwatch = async () => {
    soundFx.playWhoosh();
    try {
      const updated = await api.startTransitionStopwatch(teamId);
      setTransition(updated);
      setTimeout(() => inputRef.current?.focus(), 300);
    } catch (err) {
      console.error('Error starting stopwatch:', err);
    }
  };

  const handleVerifyPassword = async (e) => {
    if (e) e.preventDefault();
    if (!passwordInput.trim() || verifying) return;

    soundFx.playKeystroke();
    setVerifying(true);
    setVerifyError(null);

    try {
      const res = await api.verifyTransitionPassword(teamId, passwordInput.trim());
      if (res.success) {
        soundFx.playAccessGranted();
        setTransition((prev) => ({
          ...prev,
          stopwatch_status: 'COMPLETED',
          is_completed: true,
          can_proceed: true,
          elapsed_seconds: res.elapsed_seconds,
        }));
        setStopwatchElapsed(res.elapsed_seconds || 0);
      } else {
        soundFx.playError();
        setVerifyError(res.error || 'Invalid password.');
      }
    } catch (err) {
      soundFx.playError();
      setVerifyError(err.message || 'Invalid password. Stopwatch continues running.');
    } finally {
      setVerifying(false);
    }
  };

  const handleProceedToRound2 = () => {
    if (proceeding) return;
    soundFx.playAccessGranted();
    setProceeding(true);
    if (onStartRound2) onStartRound2(team);
  };

  const formatStopwatch = (seconds) => {
    if (seconds == null || isNaN(seconds)) return '00:00.0';
    const totalTenths = Math.floor(seconds * 10);
    const tenths = totalTenths % 10;
    const totalSeconds = Math.floor(seconds);
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${tenths}`;
  };

  // Zone specific styling metadata
  const zoneConfig = {
    PAST: {
      label: 'PAST ZONE',
      subtitle: 'ARCHIVE RECONNAISSANCE // PHYSICAL RELIC RECOVERY',
      themeBadge: 'border-amber-500/60 bg-amber-950/40 text-amber-300 shadow-[0_0_20px_rgba(245,158,11,0.25)]',
      glow: 'shadow-[0_0_40px_rgba(245,158,11,0.15)]',
      icon: History,
      colorText: 'text-amber-400',
      accentBorder: 'border-amber-500/50',
    },
    PRESENT: {
      label: 'PRESENT ZONE',
      subtitle: 'ACTIVE TIMELINE RECONNAISSANCE // CORE ANOMALY DETECTION',
      themeBadge: 'border-cyan-500/60 bg-cyan-950/40 text-cyan-300 shadow-[0_0_20px_rgba(6,182,212,0.25)]',
      glow: 'shadow-[0_0_40px_rgba(6,182,212,0.15)]',
      icon: Compass,
      colorText: 'text-cyan-400',
      accentBorder: 'border-cyan-500/50',
    },
    FUTURE: {
      label: 'FUTURE ZONE',
      subtitle: 'PROJECTION RECONNAISSANCE // QUANTUM TERMINAL RECOVERY',
      themeBadge: 'border-purple-500/60 bg-purple-950/40 text-purple-300 shadow-[0_0_20px_rgba(168,85,247,0.25)]',
      glow: 'shadow-[0_0_40px_rgba(168,85,247,0.15)]',
      icon: Sparkles,
      colorText: 'text-purple-400',
      accentBorder: 'border-purple-500/50',
    },
  };

  const zone = transition?.zone?.toUpperCase() || 'PAST';
  const currentZoneMeta = zoneConfig[zone] || zoneConfig.PAST;
  const ZoneIcon = currentZoneMeta.icon;

  const isStopwatchActive = transition?.stopwatch_status === 'RUNNING';
  const isCompleted = transition?.stopwatch_status === 'COMPLETED';

  return (
    <div className="relative min-h-[calc(100vh-2.5rem)] flex items-center justify-center p-3 sm:p-5 lg:p-6 text-slate-100">
      {/* Ambience Grid & Scanline Backdrop */}
      <div className="absolute inset-0 cyber-grid opacity-30 pointer-events-none" />
      <div className="absolute inset-0 scanlines opacity-40 pointer-events-none" />
      <div className="absolute inset-0 bg-radial from-transparent via-[#05070c]/85 to-[#05070c] pointer-events-none" />

      <div className="relative w-full max-w-4xl z-10 space-y-6 my-auto">

        {/* Top Header Card */}
        <div className="bg-[#070c18]/95 border border-cyan-800/60 rounded-2xl p-5 sm:p-7 shadow-[0_0_45px_rgba(6,182,212,0.15)] backdrop-blur-xl relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-400 via-pink-500 to-purple-500 shadow-[0_0_12px_rgba(6,182,212,0.7)]" />

          {/* Callsign & Unit Header */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-b border-cyan-900/50 pb-5">
            <div>
              <div className="flex items-center gap-2">
                <span className="inline-block w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                <span className="text-xs font-mono uppercase tracking-[0.25em] text-cyan-400 font-bold">
                  STAGE TRANSITION // ROUND 1 ➔ ROUND 2
                </span>
              </div>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold font-tech text-cyan-300 tracking-wide mt-1">
                WAITING FOR AUTHENTICATION
              </h2>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs font-mono text-slate-400">UNIT:</span>
                <span className="text-sm font-mono font-bold text-cyan-300">{team?.team_name || 'TEMPORAL SQUAD'}</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleLogout}
                className="px-3.5 py-2 rounded-lg border border-rose-900/70 bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 hover:text-rose-100 text-xs sm:text-sm font-mono font-bold tracking-wider inline-flex items-center gap-1.5 transition cursor-pointer"
                title="Disconnect Unit Session"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>LOGOUT</span>
              </button>
            </div>
          </div>

          {/* Progress Stage Stepper */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 pt-4 text-xs font-mono">
            <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-500/50 text-emerald-300 flex items-center justify-between">
              <span className="flex items-center gap-1.5 font-bold">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                01. TIMELINE FRAGMENTS
              </span>
              <span className="text-[10px] bg-emerald-900/60 px-1.5 py-0.5 rounded uppercase">CLEARED</span>
            </div>
            <div className={`p-2.5 rounded-lg border flex items-center justify-between ${
              isCompleted 
                ? 'bg-emerald-950/30 border-emerald-500/50 text-emerald-300' 
                : 'bg-cyan-950/40 border-cyan-500/70 text-cyan-200 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
            }`}>
              <span className="flex items-center gap-1.5 font-bold">
                <Timer className="w-4 h-4 text-cyan-400 animate-spin" style={{ animationDuration: '6s' }} />
                02. WAITING FOR AUTHENTICATION
              </span>
              <span className="text-[10px] bg-cyan-900/60 px-1.5 py-0.5 rounded uppercase">
                {isCompleted ? 'COMPLETED' : 'IN PROGRESS'}
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-[#03060f]/60 border border-slate-800 text-slate-500 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Terminal className="w-4 h-4 text-slate-600" />
                03. CHRONOS TERMINAL
              </span>
              <span className="text-[10px] bg-slate-900 px-1.5 py-0.5 rounded uppercase">
                {isCompleted ? 'READY' : 'LOCKED'}
              </span>
            </div>
          </div>
        </div>

        {/* Main Grid: Sector Clue Card & Stopwatch Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

          {/* Left Column: Sector Clue (7 cols) */}
          <div className="lg:col-span-7 space-y-5">

            {/* Clue Box */}
            <div className={`bg-[#070c18]/95 border ${currentZoneMeta.accentBorder} rounded-2xl p-5 sm:p-6 ${currentZoneMeta.glow} relative`}>
              
              {/* Header */}
              <div className="flex items-center gap-2.5 pb-4 border-b border-slate-800">
                <div className={`p-2 rounded-lg border ${currentZoneMeta.themeBadge}`}>
                  <ZoneIcon className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-slate-400 block">
                    SECTOR RECONNAISSANCE
                  </span>
                  <h3 className="text-xl sm:text-2xl font-bold font-tech tracking-wide text-cyan-300">
                    PHYSICAL INVESTIGATION
                  </h3>
                </div>
              </div>

              {/* Clue Presentation */}
              <div className="mt-5 space-y-4">
                {loading ? (
                  <div className="p-6 rounded-xl bg-black/50 border border-slate-800 text-center font-mono text-sm text-cyan-400 animate-pulse">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-cyan-400" />
                    DECODING SECTOR CLUE...
                  </div>
                ) : (
                  <div className="p-5 sm:p-6 rounded-xl bg-black/60 border border-slate-800/80 font-mono text-sm sm:text-base leading-relaxed text-slate-200 relative overflow-hidden group">
                    <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-cyan-400 via-purple-500 to-pink-500" />
                    
                    {/* Clue Text */}
                    <div className="space-y-2 pl-2 whitespace-pre-line text-sm sm:text-base font-medium text-slate-200">
                      {transition?.clue_text ||
                        'Between the dust of early gears and the neon of unborn centuries lies your target.\nSeek the space that mirrors your active reality.'}
                    </div>
                  </div>
                )}
              </div>

            </div>

          </div>

          {/* Right Column: Stopwatch & Password Gate (5 cols) */}
          <div className="lg:col-span-5 space-y-5">

            <div className="bg-[#070c18]/95 border border-purple-800/60 rounded-2xl p-5 sm:p-6 shadow-[0_0_35px_rgba(168,85,247,0.15)] relative overflow-hidden flex flex-col justify-between h-full min-h-[380px]">
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 via-cyan-400 to-purple-500" />

              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-center justify-between pb-3 border-b border-purple-900/50">
                  <div className="flex items-center gap-2 text-xs font-mono text-purple-300 font-bold uppercase tracking-wider">
                    <Timer className="w-4 h-4 text-purple-400" />
                    <span>TEMPORAL STOPWATCH</span>
                  </div>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full uppercase font-bold ${
                    isCompleted
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-600'
                      : isStopwatchActive
                      ? 'bg-cyan-950 text-cyan-300 border border-cyan-500 animate-pulse'
                      : 'bg-slate-900 text-slate-400 border border-slate-700'
                  }`}>
                    {isCompleted ? 'COMPLETED' : isStopwatchActive ? 'RUNNING' : 'STANDBY'}
                  </span>
                </div>

                {/* Digital Stopwatch Display */}
                <div className="p-5 rounded-2xl bg-black/80 border border-purple-900/70 text-center relative overflow-hidden">
                  <div className="absolute inset-0 scanlines opacity-30 pointer-events-none" />
                  
                  <span className="text-[10px] font-mono uppercase tracking-[0.25em] text-slate-500 block mb-1">
                    ELAPSED TIME
                  </span>

                  <div className={`text-4xl sm:text-5xl font-mono font-black tracking-widest ${
                    isCompleted
                      ? 'text-emerald-400 drop-shadow-[0_0_15px_rgba(16,185,129,0.7)]'
                      : isStopwatchActive
                      ? 'text-cyan-300 drop-shadow-[0_0_15px_rgba(6,182,212,0.7)]'
                      : 'text-slate-500'
                  }`}>
                    {formatStopwatch(stopwatchElapsed)}
                  </div>

                  <div className="mt-2 text-[11px] font-mono text-slate-400">
                    {isCompleted ? (
                      <span className="text-emerald-400 flex items-center justify-center gap-1 font-bold">
                        <Check className="w-3.5 h-3.5" /> RECONNAISSANCE CONCLUDED
                      </span>
                    ) : isStopwatchActive ? (
                      <span className="text-cyan-400 animate-pulse flex items-center justify-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-cyan-400" />
                        STOPWATCH RUNNING
                      </span>
                    ) : (
                      <span>STOPWATCH READY</span>
                    )}
                  </div>
                </div>

                {/* State Controls: Start Stopwatch & Password Entry */}
                {!isCompleted && (
                  <div className="space-y-4 pt-1">
                    {!isStopwatchActive && (
                      <div>
                        <button
                          onClick={handleStartStopwatch}
                          className="group relative inline-flex items-center justify-center w-full py-3.5 px-6 text-sm font-bold font-tech tracking-widest uppercase transition-all duration-300 rounded-xl text-slate-950 bg-gradient-to-r from-cyan-400 via-purple-300 to-cyan-400 hover:from-cyan-300 hover:to-purple-200 shadow-[0_0_25px_rgba(6,182,212,0.5)] hover:shadow-[0_0_40px_rgba(168,85,247,0.7)] hover:scale-[1.01] active:scale-95 border border-cyan-200 cursor-pointer"
                        >
                          <div className="flex items-center gap-2.5">
                            <Play className="w-4 h-4 text-slate-950 fill-current animate-pulse" />
                            <span>START RECON STOPWATCH</span>
                          </div>
                        </button>
                        <div className="relative my-3 flex items-center justify-center">
                          <div className="border-t border-purple-900/60 w-full" />
                          <span className="bg-[#070c18] px-2 text-[10px] font-mono text-slate-500 uppercase tracking-widest absolute">
                            OR VERIFY TOKEN
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Password Entry Gate */}
                    <form onSubmit={handleVerifyPassword} className="space-y-3">
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between">
                          <label className="text-xs font-mono font-bold text-slate-300 flex items-center gap-1.5">
                            <Key className="w-3.5 h-3.5 text-purple-400" />
                            <span>ENTER AUTHENTICATION PASSWORD</span>
                          </label>
                          <span className="text-[10px] font-mono text-cyan-400/80">
                            LIVE GOOGLE REGISTRY
                          </span>
                        </div>

                        <div className="relative">
                          <input
                            ref={inputRef}
                            type="text"
                            value={passwordInput}
                            onChange={(e) => setPasswordInput(e.target.value)}
                            placeholder="Enter sector password..."
                            className="w-full px-4 py-3 rounded-xl bg-black/90 border border-purple-500/70 text-purple-100 placeholder-slate-600 font-mono text-sm focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/30 transition tracking-wider"
                          />
                        </div>
                      </div>

                      {verifyError && (
                        <div className="p-2.5 rounded-lg bg-rose-950/60 border border-rose-500/80 text-rose-300 font-mono text-xs flex items-center gap-2 animate-shake">
                          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                          <span>{verifyError}</span>
                        </div>
                      )}

                      <button
                        type="submit"
                        disabled={verifying || !passwordInput.trim()}
                        className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-purple-600 via-pink-600 to-purple-600 hover:from-purple-500 hover:to-pink-500 text-white font-mono font-bold text-xs sm:text-sm tracking-wider uppercase transition shadow-[0_0_20px_rgba(168,85,247,0.4)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer"
                      >
                        {verifying ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            <span>VALIDATING VIA GOOGLE REGISTRY...</span>
                          </>
                        ) : (
                          <>
                            <Lock className="w-4 h-4" />
                            <span>SUBMIT & UNLOCK ROUND 2</span>
                          </>
                        )}
                      </button>
                    </form>
                  </div>
                )}

                {/* Completed State Feedback */}
                {isCompleted && (
                  <div className="p-3 rounded-xl bg-emerald-950/50 border border-emerald-500/70 text-emerald-300 font-mono text-xs flex items-center justify-center gap-2">
                    <Unlock className="w-4 h-4 text-emerald-400" />
                    <span className="font-bold">ACCESS GRANTED: SECTOR CLEARED</span>
                  </div>
                )}
              </div>

              {/* Final Proceed to Round 2 Button */}
              <div className="pt-4 border-t border-purple-900/50 mt-4">
                {isCompleted ? (
                  <button
                    onClick={handleProceedToRound2}
                    disabled={proceeding}
                    className="group relative inline-flex items-center justify-center w-full py-4 px-6 text-base sm:text-lg font-bold font-tech tracking-widest uppercase transition-all duration-300 rounded-xl text-slate-950 bg-gradient-to-r from-emerald-400 via-cyan-300 to-emerald-400 hover:from-emerald-300 hover:to-cyan-200 shadow-[0_0_35px_rgba(16,185,129,0.6)] hover:shadow-[0_0_50px_rgba(16,185,129,0.9)] hover:scale-[1.02] active:scale-95 border border-emerald-200 cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <Play className="w-5 h-5 text-slate-950 fill-current animate-pulse" />
                      <span>{proceeding ? 'INITIALIZING...' : 'PROCEED TO ROUND 2'}</span>
                      <ArrowRight className="w-5 h-5 text-slate-950" />
                    </div>
                  </button>
                ) : (
                  <div className="p-3 rounded-xl bg-black/60 border border-slate-800 text-center font-mono text-xs text-slate-500 flex items-center justify-center gap-2">
                    <Lock className="w-3.5 h-3.5 text-slate-600" />
                    <span>ROUND 2 LOCKED</span>
                  </div>
                )}
              </div>

            </div>

          </div>

        </div>

      </div>
    </div>
  );
}
