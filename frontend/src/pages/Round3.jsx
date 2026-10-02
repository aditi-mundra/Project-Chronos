import React, { useState, useEffect, useMemo } from 'react';
import { 
  ShieldAlert, 
  AlertOctagon, 
  Cpu, 
  Fingerprint, 
  CheckCircle2, 
  XCircle, 
  FileText, 
  Clock, 
  Lock, 
  Unlock, 
  Volume2, 
  VolumeX, 
  Info, 
  ExternalLink, 
  Check, 
  Sparkles,
  Layers,
  Activity,
  Terminal,
  ChevronRight,
  UserX,
  Radio,
  Zap,
  Crosshair
} from 'lucide-react';
import Timer from '../components/Timer';
import { soundEngine } from '../components/AudioEngine';
import { api } from '../services/api';

/**
 * Project Chronos — Round 3: Final Decision / Wisdom Round
 * Black-Heavy Primary UI with High-Contrast Neon Purple Accents,
 * Soft Violet Ambient Depth, Holographic Dossiers, and Emergency Lockdown.
 */
export default function Round3({ 
  teamId = 1, 
  teamName = "Temporal Engineers",
  onNavigateToCompletion = null 
}) {
  // Scenario & Game State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scenarioData, setScenarioData] = useState(null);
  const [teamInfo, setTeamInfo] = useState(null);
  const [roundStartedAt, setRoundStartedAt] = useState(null);

  // User Selections
  const [selectedCandidateId, setSelectedCandidateId] = useState(null);
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState([]);
  const [activeDossierTab, setActiveDossierTab] = useState('overview'); // overview, discrepancy, motive, alibi
  const [evidenceCategoryFilter, setEvidenceCategoryFilter] = useState('ALL');

  // UI Interactive States
  const [isAudioMuted, setIsAudioMuted] = useState(false);
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [isCinematicRevealing, setIsCinematicRevealing] = useState(false);
  const [holdProgress, setHoldProgress] = useState(0);
  const [isHolding, setIsHolding] = useState(false);
  const [showBriefingModal, setShowBriefingModal] = useState(false);

  // Load Round 3 Scenario on Mount
  useEffect(() => {
    async function loadRound3() {
      try {
        setLoading(true);
        setError(null);

        // Fetch team case from backend API
        const response = await api.startRound3(teamId);
        
        if (response.status === 'success') {
          setScenarioData(response.case);
          setRoundStartedAt(response.round3_started_at);
          setTeamInfo({
            id: response.team_id || teamId,
            name: response.team_name || teamName,
            state: response.team_state
          });

          // If already submitted (e.g. on page refresh)
          if (response.is_submitted && response.submission) {
            setSelectedCandidateId(response.submission.selected_candidate_id);
            setSelectedEvidenceIds(response.submission.selected_evidence_ids || []);
            // Fetch complete verdict reveal
            const verdictRes = await api.getRound3Verdict(teamId);
            if (verdictRes.status === 'success') {
              setSubmissionResult({
                is_correct: verdictRes.submission.is_correct,
                points_awarded: verdictRes.submission.points_awarded,
                round3_score: verdictRes.round3_score,
                total_score: verdictRes.total_score,
                completed_at: verdictRes.round3_completed_at,
                narrative_summary: verdictRes.verdict_details?.narrative_summary || ""
              });
            }
          }
        } else {
          throw new Error(response.message || "Failed to initialize Round 3");
        }
      } catch (err) {
        console.error("Round 3 loading error:", err);
        setError(err.message || "Failed to connect to CHRONOS Core Mainframe.");
      } finally {
        setLoading(false);
      }
    }

    loadRound3();
  }, [teamId, teamName]);

  // Handle Audio Mute Toggle
  const toggleSound = () => {
    const isMuted = soundEngine.toggleMute();
    setIsAudioMuted(isMuted);
    if (!isMuted) soundEngine.playClick();
  };

  // Handle Candidate Selection
  const handleSelectCandidate = (candId) => {
    soundEngine.playDossierSelect();
    setSelectedCandidateId(candId);
  };

  // Handle Evidence Checkbox Toggle
  const handleToggleEvidence = (evId) => {
    setSelectedEvidenceIds(prev => {
      const exists = prev.includes(evId);
      soundEngine.playEvidenceToggle(!exists);
      if (exists) {
        return prev.filter(id => id !== evId);
      } else {
        return [...prev, evId];
      }
    });
  };

  // Filtered Evidence Pool
  const filteredEvidence = useMemo(() => {
    if (!scenarioData || !scenarioData.evidence_pool) return [];
    if (evidenceCategoryFilter === 'ALL') return scenarioData.evidence_pool;
    return scenarioData.evidence_pool.filter(
      ev => ev.category_code === evidenceCategoryFilter || ev.category === evidenceCategoryFilter
    );
  }, [scenarioData, evidenceCategoryFilter]);

  // Selected Suspect Object
  const selectedSuspect = useMemo(() => {
    if (!scenarioData || !selectedCandidateId) return null;
    return scenarioData.candidates.find(c => c.id === selectedCandidateId);
  }, [scenarioData, selectedCandidateId]);

  // Validation Check: Exactly 1 candidate + >= 2 evidence items
  const isSubmissionReady = Boolean(selectedCandidateId && selectedEvidenceIds.length >= 2);

  // Hold-to-confirm timer effect
  useEffect(() => {
    let interval = null;
    if (isHolding && isConfirmModalOpen) {
      interval = setInterval(() => {
        setHoldProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval);
            executeFinalSubmission();
            return 100;
          }
          return prev + 5; // ~2 seconds
        });
      }, 100);
    } else {
      setHoldProgress(0);
    }
    return () => clearInterval(interval);
  }, [isHolding, isConfirmModalOpen]);

  // Execute Final Decision Submission
  const executeFinalSubmission = async () => {
    if (!isSubmissionReady || isSubmitting) return;

    try {
      setIsSubmitting(true);
      soundEngine.playPurgeConfirm();
      setIsConfirmModalOpen(false);
      setIsCinematicRevealing(true);

      const res = await api.submitRound3Decision(
        teamId,
        selectedCandidateId,
        selectedEvidenceIds
      );

      if (res.status === 'success') {
        setTimeout(() => {
          setSubmissionResult(res);
          setIsCinematicRevealing(false);
        }, 2200);
      } else {
        setIsCinematicRevealing(false);
        alert(res.message || "Failed to record verdict.");
      }
    } catch (err) {
      setIsCinematicRevealing(false);
      console.error("Submission failed:", err);
      alert(`Submission Error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
      setIsHolding(false);
    }
  };

  // Loading Screen
  if (loading) {
    return (
      <div className="min-h-screen bg-obsidian flex flex-col items-center justify-center relative overflow-hidden p-6">
        <div className="absolute inset-0 crt-overlay pointer-events-none opacity-40"></div>
        <div className="relative z-10 flex flex-col items-center text-center max-w-md">
          <div className="relative mb-6">
            <div className="w-20 h-20 rounded-full border-4 border-neon-purple/20 border-t-neon-purple animate-spin glow-neon"></div>
            <Cpu className="w-8 h-8 text-neon-light absolute inset-0 m-auto animate-pulse" />
          </div>
          <h2 className="font-orbitron font-bold text-2xl text-neon-light tracking-widest mb-2">
            INITIALIZING CHRONOS // ROUND 3
          </h2>
          <p className="font-mono text-sm text-dusty-lavender tracking-wider animate-pulse">
            CONNECTING TO SECTOR-0 EMERGENCY DECISION TERMINAL...
          </p>
        </div>
      </div>
    );
  }

  // Error Screen
  if (error || !scenarioData) {
    return (
      <div className="min-h-screen bg-obsidian flex flex-col items-center justify-center p-6 text-center">
        <div className="game-card max-w-lg p-8 border-danger-crimson/50 glow-danger">
          <ShieldAlert className="w-16 h-16 text-danger-crimson mx-auto mb-4 animate-bounce" />
          <h2 className="font-orbitron font-bold text-2xl text-danger-crimson mb-3">
            MAINFRAME CONNECTION FAILED
          </h2>
          <p className="text-dusty-lavender mb-6 text-sm">{error || "Scenario payload missing."}</p>
          <button 
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-neon-purple hover:bg-neon-violet text-white font-orbitron font-bold rounded-xl transition-all shadow-neon-glow"
          >
            RETRY UPLINK
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-obsidian text-[#F5F0FF] relative overflow-x-hidden font-space pb-28">
      {/* CRT Scanline & Subtle Grain Aesthetic Overlay */}
      <div className="fixed inset-0 crt-overlay pointer-events-none opacity-40 z-40"></div>

      {/* Deep Void Background Glows (Neon Purple & Soft Violet Flares) */}
      <div className="fixed top-0 left-1/4 w-[600px] h-[600px] bg-neon-purple/10 rounded-full blur-[150px] pointer-events-none"></div>
      <div className="fixed bottom-0 right-1/4 w-[650px] h-[650px] bg-deep-violet/40 rounded-full blur-[160px] pointer-events-none"></div>

      {/* =====================================================================
          1. TOP EMERGENCY HUD HEADER (Black-Heavy with Neon Purple Accents)
      ====================================================================== */}
      <header className="sticky top-0 z-30 bg-obsidian/95 border-b border-neon-purple/20 backdrop-blur-2xl px-4 lg:px-8 py-3.5 transition-all shadow-2xl">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          
          {/* Main Title & Emergency Status */}
          <div className="flex items-center gap-4">
            <div className="relative flex items-center justify-center w-11 h-11 rounded-xl bg-surface-dark border border-neon-purple/50 glow-neon">
              <ShieldAlert className="w-6 h-6 text-neon-light animate-pulse" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-neon-purple rounded-full animate-ping"></div>
            </div>

            <div>
              <div className="flex items-center gap-2.5">
                <span className="font-orbitron font-black text-lg lg:text-xl tracking-wider text-white">
                  CHRONOS // <span className="text-neon-purple drop-shadow-[0_0_12px_rgba(168,85,247,0.7)]">FINAL DECISION</span>
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-neon-purple/15 border border-neon-purple/50 text-neon-light font-mono tracking-widest font-bold">
                  EMERGENCY TERMINAL
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs text-dusty-lavender font-mono">
                <span>{scenarioData.emergency_header || "PROTOCOL 2140"}</span>
                <span className="text-neon-purple/60">•</span>
                <span className="text-danger-crimson font-bold">{scenarioData.emergency_subtext || "TEMPORAL COLLAPSE: IMMINENT"}</span>
              </div>
            </div>
          </div>

          {/* Right Controls: Integrity Gauge, Timer, Audio & Help */}
          <div className="flex items-center gap-4">
            
            {/* Temporal Stability Indicator */}
            <div className="hidden sm:flex flex-col items-end border-r border-neon-purple/20 pr-4">
              <div className="flex items-center gap-2 text-[11px] font-mono text-dusty-lavender">
                <Activity className="w-3.5 h-3.5 text-neon-purple animate-pulse" />
                <span>CORE INTEGRITY</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-void-black rounded-full overflow-hidden border border-neon-purple/30">
                  <div className="h-full bg-gradient-to-r from-danger-crimson via-neon-purple to-neon-light w-[14.8%] animate-pulse"></div>
                </div>
                <span className="font-orbitron font-bold text-xs text-neon-light">14.8%</span>
              </div>
            </div>

            {/* Countdown Timer */}
            <Timer 
              initialMinutes={5}
              startedAt={roundStartedAt}
              onExpire={() => soundEngine.playLockdownPulse()}
            />

            {/* Audio Toggle Button */}
            <button
              onClick={toggleSound}
              title={isAudioMuted ? "Unmute Tactical SFX" : "Mute Tactical SFX"}
              className="p-2.5 rounded-xl bg-surface-dark border border-neon-purple/30 hover:border-neon-purple text-dusty-lavender hover:text-neon-light transition-all glow-neon-subtle"
            >
              {isAudioMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4 text-neon-light" />}
            </button>

            {/* Mission Briefing Button */}
            <button
              onClick={() => {
                soundEngine.playClick();
                setShowBriefingModal(true);
              }}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-surface-dark border border-neon-purple/30 hover:border-neon-purple text-xs font-mono text-dusty-lavender hover:text-white transition-all glow-neon-subtle"
            >
              <Info className="w-4 h-4 text-neon-purple" />
              <span className="hidden md:inline">PROTOCOL BRIEF</span>
            </button>
          </div>

        </div>
      </header>

      {/* =====================================================================
          2. MAIN INVESTIGATION WORKSPACE
      ====================================================================== */}
      <main className="max-w-7xl mx-auto px-4 lg:px-8 pt-6 space-y-6">

        {/* Incident Alert Strip */}
        <section className="game-card p-4 lg:p-5 border-neon-purple/30 relative overflow-hidden bg-surface-dark/95">
          <div className="absolute top-0 right-0 w-48 h-48 bg-neon-purple/10 rounded-full blur-3xl pointer-events-none"></div>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="p-2.5 rounded-xl bg-neon-purple/15 text-neon-light border border-neon-purple/30 mt-0.5 glow-neon">
                <Radio className="w-5 h-5 animate-pulse" />
              </div>
              <div>
                <div className="flex items-center gap-2 font-mono text-xs text-neon-light">
                  <span className="px-2 py-0.5 rounded bg-neon-purple/20 border border-neon-purple/40 font-bold text-white">
                    CASE CODE: {scenarioData.case_code || scenarioData.case_id}
                  </span>
                  <span>// INCIDENT TELEMETRY</span>
                </div>
                <h3 className="font-orbitron font-bold text-base lg:text-lg text-white mt-1">
                  {scenarioData.title || "Critical Mainframe Divergence"}
                </h3>
                <p className="text-sm text-dusty-lavender/90 leading-relaxed mt-1 max-w-4xl font-space">
                  {scenarioData.incident_brief}
                </p>
              </div>
            </div>

            {/* Team PRN & Live Session Status */}
            <div className="flex sm:flex-col items-center sm:items-end justify-between border-t md:border-t-0 md:border-l border-neon-purple/20 pt-3 md:pt-0 md:pl-6 shrink-0">
              <div className="font-mono text-[11px] text-dusty-lavender">INVESTIGATING TEAM</div>
              <div className="font-orbitron font-bold text-sm text-solar-cream">{teamInfo?.name || teamName}</div>
              <div className="flex items-center gap-1.5 text-[10px] font-mono text-neon-light mt-1">
                <span className="w-1.5 h-1.5 rounded-full bg-neon-purple animate-ping"></span>
                <span>UPLINK ENCRYPTED // SECTOR-0</span>
              </div>
            </div>
          </div>
        </section>

        {/* =====================================================================
            3. TWO-COLUMN SPLIT WORKSPACE
            Left: Suspect Dossiers (Candidate Matrix)
            Right: Supporting Evidence Grid (Correlation Matrix)
        ====================================================================== */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

          {/* -------------------------------------------------------------------
              LEFT COLUMN: SUSPECT DOSSIERS (5-6 Cols on Desktop)
          -------------------------------------------------------------------- */}
          <div className="lg:col-span-6 space-y-4">
            
            <div className="flex items-center justify-between pb-2 border-b border-neon-purple/25">
              <div className="flex items-center gap-2">
                <Fingerprint className="w-5 h-5 text-neon-purple" />
                <h2 className="font-orbitron font-bold text-base tracking-wider text-white">
                  SUSPECT DOSSIERS
                </h2>
              </div>
              <span className="text-xs font-mono text-dusty-lavender">
                [ 1 PRIMARY CULPRIT REQUIRED ]
              </span>
            </div>

            {/* Suspect Candidate Cards */}
            <div className="space-y-4">
              {scenarioData.candidates.map((candidate, idx) => {
                const isSelected = selectedCandidateId === candidate.id;

                return (
                  <div
                    key={candidate.id}
                    onClick={() => handleSelectCandidate(candidate.id)}
                    className={`game-card relative p-5 cursor-pointer transition-all duration-300 ${
                      isSelected 
                        ? 'active border-neon-purple ring-2 ring-neon-purple/60 shadow-neon-active scale-[1.01] bg-surface-card' 
                        : 'hover:border-neon-purple/50 bg-surface-dark/90 opacity-90 hover:opacity-100'
                    }`}
                  >
                    {/* Top Candidate Bar */}
                    <div className="flex items-start justify-between gap-3">
                      
                      <div className="flex items-center gap-3.5">
                        {/* Avatar / Biometric Hologram Badge */}
                        <div className={`relative w-12 h-12 rounded-xl flex items-center justify-center border transition-all ${
                          isSelected 
                            ? 'bg-neon-purple/30 border-neon-purple text-neon-light glow-neon' 
                            : 'bg-void-black border-neon-purple/20 text-dusty-lavender'
                        }`}>
                          <Crosshair className={`w-6 h-6 ${isSelected ? 'text-neon-light animate-spin-slow' : 'text-dusty-lavender'}`} />
                          <div className="absolute -bottom-1 -right-1 px-1 py-0.2 text-[9px] font-mono font-bold rounded bg-black/90 border border-neon-purple/40 text-neon-light">
                            #{idx + 1}
                          </div>
                        </div>

                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-orbitron font-bold text-base text-white">
                              {candidate.name}
                            </h3>
                          </div>
                          <div className="text-xs text-neon-light font-medium">
                            {candidate.designation}
                          </div>
                          <div className="text-[11px] font-mono text-dusty-lavender flex items-center gap-2 mt-0.5">
                            <span>CLEARANCE: {candidate.clearance_level}</span>
                          </div>
                        </div>
                      </div>

                      {/* Selection Radio / Action Button */}
                      <div className="flex flex-col items-end">
                        <button
                          type="button"
                          className={`px-3 py-1.5 rounded-lg font-orbitron font-bold text-xs tracking-wider transition-all flex items-center gap-1.5 ${
                            isSelected 
                              ? 'bg-neon-purple text-white shadow-neon-glow' 
                              : 'bg-void-black border border-neon-purple/30 text-dusty-lavender hover:text-neon-light hover:border-neon-purple'
                          }`}
                        >
                          {isSelected ? (
                            <>
                              <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                              <span>ACCUSED</span>
                            </>
                          ) : (
                            <>
                              <UserX className="w-3.5 h-3.5" />
                              <span>DESIGNATE</span>
                            </>
                          )}
                        </button>
                        <span className="text-[10px] font-mono text-dusty-lavender/80 mt-1">
                          {candidate.biometric_hash}
                        </span>
                      </div>

                    </div>

                    {/* Dossier Expanded Tab Content */}
                    <div className="mt-4 pt-3 border-t border-neon-purple/15">
                      
                      {/* Sub-tabs for Dossier */}
                      <div className="flex items-center gap-2 mb-3 overflow-x-auto pb-1 text-xs font-mono">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            soundEngine.playClick();
                            setActiveDossierTab('overview');
                          }}
                          className={`px-2.5 py-1 rounded-md transition-all ${
                            activeDossierTab === 'overview'
                              ? 'bg-neon-purple text-white border border-neon-light shadow-neon-subtle'
                              : 'bg-void-black text-dusty-lavender hover:text-white border border-neon-purple/20'
                          }`}
                        >
                          PROFILE
                        </button>

                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            soundEngine.playClick();
                            setActiveDossierTab('discrepancy');
                          }}
                          className={`px-2.5 py-1 rounded-md transition-all ${
                            activeDossierTab === 'discrepancy'
                              ? 'bg-danger-crimson/80 text-white border border-danger-crimson glow-danger'
                              : 'bg-void-black text-dusty-lavender hover:text-white border border-neon-purple/20'
                          }`}
                        >
                          DISCREPANCY
                        </button>

                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            soundEngine.playClick();
                            setActiveDossierTab('motive');
                          }}
                          className={`px-2.5 py-1 rounded-md transition-all ${
                            activeDossierTab === 'motive'
                              ? 'bg-neon-purple text-white border border-neon-light shadow-neon-subtle'
                              : 'bg-void-black text-dusty-lavender hover:text-white border border-neon-purple/20'
                          }`}
                        >
                          MOTIVE
                        </button>

                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            soundEngine.playClick();
                            setActiveDossierTab('alibi');
                          }}
                          className={`px-2.5 py-1 rounded-md transition-all ${
                            activeDossierTab === 'alibi'
                              ? 'bg-neon-purple text-white border border-neon-light shadow-neon-subtle'
                              : 'bg-void-black text-dusty-lavender hover:text-white border border-neon-purple/20'
                          }`}
                        >
                          CLAIMED ALIBI
                        </button>
                      </div>

                      {/* Tab Dynamic Body */}
                      <div className="bg-void-black rounded-xl p-3.5 border border-neon-purple/20 text-xs leading-relaxed">
                        {activeDossierTab === 'overview' && (
                          <div className="text-dusty-lavender">
                            <span className="text-neon-light font-mono font-bold block mb-1">DOSSIER FILE:</span>
                            {candidate.dossier}
                          </div>
                        )}

                        {activeDossierTab === 'discrepancy' && (
                          <div className="text-[#FCA5A5]">
                            <span className="text-danger-crimson font-mono font-bold block mb-1">TELEMETRY ANOMALY:</span>
                            {candidate.discrepancy}
                          </div>
                        )}

                        {activeDossierTab === 'motive' && (
                          <div className="text-dusty-lavender">
                            <span className="text-neon-light font-mono font-bold block mb-1">BEHAVIORAL ASSESSMENT:</span>
                            {candidate.motive_analysis}
                          </div>
                        )}

                        {activeDossierTab === 'alibi' && (
                          <div className="text-dusty-lavender italic">
                            <span className="text-neon-light font-mono font-bold block mb-1 not-italic">RECORDED STATEMENT:</span>
                            "{candidate.alibi_statement}"
                          </div>
                        )}
                      </div>

                    </div>
                  </div>
                );
              })}
            </div>

          </div>

          {/* -------------------------------------------------------------------
              RIGHT COLUMN: SUPPORTING EVIDENCE MATRIX (6 Cols on Desktop)
          -------------------------------------------------------------------- */}
          <div className="lg:col-span-6 space-y-4">
            
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-neon-purple/25">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-neon-purple" />
                <h2 className="font-orbitron font-bold text-base tracking-wider text-white">
                  SUPPORTING EVIDENCE GRID
                </h2>
              </div>
              
              {/* Evidence Counter Badge */}
              <div className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold flex items-center gap-1.5 transition-all ${
                selectedEvidenceIds.length >= 2 
                  ? 'bg-emerald-500/20 border border-emerald-500/50 text-emerald-400' 
                  : 'bg-neon-purple/20 border border-neon-purple/60 text-neon-light animate-pulse glow-neon-subtle'
              }`}>
                <span>EVIDENCE: {selectedEvidenceIds.length} / MIN 2</span>
                {selectedEvidenceIds.length >= 2 ? <Check className="w-3.5 h-3.5" /> : null}
              </div>
            </div>

            {/* Category Filter Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs font-mono">
              {[
                { id: 'ALL', label: 'ALL LOGS' },
                { id: 'TIMELINE_MODIFICATION', label: 'TIMELINE MOD' },
                { id: 'ACCESS_HISTORY', label: 'ACCESS HIST' },
                { id: 'INCIDENT_TIMESTAMP', label: 'TIMESTAMPS' },
                { id: 'SYSTEM_AUTHORIZATION', label: 'AUTHORIZATIONS' }
              ].map(cat => (
                <button
                  key={cat.id}
                  onClick={() => {
                    soundEngine.playClick();
                    setEvidenceCategoryFilter(cat.id);
                  }}
                  className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${
                    evidenceCategoryFilter === cat.id
                      ? 'bg-neon-purple text-white font-bold border border-neon-light shadow-neon-glow'
                      : 'bg-surface-dark text-dusty-lavender border border-neon-purple/20 hover:border-neon-purple/50 hover:text-white'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            {/* Evidence Checklist Pool */}
            <div className="space-y-3 max-h-[640px] overflow-y-auto pr-1">
              {filteredEvidence.map((evidence) => {
                const isChecked = selectedEvidenceIds.includes(evidence.id);

                return (
                  <div
                    key={evidence.id}
                    onClick={() => handleToggleEvidence(evidence.id)}
                    className={`game-card p-4 cursor-pointer transition-all duration-200 border ${
                      isChecked
                        ? 'border-neon-purple bg-surface-card shadow-neon-active'
                        : 'border-neon-purple/15 bg-surface-dark/90 hover:border-neon-purple/40 opacity-90 hover:opacity-100'
                    }`}
                  >
                    <div className="flex items-start gap-3.5">
                      
                      {/* Checkbox Box */}
                      <div className={`mt-0.5 w-6 h-6 rounded-lg flex items-center justify-center shrink-0 transition-all ${
                        isChecked 
                          ? 'bg-neon-purple text-white font-bold shadow-neon-glow' 
                          : 'bg-void-black border border-neon-purple/40 text-transparent'
                      }`}>
                        <Check className="w-4 h-4" />
                      </div>

                      {/* Evidence Body */}
                      <div className="space-y-1.5 flex-1 min-w-0">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          
                          <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
                            evidence.category_code === 'TIMELINE_MODIFICATION'
                              ? 'bg-danger-crimson/20 border border-danger-crimson/40 text-[#FCA5A5]'
                              : evidence.category_code === 'SYSTEM_AUTHORIZATION'
                                ? 'bg-amber-500/20 border border-amber-500/40 text-amber-300'
                                : 'bg-neon-purple/25 border border-neon-purple/50 text-neon-light'
                          }`}>
                            {evidence.category}
                          </span>

                          <span className="text-[11px] font-mono text-dusty-lavender">
                            {evidence.timestamp}
                          </span>
                        </div>

                        <h4 className="font-orbitron font-bold text-sm text-white">
                          {evidence.label}
                        </h4>

                        <p className="text-xs text-dusty-lavender leading-relaxed">
                          {evidence.description}
                        </p>

                        {/* Terminal Node & Forensic Code Excerpt */}
                        <div className="bg-void-black rounded-lg p-2 font-mono text-[10px] text-neon-light border border-neon-purple/20 flex items-center justify-between gap-2">
                          <span className="truncate">SOURCE: {evidence.terminal_source}</span>
                          <span className="text-dusty-lavender shrink-0">[{evidence.severity_level || "LOGGED"}]</span>
                        </div>
                      </div>

                    </div>
                  </div>
                );
              })}
            </div>

          </div>

        </div>

      </main>

      {/* =====================================================================
          4. BOTTOM STICKY ACTION HUD BAR (Black-Heavy with Neon Glow)
      ====================================================================== */}
      <footer className="fixed bottom-0 left-0 right-0 z-30 bg-obsidian/95 border-t border-neon-purple/30 backdrop-blur-2xl px-4 lg:px-8 py-3.5 shadow-2xl">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          
          {/* Live Accusation Summary */}
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-2">
              <span className="text-dusty-lavender">ACCUSED:</span>
              <span className={`font-orbitron font-bold text-sm ${
                selectedSuspect ? 'text-neon-light' : 'text-danger-crimson italic'
              }`}>
                {selectedSuspect ? selectedSuspect.name : "[ NONE SELECTED ]"}
              </span>
            </div>

            <div className="hidden md:flex items-center gap-2 border-l border-neon-purple/30 pl-4">
              <span className="text-dusty-lavender">EVIDENCE CORROBORATION:</span>
              <span className={`font-bold ${
                selectedEvidenceIds.length >= 2 ? 'text-emerald-400' : 'text-amber-400'
              }`}>
                {selectedEvidenceIds.length} Log(s) Linked
              </span>
            </div>
          </div>

          {/* Action Button: Initiate Purge */}
          <div className="flex items-center gap-3 w-full sm:w-auto">
            {submissionResult ? (
              <button
                onClick={() => {
                  soundEngine.playClick();
                  if (onNavigateToCompletion) onNavigateToCompletion();
                  else window.location.href = '/completion';
                }}
                className="w-full sm:w-auto px-8 py-3 rounded-xl bg-reward-gradient font-orbitron font-bold text-sm text-obsidian tracking-wider hover:opacity-95 transition-all shadow-solar-glow flex items-center justify-center gap-2"
              >
                <span>ADVANCE TO MISSION DEBRIEF</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="button"
                disabled={!isSubmissionReady || isSubmitting}
                onClick={() => {
                  soundEngine.playLockdownPulse();
                  setIsConfirmModalOpen(true);
                }}
                className={`w-full sm:w-auto px-8 py-3.5 rounded-xl font-orbitron font-black text-sm tracking-wider transition-all flex items-center justify-center gap-2.5 ${
                  isSubmissionReady
                    ? 'bg-gradient-to-r from-neon-purple via-neon-violet to-danger-crimson text-white hover:opacity-95 shadow-neon-active animate-pulse'
                    : 'bg-surface-dark border border-neon-purple/20 text-dusty-lavender cursor-not-allowed opacity-60'
                }`}
              >
                <Lock className="w-4 h-4 text-neon-light" />
                <span>INITIATE FINAL PURGE & LOCK DECISION</span>
              </button>
            )}
          </div>

        </div>
      </footer>

      {/* =====================================================================
          5. HIGH-TENSION CONFIRMATION MODAL
      ====================================================================== */}
      {isConfirmModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md animate-fadeIn">
          <div className="game-card max-w-xl w-full p-6 lg:p-8 border-danger-crimson glow-danger relative overflow-hidden bg-surface-card">
            
            {/* Modal Ambient Beacon */}
            <div className="flex items-center gap-3 pb-4 border-b border-danger-crimson/40">
              <div className="p-3 rounded-xl bg-danger-crimson/20 text-danger-crimson animate-bounce">
                <AlertOctagon className="w-7 h-7" />
              </div>
              <div>
                <h3 className="font-orbitron font-black text-lg text-white tracking-wide">
                  CRITICAL: CONFIRM TIMELINE PURGE
                </h3>
                <p className="font-mono text-xs text-danger-crimson tracking-widest font-bold">
                  IRREVERSIBLE CHRONOS MAINFRAME LOCKOUT
                </p>
              </div>
            </div>

            {/* Accusation Verification Box */}
            <div className="my-6 space-y-4 text-xs font-mono">
              <div className="bg-void-black rounded-xl p-4 border border-neon-purple/25 space-y-2">
                <div className="text-dusty-lavender">PRIMARY SUSPECT ACCUSED:</div>
                <div className="font-orbitron font-bold text-base text-neon-light">
                  {selectedSuspect?.name}
                </div>
                <div className="text-dusty-lavender">
                  {selectedSuspect?.designation} ({selectedSuspect?.biometric_hash})
                </div>
              </div>

              <div className="bg-void-black rounded-xl p-4 border border-neon-purple/25 space-y-2">
                <div className="text-dusty-lavender">CITED EVIDENCE LOGS ({selectedEvidenceIds.length}):</div>
                <ul className="space-y-1 list-disc list-inside text-white/90">
                  {selectedEvidenceIds.map(id => {
                    const ev = scenarioData.evidence_pool.find(e => e.id === id);
                    return (
                      <li key={id} className="truncate">
                        <span className="text-neon-purple">[{ev?.category}]:</span> {ev?.label}
                      </li>
                    );
                  })}
                </ul>
              </div>

              <div className="p-3 rounded-lg bg-danger-crimson/15 border border-danger-crimson/40 text-danger-crimson text-center">
                WARNING: Submitting this decision will lock your score (+30 or 0) and establish your official leaderboard completion timestamp.
              </div>
            </div>

            {/* Hold to Confirm Button & Cancel */}
            <div className="space-y-3">
              <button
                type="button"
                onMouseDown={() => setIsHolding(true)}
                onMouseUp={() => setIsHolding(false)}
                onMouseLeave={() => setIsHolding(false)}
                onTouchStart={() => setIsHolding(true)}
                onTouchEnd={() => setIsHolding(false)}
                className="relative w-full py-4 rounded-xl overflow-hidden bg-gradient-to-r from-danger-crimson via-neon-violet to-neon-purple font-orbitron font-black text-sm text-white tracking-widest uppercase transition-all shadow-danger-glow select-none"
              >
                {/* Hold Progress Bar Fill */}
                <div 
                  className="absolute inset-0 bg-white/30 transition-all duration-100 pointer-events-none"
                  style={{ width: `${holdProgress}%` }}
                ></div>
                
                <div className="relative z-10 flex items-center justify-center gap-2">
                  <Zap className="w-4 h-4 text-neon-light" />
                  <span>{holdProgress > 0 ? `HOLDING... ${holdProgress}%` : "PRESS & HOLD TO LOCK VERDICT"}</span>
                </div>
              </button>

              <button
                type="button"
                onClick={() => {
                  soundEngine.playClick();
                  setIsConfirmModalOpen(false);
                  setIsHolding(false);
                }}
                className="w-full py-2.5 rounded-xl bg-void-black border border-neon-purple/30 text-dusty-lavender hover:text-white font-mono text-xs transition-all"
              >
                [ RETURN TO FORENSIC ANALYSIS ]
              </button>
            </div>

          </div>
        </div>
      )}

      {/* =====================================================================
          6. CINEMATIC GLITCH WIPE OVERLAY
      ====================================================================== */}
      {isCinematicRevealing && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-obsidian text-center p-6">
          <div className="relative mb-8">
            <div className="w-28 h-28 rounded-full border-4 border-neon-purple border-t-white animate-spin glow-neon"></div>
            <ShieldAlert className="w-12 h-12 text-neon-light absolute inset-0 m-auto animate-pulse" />
          </div>
          <h2 className="font-orbitron font-black text-3xl text-white tracking-widest mb-3 animate-pulse">
            COMMITTING FINAL PURGE SEQUENCE
          </h2>
          <p className="font-mono text-sm text-neon-purple tracking-widest max-w-md">
            ISOLATING CORRUPTED TIMELINE CLUSTERS... RECOMPUTING CHRONOS SYNCHRONIZATION INDEX...
          </p>
        </div>
      )}

      {/* =====================================================================
          7. POST-SUBMISSION VERDICT & DEBRIEF OVERLAY
      ====================================================================== */}
      {submissionResult && !isCinematicRevealing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/95 backdrop-blur-xl animate-fadeIn">
          <div className="game-card max-w-2xl w-full p-6 lg:p-8 border-neon-purple shadow-neon-active space-y-6 bg-surface-card">
            
            {/* Header Result */}
            <div className="text-center space-y-2">
              <div className="inline-flex p-3 rounded-2xl bg-neon-purple/20 text-neon-light border border-neon-purple/50 mb-2 glow-neon">
                <Sparkles className="w-8 h-8" />
              </div>

              <h2 className="font-orbitron font-black text-2xl lg:text-3xl text-white tracking-wider">
                DECISION COMMITTED // <span className="text-neon-purple">VERDICT RECORDED</span>
              </h2>
              <p className="font-mono text-xs text-dusty-lavender">
                OFFICIAL SUBMISSION TIMESTAMP: {submissionResult.completed_at || new Date().toISOString()}
              </p>
            </div>

            {/* Score Breakdown Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="bg-void-black p-4 rounded-xl border border-neon-purple/20 text-center">
                <div className="text-[10px] font-mono text-dusty-lavender uppercase">ROUND 3 SCORE</div>
                <div className="font-orbitron font-bold text-2xl text-neon-light mt-1">
                  +{submissionResult.points_awarded || submissionResult.round3_score || 0}
                </div>
                <div className="text-[9px] font-mono text-dusty-lavender">MAX 30 PTS</div>
              </div>

              <div className="bg-void-black p-4 rounded-xl border border-neon-purple/20 text-center">
                <div className="text-[10px] font-mono text-dusty-lavender uppercase">TOTAL EVENT SCORE</div>
                <div className="font-orbitron font-bold text-2xl text-emerald-400 mt-1">
                  {submissionResult.total_score || 0}
                </div>
                <div className="text-[9px] font-mono text-dusty-lavender">MAX 130 PTS</div>
              </div>

              <div className="col-span-2 sm:col-span-1 bg-void-black p-4 rounded-xl border border-neon-purple/20 text-center">
                <div className="text-[10px] font-mono text-dusty-lavender uppercase">TIE-BREAKER STATUS</div>
                <div className="font-orbitron font-bold text-sm text-neon-light mt-2">
                  LOCKED
                </div>
                <div className="text-[9px] font-mono text-dusty-lavender">PRIORITY 1 ACTIVE</div>
              </div>
            </div>

            {/* Forensic Narrative Debrief */}
            <div className="bg-void-black rounded-xl p-4 border border-neon-purple/20 space-y-2">
              <div className="font-mono text-xs text-neon-light font-bold flex items-center gap-1.5">
                <Terminal className="w-4 h-4 text-neon-purple" />
                <span>CHRONOS FORENSIC DEBRIEF</span>
              </div>
              <p className="text-xs text-dusty-lavender leading-relaxed font-space">
                {submissionResult.narrative_summary || 
                  "Your final accusation and corroborating forensic evidence have been permanently integrated into the CHRONOS temporal ledger."}
              </p>
            </div>

            {/* Action Advance */}
            <button
              onClick={() => {
                soundEngine.playClick();
                if (onNavigateToCompletion) onNavigateToCompletion();
                else window.location.href = '/completion';
              }}
              className="w-full py-4 rounded-xl bg-neon-gradient font-orbitron font-black text-sm text-white tracking-widest uppercase hover:opacity-95 transition-all shadow-neon-glow flex items-center justify-center gap-2"
            >
              <span>ADVANCE TO FINAL COMPLETION & SUMMARY</span>
              <ChevronRight className="w-4 h-4" />
            </button>

          </div>
        </div>
      )}

      {/* =====================================================================
          8. MISSION BRIEFING MODAL
      ====================================================================== */}
      {showBriefingModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md animate-fadeIn">
          <div className="game-card max-w-lg w-full p-6 lg:p-8 border-neon-purple/50 space-y-4 bg-surface-card shadow-neon-active">
            <div className="flex items-center justify-between pb-3 border-b border-neon-purple/20">
              <div className="flex items-center gap-2 font-orbitron font-bold text-base text-white">
                <Info className="w-5 h-5 text-neon-purple" />
                <span>ROUND 3 PROTOCOL RULES</span>
              </div>
              <button
                onClick={() => setShowBriefingModal(false)}
                className="text-dusty-lavender hover:text-white"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs text-dusty-lavender leading-relaxed font-space">
              <p>
                <strong className="text-neon-light">1. The Wisdom Round:</strong> As Temporal Engineers reaching the CHRONOS Core, you must review candidate dossiers and forensic evidence to identify the true culprit behind the timeline collapse.
              </p>
              <p>
                <strong className="text-neon-light">2. Evidence Corroboration:</strong> You must select at least <strong className="text-white">two (2) verified supporting evidence logs</strong> that substantiate your accusation.
              </p>
              <p>
                <strong className="text-neon-light">3. Scoring:</strong> Correct suspect awards <strong className="text-white">+30 Points</strong>. Incorrect suspect awards <strong className="text-white">0 Points</strong>.
              </p>
              <p>
                <strong className="text-neon-light">4. Tie-Breaker Rule:</strong> Round 3 submission time is the first priority tie-breaker on the master leaderboard.
              </p>
            </div>

            <button
              onClick={() => setShowBriefingModal(false)}
              className="w-full py-2.5 rounded-xl bg-neon-purple hover:bg-neon-violet font-orbitron font-bold text-xs text-white tracking-wider shadow-neon-glow"
            >
              ACKNOWLEDGED
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
