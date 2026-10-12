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
  FastForward,
  ShieldAlert,
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
  const [autoAdvancedBanner, setAutoAdvancedBanner] = useState(false);
  const [skippingAuth, setSkippingAuth] = useState(false);
  const [noAuthAdvancedBanner, setNoAuthAdvancedBanner] = useState(false);
  const [gradedResult, setGradedResult] = useState(null);
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

  // Live polling for transition round state while not completed
  useEffect(() => {
    if (!teamId || transition?.stopwatch_status === 'COMPLETED' || (transition?.transition_attempts ?? 0) >= 3) return undefined;

    const interval = setInterval(async () => {
      try {
        const fresh = await api.getTransitionInfo(teamId);
        if (fresh) {
          setTransition((prev) => {
            if (!prev) return fresh;
            const effectiveAttempts = Math.max(prev.transition_attempts ?? 0, fresh.transition_attempts ?? 0);
            const isDone = fresh.is_completed || effectiveAttempts >= 3 || fresh.stopwatch_status === 'COMPLETED';
            if (
              prev.transition_attempts !== effectiveAttempts ||
              prev.stopwatch_status !== (isDone ? 'COMPLETED' : fresh.stopwatch_status) ||
              prev.is_completed !== isDone
            ) {
              return {
                ...fresh,
                transition_attempts: effectiveAttempts,
                stopwatch_status: isDone ? 'COMPLETED' : fresh.stopwatch_status,
                is_completed: isDone,
                can_proceed: isDone,
              };
            }
            return prev;
          });
          if (fresh.is_completed || (fresh.transition_attempts ?? 0) >= 3) {
            setStopwatchElapsed(fresh.elapsed_seconds || 0);
            if (fresh.auto_advanced || (fresh.transition_attempts ?? 0) >= 3) {
              setAutoAdvancedBanner(true);
              setTimeout(() => {
                if (onStartRound2) onStartRound2(team);
              }, 2500);
            }
          }
        }
      } catch {
        // ignore background poll errors
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [teamId, transition?.stopwatch_status, transition?.transition_attempts]);

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
    // HARD BLOCK: Never allow more than 3 attempts or submission when completed
    if (!passwordInput.trim() || verifying || isCompleted || currentAttempts >= 3) return;

    soundFx.playKeystroke();
    setVerifying(true);
    setVerifyError(null);

    try {
      const res = await api.verifyTransitionPassword(teamId, passwordInput.trim());
      if (res.success) {
        if (res.auto_advanced || res.points_awarded === 0) {
          soundFx.playError();
        } else {
          soundFx.playAccessGranted();
        }
        setGradedResult(res);
        setTransition((prev) => ({
          ...prev,
          stopwatch_status: 'COMPLETED',
          is_completed: true,
          can_proceed: true,
          elapsed_seconds: res.elapsed_seconds,
          transition_score: res.points_awarded ?? 0,
          transition_attempts: res.attempts_used ?? Math.min((prev?.transition_attempts ?? 0) + 1, 3),
        }));
        setStopwatchElapsed(res.elapsed_seconds || 0);

        if (res.auto_advanced || (res.points_awarded === 0 && (res.attempts_used ?? 0) >= 3)) {
          setAutoAdvancedBanner(true);
          // Automatically advance to Round 2 after 2.5 seconds
          setTimeout(() => {
            if (onStartRound2) onStartRound2(team);
          }, 2500);
        }
      } else {
        soundFx.playError();
        setVerifyError(res.error || 'Invalid password.');
        setPasswordInput('');
        let reachedLockout = false;
        // Optimistically update attempt counter dynamically
        setTransition((prev) => {
          const nextAttempts = Math.min((prev?.transition_attempts ?? 0) + 1, 3);
          reachedLockout = nextAttempts >= 3;
          return {
            ...prev,
            transition_attempts: nextAttempts,
            attempts_remaining: Math.max(0, 3 - nextAttempts),
            ...(reachedLockout ? {
              stopwatch_status: 'COMPLETED',
              is_completed: true,
              can_proceed: true,
              transition_score: 0.0,
              auto_advanced: true
            } : {})
          };
        });
        if (reachedLockout) {
          setAutoAdvancedBanner(true);
          setTimeout(() => {
            if (onStartRound2) onStartRound2(team);
          }, 2500);
        }
        // Sync with backend without letting attempt count regress
        try {
          const fresh = await api.getTransitionInfo(teamId);
          if (fresh) {
            setTransition((prev) => {
              const safeAttempts = Math.max(prev?.transition_attempts ?? 0, fresh.transition_attempts ?? 0);
              const isDone = fresh.is_completed || safeAttempts >= 3 || fresh.stopwatch_status === 'COMPLETED';
              return {
                ...fresh,
                transition_attempts: safeAttempts,
                stopwatch_status: isDone ? 'COMPLETED' : fresh.stopwatch_status,
                is_completed: isDone,
                can_proceed: isDone,
              };
            });
          }
        } catch {
          // ignore
        }
      }
    } catch (err) {
      soundFx.playError();
      const errMsg = err.response?.data?.detail || err.message || 'Invalid password. Stopwatch continues running.';
      setVerifyError(errMsg);
      setPasswordInput('');

      // Immediately increment attempts locally so the counter updates INSTANTLY and dynamically!
      let reachedLockout = false;
      setTransition((prev) => {
        const nextAttempts = Math.min((prev?.transition_attempts ?? 0) + 1, 3);
        reachedLockout = nextAttempts >= 3;
        return {
          ...prev,
          transition_attempts: nextAttempts,
          attempts_remaining: Math.max(0, 3 - nextAttempts),
          ...(reachedLockout ? {
            stopwatch_status: 'COMPLETED',
            is_completed: true,
            can_proceed: true,
            transition_score: 0.0,
            auto_advanced: true
          } : {})
        };
      });

      if (reachedLockout) {
        setAutoAdvancedBanner(true);
        setTimeout(() => {
          if (onStartRound2) onStartRound2(team);
        }, 2500);
      }

      // Refresh attempts from backend to reconcile state without letting attempt count regress
      try {
        const fresh = await api.getTransitionInfo(teamId);
        if (fresh) {
          setTransition((prev) => {
            const safeAttempts = Math.max(prev?.transition_attempts ?? 0, fresh.transition_attempts ?? 0);
            const isDone = fresh.is_completed || safeAttempts >= 3 || fresh.stopwatch_status === 'COMPLETED';
            return {
              ...fresh,
              transition_attempts: safeAttempts,
              stopwatch_status: isDone ? 'COMPLETED' : fresh.stopwatch_status,
              is_completed: isDone,
              can_proceed: isDone,
            };
          });
          if (fresh.is_completed || (fresh.transition_attempts ?? 0) >= 3) {
            if (fresh.auto_advanced || (fresh.transition_attempts ?? 0) >= 3) {
              setAutoAdvancedBanner(true);
              setTimeout(() => {
                if (onStartRound2) onStartRound2(team);
              }, 2500);
            }
          }
        }
      } catch {
        // ignore
      }
    } finally {
      setVerifying(false);
    }
  };

  const handleSkipAuthentication = async () => {
    if (skippingAuth || isCompleted) return;
    soundFx.playKeystroke();
    setSkippingAuth(true);
    setVerifyError(null);
    try {
      const res = await api.skipTransition(teamId);
      if (res) {
        soundFx.playWhoosh();
        setGradedResult(res);
        setTransition((prev) => ({
          ...prev,
          stopwatch_status: 'COMPLETED',
          is_completed: true,
          can_proceed: true,
          elapsed_seconds: res.elapsed_seconds ?? prev?.elapsed_seconds ?? 0,
          transition_score: 0.0,
          auto_advanced: true,
        }));
        setNoAuthAdvancedBanner(true);
      }
    } catch (err) {
      console.error('Failed to advance without authentication:', err);
      setTransition((prev) => ({
        ...prev,
        stopwatch_status: 'COMPLETED',
        is_completed: true,
        can_proceed: true,
        transition_score: 0.0,
      }));
      setNoAuthAdvancedBanner(true);
    } finally {
      setSkippingAuth(false);
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

  const currentAttempts = Number(transition?.transition_attempts ?? 0);
  const isLockedOut = currentAttempts >= 3;
  const isStopwatchActive = transition?.stopwatch_status === 'RUNNING' && !isLockedOut;
  const isCompleted = transition?.stopwatch_status === 'COMPLETED' || Boolean(transition?.is_completed) || isLockedOut;

  const currentAttemptNumber = Math.min(currentAttempts + 1, 3);
  const attemptsRemaining = Math.max(0, 3 - currentAttempts);

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
                      <div className="space-y-3">
                        <button
                          onClick={handleStartStopwatch}
                          className="group relative inline-flex items-center justify-center w-full py-4 px-6 text-sm sm:text-base font-bold font-tech tracking-widest uppercase transition-all duration-300 rounded-xl text-slate-950 bg-gradient-to-r from-cyan-400 via-purple-300 to-cyan-400 hover:from-cyan-300 hover:to-purple-200 shadow-[0_0_30px_rgba(6,182,212,0.6)] hover:shadow-[0_0_45px_rgba(168,85,247,0.8)] hover:scale-[1.01] active:scale-95 border border-cyan-200 cursor-pointer"
                        >
                          <div className="flex items-center gap-2.5">
                            <Play className="w-5 h-5 text-slate-950 fill-current animate-pulse" />
                            <span>START RECON STOPWATCH</span>
                          </div>
                        </button>
                        <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-600/50 text-amber-300 font-mono text-xs flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                          <span>STOPWATCH REQUIRED // Start stopwatch above to unlock security password entry.</span>
                        </div>
                        <div className="text-center pt-1">
                          <button
                            type="button"
                            onClick={handleSkipAuthentication}
                            disabled={skippingAuth || isCompleted}
                            className="text-xs font-mono text-slate-400 hover:text-cyan-300 transition-colors underline decoration-slate-600 hover:decoration-cyan-400 cursor-pointer disabled:opacity-50 inline-flex items-center gap-1.5"
                          >
                            {skippingAuth ? (
                              <>
                                <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                                <span>ADVANCING TO ROUND 2...</span>
                              </>
                            ) : (
                              <>
                                <FastForward className="w-3.5 h-3.5 text-slate-400" />
                                <span>ADVANCE TO ROUND 2 WITHOUT AUTHENTICATION (0 PTS)</span>
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Graded Scoring Tiers Indicator (Dynamic Counter + Clean Capsule Dots) */}
                    <div className="space-y-2.5">
                      {/* Header Row: Clean, zero-wrap, structured */}
                      <div className="flex items-center justify-between text-xs font-mono pb-1">
                        <label className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5 whitespace-nowrap">
                          <Key className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                          <span>AUTHENTICATION</span>
                        </label>

                        {/* Attempt Capsule with Clean Embedded Dots */}
                        <div
                          className={`flex items-center gap-2 px-3 py-1 rounded-full border text-[11px] font-mono font-bold whitespace-nowrap shadow-sm transition-all ${
                            currentAttemptNumber === 3
                              ? 'bg-amber-950/90 border-amber-500 text-amber-300 shadow-[0_0_10px_rgba(245,158,11,0.4)] animate-pulse'
                              : 'bg-purple-950/80 border-purple-700/70 text-purple-200'
                          }`}
                        >
                          {/* 3 Clear Dot Indicators */}
                          <div className="flex items-center gap-1.5">
                            {/* Dot 1 */}
                            <span
                              className={`w-2 h-2 rounded-full transition-all duration-300 ${
                                currentAttempts >= 1
                                  ? 'bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.8)]'
                                  : currentAttemptNumber === 1
                                  ? 'bg-cyan-400 ring-2 ring-cyan-400/50 shadow-[0_0_8px_rgba(6,182,212,0.9)] animate-pulse'
                                  : 'border border-slate-600 bg-transparent'
                              }`}
                              title="Attempt 1"
                            />
                            {/* Dot 2 */}
                            <span
                              className={`w-2 h-2 rounded-full transition-all duration-300 ${
                                currentAttempts >= 2
                                  ? 'bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.8)]'
                                  : currentAttemptNumber === 2
                                  ? 'bg-cyan-400 ring-2 ring-cyan-400/50 shadow-[0_0_8px_rgba(6,182,212,0.9)] animate-pulse'
                                  : 'border border-slate-600 bg-transparent'
                              }`}
                              title="Attempt 2"
                            />
                            {/* Dot 3 */}
                            <span
                              className={`w-2 h-2 rounded-full transition-all duration-300 ${
                                currentAttempts >= 3
                                  ? 'bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.8)]'
                                  : currentAttemptNumber === 3
                                  ? 'bg-amber-400 ring-2 ring-amber-400/50 shadow-[0_0_8px_rgba(245,158,11,0.9)] animate-pulse'
                                  : 'border border-slate-600 bg-transparent'
                              }`}
                              title="Attempt 3"
                            />
                          </div>
                          <span>ATTEMPT {currentAttemptNumber} / 3</span>
                        </div>
                      </div>

                      {/* 3 Full-width score tier cards */}
                      <div className="grid grid-cols-3 gap-2 font-mono">
                        <div
                          className={`p-2 rounded-xl border text-center transition-all ${
                            currentAttempts === 0
                              ? 'bg-cyan-950/70 border-cyan-400 text-cyan-200 shadow-[0_0_12px_rgba(6,182,212,0.35)] ring-1 ring-cyan-400/60 font-bold'
                              : currentAttempts > 0
                              ? 'bg-black/40 border-slate-800 text-slate-600 line-through opacity-50'
                              : 'bg-black/50 border-slate-800 text-slate-400'
                          }`}
                        >
                          <div className="text-[9px] uppercase tracking-wider text-slate-400">1ST TRY</div>
                          <div className="text-xs sm:text-sm font-bold text-cyan-300">20 PTS</div>
                          {currentAttempts > 0 && <div className="text-[9px] text-rose-500 font-bold mt-0.5">USED</div>}
                        </div>

                        <div
                          className={`p-2 rounded-xl border text-center transition-all ${
                            currentAttempts === 1
                              ? 'bg-cyan-950/70 border-cyan-400 text-cyan-200 shadow-[0_0_12px_rgba(6,182,212,0.35)] ring-1 ring-cyan-400/60 font-bold'
                              : currentAttempts > 1
                              ? 'bg-black/40 border-slate-800 text-slate-600 line-through opacity-50'
                              : 'bg-black/50 border-slate-800 text-slate-400'
                          }`}
                        >
                          <div className="text-[9px] uppercase tracking-wider text-slate-400">2ND TRY</div>
                          <div className="text-xs sm:text-sm font-bold text-cyan-300">10 PTS</div>
                          {currentAttempts > 1 && <div className="text-[9px] text-rose-500 font-bold mt-0.5">USED</div>}
                        </div>

                        <div
                          className={`p-2 rounded-xl border text-center transition-all ${
                            currentAttempts === 2
                              ? 'bg-amber-950/80 border-amber-400 text-amber-200 shadow-[0_0_15px_rgba(245,158,11,0.4)] ring-2 ring-amber-400 font-bold animate-pulse'
                              : currentAttempts > 2
                              ? 'bg-black/40 border-slate-800 text-slate-600 line-through opacity-50'
                              : 'bg-black/50 border-slate-800 text-slate-400'
                          }`}
                        >
                          <div className="text-[9px] uppercase tracking-wider text-amber-400/90 font-bold">3RD TRY (FINAL)</div>
                          <div className="text-xs sm:text-sm font-bold text-amber-300">5 PTS</div>
                          <div className="text-[9px] text-rose-400 font-bold mt-0.5 tracking-tight">FAIL = 0 PTS</div>
                        </div>
                      </div>

                      {/* Explicit Warning for 3rd Attempt: 0 points will be given */}
                      {currentAttemptNumber === 3 && (
                        <div className="p-3.5 rounded-xl bg-amber-950/80 border border-amber-500/90 text-amber-200 font-mono text-xs flex items-start gap-2.5 shadow-[0_0_20px_rgba(245,158,11,0.3)] animate-pulse">
                          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                          <div className="space-y-1">
                            <div className="font-bold text-amber-300 uppercase tracking-wider text-[11px] flex items-center gap-2">
                              <span>FINAL ATTEMPT WARNING // 3RD TRY</span>
                              <span className="px-1.5 py-0.5 rounded bg-rose-950 border border-rose-500 text-rose-300 text-[9px] font-bold">
                                0 PTS IF FAILED
                              </span>
                            </div>
                            <p className="text-[11px] text-amber-200/95 leading-relaxed">
                              Attention: You are entering your <strong>3rd and final attempt</strong>. If this password fails, <strong className="text-rose-300 bg-rose-950/80 px-1 py-0.5 rounded border border-rose-700/60">0 POINTS WILL BE GIVEN</strong> and automatic security lockout will immediately advance your squad to Round 2!
                            </p>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Password Entry Gate */}
                    <form onSubmit={handleVerifyPassword} className="space-y-3 pt-1">
                      <div className="relative">
                        <input
                          ref={inputRef}
                          type="text"
                          value={passwordInput}
                          onChange={(e) => setPasswordInput(e.target.value)}
                          disabled={!isStopwatchActive || verifying || isCompleted || currentAttempts >= 3}
                          placeholder={
                            !isStopwatchActive
                              ? 'Start stopwatch above to unlock input...'
                              : currentAttempts >= 3
                              ? 'MAXIMUM ATTEMPTS REACHED // LOCKED'
                              : currentAttemptNumber === 3
                              ? 'FINAL ATTEMPT: Enter sector password (Fail = 0 pts)...'
                              : 'Enter sector password...'
                          }
                          className={`w-full px-4 py-3 rounded-xl bg-black/90 font-mono text-sm focus:outline-none transition tracking-wider disabled:opacity-50 disabled:cursor-not-allowed ${
                            currentAttemptNumber === 3
                              ? 'border-2 border-amber-500/80 text-amber-100 placeholder-amber-600/70 focus:border-amber-400 focus:ring-2 focus:ring-amber-500/40 shadow-[0_0_15px_rgba(245,158,11,0.2)]'
                              : 'border border-purple-500/70 text-purple-100 placeholder-slate-600 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/30'
                          }`}
                        />
                      </div>

                      {verifyError && (
                        <div className="p-2.5 rounded-lg bg-rose-950/60 border border-rose-500/80 text-rose-300 font-mono text-xs flex items-center gap-2 animate-shake">
                          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                          <span>{verifyError}</span>
                        </div>
                      )}

                      <button
                        type="submit"
                        disabled={!isStopwatchActive || verifying || !passwordInput.trim() || isCompleted || currentAttempts >= 3}
                        className={`w-full py-3.5 px-4 rounded-xl text-white font-mono font-bold text-xs sm:text-sm tracking-wider uppercase transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer ${
                          currentAttempts >= 3
                            ? 'bg-slate-800 text-slate-500'
                            : currentAttemptNumber === 3
                            ? 'bg-gradient-to-r from-amber-600 via-rose-600 to-amber-600 hover:from-amber-500 hover:to-rose-500 shadow-[0_0_25px_rgba(245,158,11,0.5)]'
                            : 'bg-gradient-to-r from-purple-600 via-pink-600 to-purple-600 hover:from-purple-500 hover:to-pink-500 shadow-[0_0_20px_rgba(168,85,247,0.4)]'
                        }`}
                      >
                        {verifying ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            <span>VALIDATING SECURITY OVERRIDE...</span>
                          </>
                        ) : !isStopwatchActive ? (
                          <>
                            <Lock className="w-4 h-4" />
                            <span>AWAITING STOPWATCH ACTIVATION</span>
                          </>
                        ) : currentAttemptNumber === 3 ? (
                          <>
                            <AlertTriangle className="w-4 h-4 text-amber-300" />
                            <span>SUBMIT FINAL ATTEMPT (5 PTS OR 0 PTS)</span>
                          </>
                        ) : (
                          <>
                            <Unlock className="w-4 h-4" />
                            <span>SUBMIT & UNLOCK ROUND 2</span>
                          </>
                        )}
                      </button>

                      <div className="pt-2 text-center">
                        <button
                          type="button"
                          onClick={handleSkipAuthentication}
                          disabled={skippingAuth || isCompleted}
                          className="text-xs font-mono text-slate-400 hover:text-cyan-300 transition-colors underline decoration-slate-600 hover:decoration-cyan-400 cursor-pointer disabled:opacity-50 inline-flex items-center gap-1.5"
                        >
                          {skippingAuth ? (
                            <>
                              <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                              <span>ADVANCING TO ROUND 2...</span>
                            </>
                          ) : (
                            <>
                              <FastForward className="w-3.5 h-3.5 text-slate-400" />
                              <span>ADVANCE WITHOUT AUTHENTICATION (0 PTS)</span>
                            </>
                          )}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Completed State Feedback & Proceed to Round 2 */}
                {isCompleted && (
                  <div className="space-y-4 pt-1">
                    {autoAdvancedBanner || (transition?.transition_score === 0 && (transition?.transition_attempts ?? 0) >= 3) ? (
                      <div className="p-4 rounded-xl bg-amber-950/60 border border-amber-500/80 text-amber-200 font-mono text-xs flex flex-col items-center justify-center gap-1.5 text-center shadow-[0_0_20px_rgba(245,158,11,0.2)]">
                        <div className="flex items-center gap-1.5 font-bold text-amber-300 text-sm">
                          <AlertTriangle className="w-4 h-4 text-amber-400" />
                          <span>3 INACCURATE ATTEMPTS</span>
                        </div>
                        <span className="text-slate-300 font-medium">
                          SECURITY BYPASS ENGAGED // ADVANCING TO ROUND 2
                        </span>
                      </div>
                    ) : noAuthAdvancedBanner || transition?.transition_score === 0 ? (
                      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-700/80 text-slate-300 font-mono text-xs flex flex-col items-center justify-center gap-1.5 text-center shadow-[0_0_20px_rgba(100,116,139,0.2)]">
                        <div className="flex items-center gap-1.5 font-bold text-slate-200 text-sm">
                          <ShieldAlert className="w-4 h-4 text-slate-400" />
                          <span>NO AUTHENTICATION PROVIDED // SECTOR BYPASS ENGAGED</span>
                        </div>
                        <span className="text-slate-400 font-medium">
                          SECURITY CLEARANCE BYPASS // PROCEED TO ROUND 2
                        </span>
                      </div>
                    ) : (
                      <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/80 text-emerald-200 font-mono text-xs flex flex-col items-center justify-center gap-1.5 text-center shadow-[0_0_20px_rgba(16,185,129,0.2)]">
                        <div className="flex items-center gap-1.5 font-bold text-emerald-300 text-sm">
                          <ShieldCheck className="w-4 h-4 text-emerald-400" />
                          <span>AUTHENTICATION VERIFIED: SECTOR CLEARED</span>
                        </div>
                      </div>
                    )}

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
