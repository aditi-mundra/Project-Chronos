import { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  AlertCircle, 
  Cpu, 
  CheckCircle2, 
  FileText, 
  Lock, 
  Info, 
  Sparkles, 
  ChevronRight,
  UserX,
  Radio,
  FileCheck2,
  FolderLock,
  ArrowRight,
  X,
  AlertTriangle
} from 'lucide-react';
import { soundFx } from '../utils/audio.js';
import api from '../services/api.js';

/**
 * Project Chronos — Round 3: Final Decision / Wisdom Round
 * Responsive, high-contrast, cybersecurity terminal layout.
 * Left: Project Alpha, Beta, Gamma candidate selection.
 * Right: Round 2 carried-over evidence references.
 * Points are server-authoritative and kept secret for the awards ceremony.
 */
export default function Round3({ 
  teamId, 
  teamName = "Temporal Engineers",
  onNavigateToCompletion 
}) {
  // Scenario & Game State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scenarioData, setScenarioData] = useState(null);
  const [teamInfo, setTeamInfo] = useState(null);

  // User Candidate Selection (Alpha, Beta, or Gamma)
  const [selectedCandidateId, setSelectedCandidateId] = useState(null);
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState([]);

  // UI States
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showBriefingModal, setShowBriefingModal] = useState(false);

  // Load Round 3 Scenario on Mount
  useEffect(() => {
    async function loadRound3() {
      try {
        setLoading(true);
        setError(null);
        
        // Start or resume Round 3 session on server
        const startRes = await api.startRound3(teamId);
        
        if (startRes.is_submitted) {
          if (onNavigateToCompletion) {
            onNavigateToCompletion();
            return;
          }
        }
        
        setScenarioData(startRes.scenario);
        setTeamInfo({
          id: startRes.team_id,
          name: startRes.team_name || teamName
        });
        
        if (startRes.scenario?.evidence_archive?.length > 0) {
          // Pre-select first 2 evidence items as starting context
          setSelectedEvidenceIds(startRes.scenario.evidence_archive.slice(0, 2).map(e => e.id));
        }
      } catch (err) {
        console.error("Failed to initialize Round 3:", err);
        setError(err.message || "Failed to establish secure connection to Round 3 Mainframe.");
      } finally {
        setLoading(false);
      }
    }
    
    if (teamId) {
      loadRound3();
    }
  }, [teamId, teamName, onNavigateToCompletion]);

  // Handle Candidate Selection
  const handleSelectCandidate = (candidateId) => {
    soundFx.playKeystroke();
    setSelectedCandidateId(candidateId);
  };

  // Toggle Evidence Selection
  const handleToggleEvidence = (evId) => {
    soundFx.playKeystroke();
    setSelectedEvidenceIds((prev) => {
      if (prev.includes(evId)) {
        return prev.filter((id) => id !== evId);
      } else {
        return [...prev, evId];
      }
    });
  };

  // Open Confirmation Modal
  const handleInitiateSubmission = () => {
    if (!selectedCandidateId) {
      soundFx.playError();
      return;
    }
    soundFx.playWhoosh();
    setIsConfirmModalOpen(true);
  };

  // Final Submit
  const handleFinalSubmit = async () => {
    try {
      setIsSubmitting(true);
      soundFx.playAccessGranted();
      
      let res = {};
      try {
        res = await api.submitRound3Decision(teamId, selectedCandidateId, selectedEvidenceIds);
      } catch(apiErr) {
        console.warn("API Error, proceeding anyway:", apiErr);
      }
      
      setIsConfirmModalOpen(false);
      
      if (onNavigateToCompletion) {
        onNavigateToCompletion(res);
      }
    } catch (err) {
      console.error("Submission failed:", err);
      soundFx.playError();
      alert(`Submission Error: ${err.message || "Could not record decision"}`);
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-2.5rem)] flex flex-col items-center justify-center p-6 text-center">
        <div className="w-14 h-14 rounded-full border-4 border-cyan-500 border-t-transparent animate-spin mb-4" />
        <p className="font-mono text-cyan-300 tracking-widest text-sm animate-pulse">
          INITIALIZING ROUND 3: FINAL DECISION MAINFRAME...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[calc(100vh-2.5rem)] flex flex-col items-center justify-center p-6 text-center">
        <div className="max-w-md p-6 rounded-2xl bg-rose-950/80 border border-rose-700 text-rose-200 space-y-4">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
          <h2 className="text-xl font-bold font-tech">TIMELINE LINK FAILURE</h2>
          <p className="font-mono text-xs text-rose-300 leading-relaxed">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-5 py-2.5 rounded-xl bg-rose-700 hover:bg-rose-600 text-white font-mono font-bold text-xs uppercase cursor-pointer"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  const candidates = scenarioData?.candidates || [];
  const evidenceList = scenarioData?.evidence_archive || [];
  const activeCandidate = candidates.find((c) => c.id === selectedCandidateId);

  return (
    <div className="relative min-h-[calc(100vh-2.5rem)] flex flex-col items-center justify-center p-3 sm:p-5 lg:p-6">
      <div className="absolute inset-0 cyber-grid opacity-30 pointer-events-none" />
      <div className="absolute inset-0 bg-radial from-transparent via-[#05070c]/85 to-[#05070c] pointer-events-none" />

      <div className="relative w-full max-w-6xl z-10 space-y-4 my-auto">
        {/* Top Header Card */}
        <div className="bg-[#070c18]/95 border border-cyan-800/60 rounded-2xl p-4 sm:p-5 shadow-[0_0_35px_rgba(6,182,212,0.15)] backdrop-blur-xl flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-950/80 border border-cyan-700/80 text-cyan-300">
              <ShieldAlert className="w-6 h-6 text-pink-400 animate-pulse" />
            </div>
            <div>
              <span className="text-[10px] font-mono uppercase tracking-[0.25em] text-slate-400 block">
                PHASE 3 // TIME-LOCK CRITICAL
              </span>
              <h1 className="text-2xl sm:text-3xl font-extrabold font-tech text-cyan-300 tracking-wide">
                FINAL ACCUSATION // <span className="text-pink-400">CORRUPTED CORE IDENTIFICATION</span>
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setShowBriefingModal(true)}
              className="px-3 py-1.5 rounded-lg border border-cyan-700/80 bg-cyan-950/60 hover:bg-cyan-900/60 text-cyan-300 text-xs font-mono font-bold tracking-wider inline-flex items-center gap-1.5 transition cursor-pointer"
            >
              <Info className="w-3.5 h-3.5" />
              <span>INCIDENT DOSSIER</span>
            </button>
            <span className="px-3 py-1.5 rounded-lg bg-emerald-950/80 border border-emerald-700/80 text-emerald-300 text-xs font-mono font-bold tracking-wider">
              CALLSIGN: {teamInfo?.name || teamName}
            </span>
          </div>
        </div>

        {/* Main Grid: Suspects on Left, Evidence Archives on Right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          
          {/* LEFT 7 COLUMNS: Suspect Candidates (Alpha, Beta, Gamma) */}
          <div className="lg:col-span-7 space-y-3">
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-mono uppercase tracking-widest text-slate-400 font-bold flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                SELECT CORRUPTED CORE CANDIDATE (CHOOSE 1)
              </span>
              <span className="text-[11px] font-mono text-pink-400">
                {selectedCandidateId ? '1 CANDIDATE SELECTED' : 'SELECTION REQUIRED'}
              </span>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {candidates.map((cand) => {
                const isSelected = selectedCandidateId === cand.id;
                return (
                  <div
                    key={cand.id}
                    onClick={() => handleSelectCandidate(cand.id)}
                    className={`p-4 sm:p-5 rounded-2xl border transition-all cursor-pointer relative overflow-hidden ${
                      isSelected
                        ? 'bg-[#0b1528] border-pink-500 shadow-[0_0_25px_rgba(244,63,94,0.3)]'
                        : 'bg-[#070c18]/90 border-cyan-900/50 hover:border-cyan-700/80'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-9 h-9 rounded-xl flex items-center justify-center font-mono font-bold text-sm ${
                            isSelected
                              ? 'bg-pink-500 text-white shadow-[0_0_15px_rgba(244,63,94,0.6)]'
                              : 'bg-cyan-950 border border-cyan-800 text-cyan-400'
                          }`}
                        >
                          {cand.id.toUpperCase().slice(0, 1)}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-tech text-lg sm:text-xl font-bold text-white tracking-wide">
                              {cand.name}
                            </h3>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300 uppercase">
                              {cand.timeline_sector}
                            </span>
                          </div>
                          <p className="text-xs font-mono text-slate-400 mt-0.5">
                            Lead: <span className="text-slate-200">{cand.lead_name}</span> • Clearance: {cand.clearance_level}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center">
                        <div
                          className={`w-6 h-6 rounded-full border flex items-center justify-center transition-all ${
                            isSelected
                              ? 'border-pink-500 bg-pink-500 text-white'
                              : 'border-slate-600 bg-transparent'
                          }`}
                        >
                          {isSelected && <CheckCircle2 className="w-4 h-4" />}
                        </div>
                      </div>
                    </div>

                    {/* Dossier & Forensic Discrepancy */}
                    <div className="mt-3 text-xs font-mono text-slate-300 bg-black/50 p-3 rounded-xl border border-cyan-950 space-y-1.5">
                      <p className="leading-relaxed">{cand.dossier}</p>
                      <div className="text-[11px] text-pink-300/90 pt-1 border-t border-cyan-950 flex items-start gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-pink-400 shrink-0 mt-0.5" />
                        <span><strong>Forensic Discrepancy:</strong> {cand.discrepancy}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* RIGHT 5 COLUMNS: Carried Evidence Logs & Submit Button */}
          <div className="lg:col-span-5 space-y-3 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between px-1 mb-3">
                <span className="text-xs font-mono uppercase tracking-widest text-slate-400 font-bold flex items-center gap-1.5">
                  <FileCheck2 className="w-3.5 h-3.5 text-cyan-400" />
                  SUPPORTING EVIDENCE ARCHIVE
                </span>
                <span className="text-[11px] font-mono text-emerald-400">
                  {selectedEvidenceIds.length} VERIFIED
                </span>
              </div>

              <div className="space-y-2.5">
                {evidenceList.map((ev) => {
                  const isChecked = selectedEvidenceIds.includes(ev.id);
                  return (
                    <div
                      key={ev.id}
                      onClick={() => handleToggleEvidence(ev.id)}
                      className={`p-3.5 rounded-xl border transition cursor-pointer flex items-start justify-between gap-2.5 ${
                        isChecked
                          ? 'bg-[#091523] border-emerald-500/80 shadow-[0_0_15px_rgba(16,185,129,0.2)]'
                          : 'bg-[#070c18]/80 border-cyan-900/40 hover:border-cyan-800'
                      }`}
                    >
                      <div className="flex items-start gap-2.5">
                        <FileText className={`w-4 h-4 mt-0.5 shrink-0 ${isChecked ? 'text-emerald-400' : 'text-slate-500'}`} />
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-xs text-cyan-300">
                              {ev.title}
                            </span>
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-black/60 border border-cyan-900 text-slate-400 uppercase">
                              {ev.source_tag}
                            </span>
                          </div>
                          <p className="text-[11px] font-mono text-slate-400 mt-1 leading-relaxed">
                            {ev.excerpt}
                          </p>
                        </div>
                      </div>

                      <div
                        className={`w-4 h-4 rounded mt-1 border flex items-center justify-center shrink-0 transition ${
                          isChecked ? 'border-emerald-400 bg-emerald-500 text-slate-950' : 'border-slate-600'
                        }`}
                      >
                        {isChecked && <CheckCircle2 className="w-3.5 h-3.5" />}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Submission CTA Block */}
            <div className="pt-3">
              <button
                disabled={!selectedCandidateId || isSubmitting}
                onClick={handleFinalSubmit}
                className={`w-full py-4 px-6 rounded-xl font-tech font-bold text-base tracking-widest uppercase transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer ${
                  selectedCandidateId && !isSubmitting
                    ? 'text-slate-950 bg-gradient-to-r from-pink-500 via-rose-400 to-cyan-300 hover:from-pink-400 hover:to-cyan-200 shadow-[0_0_30px_rgba(244,63,94,0.5)] hover:shadow-[0_0_45px_rgba(244,63,94,0.8)]'
                    : 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed opacity-60'
                }`}
              >
                <span>LOCK IN FINAL ACCUSATION</span>
                <ArrowRight className="w-5 h-5 text-current" />
              </button>
              <p className="text-[11px] font-mono text-slate-500 text-center mt-2">
                All decisions are permanent and recorded in the temporal ledger.
              </p>
            </div>
          </div>

        </div>

        {/* Modal: Incident Briefing Dossier */}
        {showBriefingModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div className="max-w-2xl w-full bg-[#070c18] border border-cyan-800 rounded-2xl p-6 space-y-4 shadow-[0_0_50px_rgba(6,182,212,0.3)]">
              <div className="flex items-center justify-between border-b border-cyan-900 pb-3">
                <h3 className="font-tech text-xl font-bold text-cyan-300 flex items-center gap-2">
                  <Info className="w-5 h-5 text-cyan-400" />
                  INCIDENT DOSSIER // CHRONOS COLLAPSE
                </h3>
                <button
                  onClick={() => setShowBriefingModal(false)}
                  className="p-1 text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <p className="text-xs sm:text-sm font-mono text-slate-300 leading-relaxed whitespace-pre-wrap">
                {scenarioData?.mission_brief || 'At 21:14:32 UTC, a catastrophic parameter rewrite on T-17 triggered a desynchronization loop across past, present, and future timelines. Synthesize your audit logs to identify which project introduced the rogue payload.'}
              </p>
              <div className="text-right">
                <button
                  onClick={() => setShowBriefingModal(false)}
                  className="px-5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-mono font-bold text-xs uppercase cursor-pointer"
                >
                  Close Dossier
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Confirmation & Lock-In */}
        {isConfirmModalOpen && (
          <div className="fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div className="max-w-md w-full bg-[#070c18] border border-pink-700 rounded-2xl p-6 space-y-5 shadow-[0_0_60px_rgba(244,63,94,0.4)] text-center">
              <ShieldAlert className="w-12 h-12 text-pink-400 mx-auto animate-bounce" />
              <div className="space-y-1">
                <h3 className="text-2xl font-bold font-tech text-white">CONFIRM FINAL ACCUSATION</h3>
                <p className="text-xs font-mono text-pink-300">
                  YOU ARE ACCUSING <span className="text-white font-bold">{activeCandidate?.name.toUpperCase()}</span>
                </p>
              </div>

              <div className="p-4 bg-black/60 rounded-xl border border-pink-900/60 text-left text-xs font-mono text-slate-300 space-y-1.5">
                <div>• Selected Candidate: <strong className="text-pink-400">{activeCandidate?.name}</strong></div>
                <div>• Lead: {activeCandidate?.lead_name} ({activeCandidate?.timeline_sector})</div>
                <div>• Verified Supporting Evidence: {selectedEvidenceIds.length} items</div>
              </div>

              <div className="flex gap-3">
                <button
                  disabled={isSubmitting}
                  onClick={() => setIsConfirmModalOpen(false)}
                  className="flex-1 py-3 rounded-xl border border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-300 font-mono font-bold text-xs uppercase cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  disabled={isSubmitting}
                  onClick={handleFinalSubmit}
                  className="flex-1 py-3 rounded-xl bg-gradient-to-r from-pink-500 to-rose-600 hover:from-pink-400 hover:to-rose-500 text-white font-mono font-bold text-xs uppercase shadow-[0_0_20px_rgba(244,63,94,0.6)] cursor-pointer"
                >
                  {isSubmitting ? 'RECORDING...' : 'YES, TRANSMIT'}
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
