import React, { useState, useEffect, useMemo } from 'react';
import { 
  ShieldAlert, 
  AlertCircle, 
  Cpu, 
  CheckCircle2, 
  FileText, 
  Lock, 
  Volume2, 
  VolumeX, 
  Info, 
  Sparkles, 
  ChevronRight,
  UserX,
  Radio,
  FileCheck2,
  FolderLock,
  ArrowRight,
  X
} from 'lucide-react';
import { soundEngine } from '../components/AudioEngine';
import ThemeSelector from '../components/ThemeSelector';
import { useTheme } from '../context/ThemeContext';
import { api } from '../services/api';

/**
 * Project Chronos — Round 3: Final Decision / Wisdom Round
 * 24-inch display optimized, high-contrast, clean layout.
 * Left: Project Alpha, Beta, Gamma candidate selection.
 * Right: Round 2 carried-over evidence references (Read-only).
 * Points are hidden from players.
 */
export default function Round3({ 
  teamId = 1, 
  teamName = "Temporal Engineers",
  onNavigateToCompletion = null 
}) {
  const { themeConfig } = useTheme();

  // Scenario & Game State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scenarioData, setScenarioData] = useState(null);
  const [teamInfo, setTeamInfo] = useState(null);

  // User Candidate Selection (Alpha, Beta, or Gamma)
  const [selectedCandidateId, setSelectedCandidateId] = useState(null);

  // UI States
  const [isAudioMuted, setIsAudioMuted] = useState(false);
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showBriefingModal, setShowBriefingModal] = useState(false);

  // Load Round 3 Scenario on Mount
  useEffect(() => {
    async function loadRound3() {
      try {
        setLoading(true);
        setError(null);

        const response = await api.startRound3(teamId);
        
        if (response.status === 'success') {
          setScenarioData(response.case);
          setTeamInfo({
            id: response.team_id || teamId,
            name: response.team_name || teamName,
            state: response.team_state
          });

          // If already submitted, navigate to completion
          if (response.is_submitted) {
            if (onNavigateToCompletion) {
              onNavigateToCompletion();
            }
          }
        } else {
          throw new Error(response.message || "Failed to initialize Round 3");
        }
      } catch (err) {
        console.error("Round 3 loading error:", err);
        setError(err.message || "Failed to connect to CHRONOS Mainframe.");
      } finally {
        setLoading(false);
      }
    }

    loadRound3();
  }, [teamId, teamName, onNavigateToCompletion]);

  // Audio Toggle
  const toggleSound = () => {
    const isMuted = soundEngine.toggleMute();
    setIsAudioMuted(isMuted);
    if (!isMuted) soundEngine.playClick();
  };

  // Select Candidate
  const handleSelectCandidate = (candId) => {
    soundEngine.playDossierSelect();
    setSelectedCandidateId(candId);
  };

  // Selected Suspect Object
  const selectedSuspect = useMemo(() => {
    if (!scenarioData || !selectedCandidateId) return null;
    return scenarioData.candidates.find(c => c.id === selectedCandidateId);
  }, [scenarioData, selectedCandidateId]);

  // Execute Submission
  const executeFinalSubmission = async () => {
    if (!selectedCandidateId || isSubmitting) return;

    try {
      setIsSubmitting(true);
      soundEngine.playPurgeConfirm();
      setIsConfirmModalOpen(false);

      const availableEvidenceIds = scenarioData?.evidence_pool?.map(e => e.id) || [];

      const res = await api.submitRound3Decision(
        teamId,
        selectedCandidateId,
        availableEvidenceIds
      );

      if (res.status === 'success') {
        if (onNavigateToCompletion) {
          onNavigateToCompletion();
        } else {
          window.location.href = '/completion';
        }
      } else {
        alert(res.message || "Failed to record verdict.");
      }
    } catch (err) {
      console.error("Submission failed:", err);
      alert(`Submission Error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Loading State
  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex flex-col items-center justify-center p-8">
        <div 
          className="w-16 h-16 rounded-full border-4 border-t-transparent animate-spin mb-4"
          style={{ borderColor: 'var(--neon-primary)', borderTopColor: 'transparent' }}
        ></div>
        <h2 className="font-orbitron text-xl tracking-wider text-white">
          CHRONOS CENTRAL MAINFRAME
        </h2>
        <p className="font-mono text-sm text-[var(--text-muted)] mt-2">
          Synchronizing Round 3 Investigation Dossiers...
        </p>
      </div>
    );
  }

  // Error State
  if (error || !scenarioData) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex flex-col items-center justify-center p-8">
        <div className="game-card max-w-lg p-8 text-center space-y-4">
          <AlertCircle className="w-14 h-14 text-red-400 mx-auto" />
          <h2 className="font-orbitron font-bold text-2xl text-white">SYSTEM CONNECTION ERROR</h2>
          <p className="text-base text-[var(--text-muted)]">{error || "Failed to load case data."}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 rounded-xl font-orbitron font-bold text-sm text-white"
            style={{ background: 'var(--neon-gradient)' }}
          >
            RETRY CONNECTION
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-body)] font-space pb-36">
      {/* Scanline CRT overlay */}
      <div className="fixed inset-0 crt-overlay pointer-events-none opacity-20 z-40"></div>

      {/* Atmospheric Glow */}
      <div 
        className="fixed top-1/4 left-1/4 w-[600px] h-[600px] rounded-full blur-[200px] pointer-events-none opacity-15"
        style={{ backgroundColor: 'var(--neon-primary)' }}
      ></div>

      {/* =====================================================================
          1. TOP NAVIGATION & STATUS BAR (24" Optimized)
      ====================================================================== */}
      <header className="sticky top-0 z-30 bg-[var(--bg-primary)]/90 border-b border-white/15 backdrop-blur-xl px-6 lg:px-12 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          
          {/* Main Title */}
          <div className="flex items-center gap-4">
            <div 
              className="p-3 rounded-2xl border shadow-lg"
              style={{ 
                backgroundColor: 'var(--theme-accent-badge-bg)', 
                borderColor: 'var(--theme-accent-badge-border)',
                boxShadow: '0 0 15px var(--neon-glow)'
              }}
            >
              <Cpu className="w-6 h-6 text-[var(--neon-light)]" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="font-orbitron font-black text-xl lg:text-2xl tracking-wide text-white">
                  ROUND 3: <span style={{ color: 'var(--neon-primary)' }}>FINAL DECISION</span>
                </h1>
                <span className="text-xs font-mono px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 font-bold">
                  UNTIMED
                </span>
              </div>
              <p className="text-sm font-mono text-[var(--text-muted)] mt-0.5">
                Investigating Unit: <strong className="text-white">{teamInfo?.name || teamName}</strong>
              </p>
            </div>
          </div>

          {/* Right Controls: Theme Selector, Sound & Rules */}
          <div className="flex items-center gap-3">
            <ThemeSelector />

            <button
              onClick={toggleSound}
              title={isAudioMuted ? "Unmute Audio" : "Mute Audio"}
              className="p-3 rounded-xl bg-black/50 border border-white/15 hover:border-[var(--neon-primary)] text-[var(--text-muted)] hover:text-white transition-all backdrop-blur-md"
            >
              {isAudioMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5 text-[var(--neon-light)]" />}
            </button>

            <button
              onClick={() => {
                soundEngine.playClick();
                setShowBriefingModal(true);
              }}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-black/50 border border-white/15 hover:border-[var(--neon-primary)] text-sm font-mono text-[var(--text-muted)] hover:text-white transition-all backdrop-blur-md"
            >
              <Info className="w-4 h-4 text-[var(--neon-light)]" />
              <span>Rules</span>
            </button>
          </div>

        </div>
      </header>

      {/* =====================================================================
          2. MAIN INVESTIGATION WORKSPACE (2-Column Layout)
      ====================================================================== */}
      <main className="max-w-7xl mx-auto px-6 lg:px-12 pt-8 space-y-8">

        {/* Narrative Briefing Header */}
        <section className="game-card p-6 lg:p-8 border-white/15 space-y-3 bg-[var(--bg-surface)]">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-2 text-sm font-mono text-[var(--neon-light)]">
              <Radio className="w-5 h-5 animate-pulse text-[var(--neon-primary)]" />
              <span className="font-bold uppercase tracking-wider">{scenarioData.title || "Timeline Anomaly Brief"}</span>
            </div>
            <span className="text-xs font-mono text-[var(--text-dim)] bg-black/40 px-3 py-1 rounded-lg border border-white/10">
              CASE: {scenarioData.case_code || scenarioData.case_id}
            </span>
          </div>
          
          <p className="text-base text-[var(--text-body)] leading-relaxed font-space max-w-5xl">
            {scenarioData.incident_brief}
          </p>
        </section>

        {/* 2-Column Split: Suspect Selection (Left) & Round 2 Evidence (Right) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

          {/* ===================================================================
              LEFT COLUMN: SUSPECT DESIGNATION (Alpha, Beta, Gamma)
          ==================================================================== */}
          <div className="lg:col-span-7 space-y-6">
            <div className="flex items-center justify-between pb-3 border-b border-white/15">
              <div>
                <h2 className="font-orbitron font-bold text-xl text-white">
                  1. Designate Primary Suspect
                </h2>
                <p className="text-sm text-[var(--text-muted)] mt-1">
                  Select which project sector initiated the fatal breach.
                </p>
              </div>
              <span 
                className="text-xs font-mono font-bold px-3 py-1 rounded-lg border"
                style={{ 
                  color: 'var(--neon-light)', 
                  borderColor: 'var(--theme-accent-badge-border)',
                  backgroundColor: 'var(--theme-accent-badge-bg)'
                }}
              >
                1 REQUIRED
              </span>
            </div>

            <div className="space-y-4">
              {scenarioData.candidates.map((candidate) => {
                const isSelected = selectedCandidateId === candidate.id;

                return (
                  <div
                    key={candidate.id}
                    onClick={() => handleSelectCandidate(candidate.id)}
                    className={`game-card p-6 cursor-pointer transition-all duration-200 border relative ${
                      isSelected 
                        ? 'ring-2 active scale-[1.01]' 
                        : 'hover:bg-[var(--bg-surface-elevated)]'
                    }`}
                    style={{
                      borderColor: isSelected ? 'var(--neon-light)' : undefined,
                      boxShadow: isSelected ? '0 0 30px var(--neon-glow-strong)' : undefined
                    }}
                  >
                    <div className="space-y-4">
                      {/* Header */}
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <span className="text-xs font-mono font-bold uppercase tracking-wider text-[var(--neon-light)]">
                            {candidate.timeline_sector} • {candidate.designation}
                          </span>
                          <h3 className="font-orbitron font-black text-2xl text-white mt-1">
                            {candidate.name}
                          </h3>
                          <div className="text-sm text-[var(--text-muted)] mt-1 font-mono">
                            Lead Architect: <strong className="text-white">{candidate.lead_name}</strong>
                          </div>
                        </div>

                        <div 
                          className={`p-3 rounded-2xl transition-all ${
                            isSelected 
                              ? 'text-white shadow-lg' 
                              : 'bg-white/5 text-[var(--text-dim)]'
                          }`}
                          style={{
                            background: isSelected ? 'var(--neon-gradient)' : undefined,
                            boxShadow: isSelected ? '0 0 18px var(--neon-glow)' : undefined
                          }}
                        >
                          {isSelected ? <CheckCircle2 className="w-6 h-6" /> : <UserX className="w-6 h-6" />}
                        </div>
                      </div>

                      {/* Dossier */}
                      <p className="text-sm text-[var(--text-body)] leading-relaxed pt-3 border-t border-white/10">
                        {candidate.dossier}
                      </p>

                      {/* Forensic Discrepancy Box */}
                      <div className="bg-black/60 p-4 rounded-xl border border-white/10 text-sm text-[var(--text-body)] space-y-1">
                        <span className="text-xs font-mono text-[var(--neon-light)] font-bold block uppercase tracking-wider">
                          ROUND 2 AUDIT DISCREPANCY:
                        </span>
                        <p className="text-xs leading-relaxed text-[var(--text-muted)]">{candidate.discrepancy}</p>
                      </div>

                      {/* Action Button */}
                      <button
                        type="button"
                        className={`w-full py-3.5 rounded-xl font-orbitron font-bold text-sm tracking-wider transition-all flex items-center justify-center gap-2 cursor-pointer ${
                          isSelected 
                            ? 'text-white shadow-lg' 
                            : 'bg-white/5 hover:bg-white/10 text-[var(--text-muted)] hover:text-white border border-white/15'
                        }`}
                        style={{
                          background: isSelected ? 'var(--neon-gradient)' : undefined,
                          boxShadow: isSelected ? '0 0 20px var(--neon-glow)' : undefined
                        }}
                      >
                        {isSelected ? "SECTOR DESIGNATED AS CULPRIT" : "SELECT SECTOR"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* ===================================================================
              RIGHT COLUMN: CARRIED-OVER EVIDENCE ARCHIVES FROM ROUND 2
          ==================================================================== */}
          <div className="lg:col-span-5 space-y-6">
            <div className="flex items-center justify-between pb-3 border-b border-white/15">
              <div>
                <h2 className="font-orbitron font-bold text-xl text-white flex items-center gap-2">
                  <FolderLock className="w-5 h-5 text-[var(--neon-light)]" />
                  <span>2. Round 2 Evidence Archives</span>
                </h2>
                <p className="text-sm text-[var(--text-muted)] mt-1">
                  Corroborating telemetry logs carried over from terminal extraction.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              {scenarioData.evidence_pool.map((evidence) => (
                <div
                  key={evidence.id}
                  className="game-card p-5 border-white/15 bg-[var(--bg-surface)] space-y-2 hover:border-[var(--neon-primary)] transition-all"
                >
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span 
                      className="text-xs font-mono px-2.5 py-1 rounded-md font-bold uppercase tracking-wider border"
                      style={{
                        backgroundColor: 'var(--theme-accent-badge-bg)',
                        borderColor: 'var(--theme-accent-badge-border)',
                        color: 'var(--neon-light)'
                      }}
                    >
                      {evidence.source_file}
                    </span>
                    <span className="text-xs font-mono text-[var(--text-dim)]">
                      {evidence.timestamp}
                    </span>
                  </div>

                  <h4 className="font-orbitron font-bold text-base text-white pt-1">
                    {evidence.label}
                  </h4>

                  <p className="text-sm text-[var(--text-body)] leading-relaxed">
                    {evidence.description}
                  </p>

                  <div className="pt-2 border-t border-white/10 text-xs font-mono text-[var(--neon-light)]">
                    Link: {evidence.relevance}
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </main>

      {/* =====================================================================
          3. STICKY BOTTOM DECISION COMMIT BAR (24" High Contrast)
      ====================================================================== */}
      <footer className="fixed bottom-0 left-0 right-0 z-30 bg-[var(--bg-primary)]/95 border-t border-white/15 backdrop-blur-2xl px-6 lg:px-12 py-5 shadow-2xl">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          
          {/* Status Text */}
          <div className="flex items-center gap-4 text-sm font-mono">
            <span className="text-[var(--text-muted)]">Designated Target:</span>
            <strong 
              className="text-base font-orbitron"
              style={{ color: selectedSuspect ? 'var(--neon-light)' : 'var(--text-dim)' }}
            >
              {selectedSuspect ? `${selectedSuspect.name} (${selectedSuspect.timeline_sector})` : "NO SECTOR SELECTED"}
            </strong>
          </div>

          {/* Submit Button */}
          <div>
            <button
              type="button"
              disabled={!selectedCandidateId || isSubmitting}
              onClick={() => {
                soundEngine.playLockdownPulse();
                setIsConfirmModalOpen(true);
              }}
              className={`px-10 py-4 rounded-xl font-orbitron font-black text-sm tracking-wider transition-all flex items-center gap-3 cursor-pointer ${
                selectedCandidateId
                  ? 'text-white shadow-xl'
                  : 'bg-white/5 border border-white/15 text-[var(--text-dim)] cursor-not-allowed opacity-50'
              }`}
              style={{
                background: selectedCandidateId ? 'var(--neon-gradient)' : undefined,
                boxShadow: selectedCandidateId ? '0 0 25px var(--neon-glow)' : undefined
              }}
            >
              <Lock className="w-5 h-5" />
              <span>SUBMIT FINAL DETERMINATION</span>
            </button>
          </div>

        </div>
      </footer>

      {/* =====================================================================
          4. CONFIRMATION MODAL
      ====================================================================== */}
      {isConfirmModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/85 backdrop-blur-md">
          <div className="game-card max-w-lg w-full p-8 border-white/20 bg-[var(--bg-surface)] space-y-6 shadow-2xl">
            
            <div className="space-y-2 text-center">
              <div 
                className="inline-flex p-3 rounded-2xl border shadow-lg"
                style={{ 
                  backgroundColor: 'var(--theme-accent-badge-bg)', 
                  borderColor: 'var(--theme-accent-badge-border)' 
                }}
              >
                <ShieldAlert className="w-8 h-8 text-[var(--neon-light)]" />
              </div>
              <h3 className="font-orbitron font-black text-2xl text-white">
                CONFIRM FINAL ACCUSATION
              </h3>
              <p className="text-sm text-[var(--text-muted)] font-mono">
                Your determination will be permanently committed to the central audit ledger.
              </p>
            </div>

            <div className="space-y-3 bg-black/60 p-5 rounded-xl border border-white/10 text-sm font-mono">
              <span className="text-xs text-[var(--text-dim)] uppercase tracking-wider block">
                PRIMARY ACCUSED SECTOR:
              </span>
              <div className="font-orbitron font-bold text-lg text-white">
                {selectedSuspect?.name}
              </div>
              <div className="text-xs text-[var(--neon-light)]">
                Lead: {selectedSuspect?.lead_name} ({selectedSuspect?.timeline_sector})
              </div>
            </div>

            <div className="flex items-center gap-4 pt-2">
              <button
                type="button"
                onClick={executeFinalSubmission}
                disabled={isSubmitting}
                className="flex-1 py-4 rounded-xl font-orbitron font-black text-sm text-white tracking-wider transition-all cursor-pointer shadow-lg"
                style={{
                  background: 'var(--neon-gradient)',
                  boxShadow: '0 0 25px var(--neon-glow)'
                }}
              >
                {isSubmitting ? "TRANSMITTING VERDICT..." : "CONFIRM & LOCK VERDICT"}
              </button>

              <button
                type="button"
                onClick={() => setIsConfirmModalOpen(false)}
                className="px-6 py-4 rounded-xl bg-white/5 border border-white/15 text-[var(--text-muted)] hover:text-white font-mono text-sm cursor-pointer"
              >
                Cancel
              </button>
            </div>

          </div>
        </div>
      )}

      {/* =====================================================================
          5. RULES MODAL
      ====================================================================== */}
      {showBriefingModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/85 backdrop-blur-md">
          <div className="game-card max-w-lg w-full p-8 border-white/20 bg-[var(--bg-surface)] space-y-6">
            <div className="flex items-center justify-between pb-3 border-b border-white/15">
              <h3 className="font-orbitron font-black text-xl text-white">Round 3 Protocols</h3>
              <button onClick={() => setShowBriefingModal(false)} className="text-[var(--text-muted)] hover:text-white cursor-pointer">
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="space-y-4 text-sm text-[var(--text-body)] leading-relaxed font-space">
              <p>
                <strong className="text-white">1. Candidate Sectors:</strong> Evaluate Project Alpha, Project Beta, and Project Gamma using telemetry gathered throughout the event.
              </p>
              <p>
                <strong className="text-white">2. Supporting Evidence:</strong> Cross-reference the Round 2 audit files shown on the right to corroborate your verdict.
              </p>
              <p>
                <strong className="text-white">3. Untimed Protocol:</strong> Take as much time as required to verify timestamps and access tokens.
              </p>
              <p>
                <strong className="text-white">4. Single Commitment:</strong> Once submitted, the decision is permanent. Results are announced at the closing ceremony.
              </p>
            </div>

            <button
              onClick={() => setShowBriefingModal(false)}
              className="w-full py-3.5 rounded-xl font-orbitron font-bold text-sm text-white cursor-pointer"
              style={{ background: 'var(--neon-gradient)' }}
            >
              ACKNOWLEDGE
            </button>
          </div>
        </div>
      )}

    </div>
  );
}

