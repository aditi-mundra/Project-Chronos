import { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  AlertCircle, 
  Cpu, 
  CheckCircle2, 
  FileText, 
  Info, 
  FileCheck2, 
  ArrowRight, 
  X, 
  Bot,
  ExternalLink,
  User
} from 'lucide-react';
import { soundFx } from '../utils/audio.js';
import api from '../services/api.js';
import { useAuth } from '../context/AuthContext.jsx';

/**
 * Project Chronos — Round 3: Final Decision / Wisdom Round
 * Responsive, high-contrast, cybersecurity terminal layout.
 * Left: Candidate Suspect Selection.
 * Right: Connected Round 2 Findings (AI Analyst Q&As & Evidence File Logs).
 * Decision-making happens exclusively in Round 3.
 */
export default function Round3({ 
  teamId, 
  teamName = "Temporal Engineers",
  onNavigateToCompletion 
}) {
  const { updateTeamState } = useAuth();
  // Scenario & Game State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scenarioData, setScenarioData] = useState(null);
  const [teamInfo, setTeamInfo] = useState(null);

  // User Candidate Selection (Project Alpha, Beta, or Gamma)
  const [selectedCandidateId, setSelectedCandidateId] = useState(null);

  // Right Panel Tabs: 'evidence_logs' | 'ai_inquiries'
  const [activeRightTab, setActiveRightTab] = useState('evidence_logs');

  // UI States
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState(null);
  const [showBriefingModal, setShowBriefingModal] = useState(false);
  const [viewingFileModal, setViewingFileModal] = useState(null);

  // Load Round 3 Scenario on Mount
  useEffect(() => {
    async function loadRound3() {
      try {
        setLoading(true);
        setError(null);
        
        // Start or resume Round 3 session on server
        const startRes = await api.startRound3(teamId);
        
        if (startRes.is_submitted) {
          if (updateTeamState) {
            updateTeamState('COMPLETED');
          }
          if (onNavigateToCompletion) {
            onNavigateToCompletion();
            return;
          }
        }
        
        const scen = startRes.scenario || startRes.case || {};
        if (startRes.round2_investigation && !scen.round2_investigation) {
          scen.round2_investigation = startRes.round2_investigation;
        }

        const chatMsgs = scen?.round2_investigation?.chat_messages || startRes?.round2_investigation?.chat_messages || [];
        if (chatMsgs && chatMsgs.length > 0) {
          setActiveRightTab('ai_inquiries');
        }

        setScenarioData(scen);
        setTeamInfo({
          id: startRes.team_id,
          name: startRes.team_name || teamName
        });
        
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
    setSubmissionError(null);
    setSelectedCandidateId(candidateId);
  };

  // Open Confirmation Modal
  const handleInitiateSubmission = () => {
    if (!selectedCandidateId) {
      soundFx.playError();
      setSubmissionError('Select the suspect responsible for the timeline anomaly.');
      return;
    }
    soundFx.playWhoosh();
    setIsConfirmModalOpen(true);
  };

  // Final Submit
  const handleFinalSubmit = async () => {
    try {
      setIsSubmitting(true);
      setSubmissionError(null);
      
      const res = await api.submitRound3Decision(teamId, selectedCandidateId, []);
      soundFx.playAccessGranted();
      
      setIsConfirmModalOpen(false);
      
      if (updateTeamState) {
        updateTeamState('COMPLETED');
      }

      if (onNavigateToCompletion) {
        onNavigateToCompletion(res);
      }
    } catch (err) {
      console.error("Submission failed:", err);
      soundFx.playError();
      setSubmissionError(err.message || "Could not record decision");
      setIsConfirmModalOpen(false);
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
  const evidenceList = scenarioData?.evidence_archive || scenarioData?.evidence_pool || [];
  const r2Invest = scenarioData?.round2_investigation || {};
  const chatMessages = r2Invest.chat_messages || [];
  const activeCandidate = candidates.find((c) => c.id === selectedCandidateId || c.user_id === selectedCandidateId);

  return (
    <div className="relative min-h-[calc(100vh-2.5rem)] flex flex-col items-center justify-center p-3 sm:p-5 lg:p-6">
      <div className="absolute inset-0 cyber-grid opacity-30 pointer-events-none" />
      <div className="absolute inset-0 bg-radial from-transparent via-[#05070c]/85 to-[#05070c] pointer-events-none" />

      <div className="relative w-full max-w-7xl z-10 space-y-4 my-auto">
        {/* Top Header Card */}
        <div className="bg-[#070c18]/95 border border-cyan-800/60 rounded-2xl p-4 sm:p-5 shadow-[0_0_35px_rgba(6,182,212,0.15)] backdrop-blur-xl flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-950/80 border border-cyan-700/80 text-cyan-300">
              <ShieldAlert className="w-6 h-6 text-pink-400 animate-pulse" />
            </div>
            <div>
              <span className="text-[10px] font-mono uppercase tracking-[0.25em] text-slate-400 block">
                ROUND 3 // FINAL DECISION
              </span>
              <h1 className="text-2xl sm:text-3xl font-extrabold font-tech text-cyan-300 tracking-wide">
                FINAL ACCUSATION
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
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

        {/* Main Grid: Suspects on Left (7 cols), Round 2 Telemetry & Evidence on Right (5 cols) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          
          {/* LEFT 7 COLUMNS: Suspect Candidates (Real Suspects from Round 2) */}
          <div className="lg:col-span-7 space-y-3">
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-mono uppercase tracking-widest text-slate-400 font-bold flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                SELECT ACCUSED SUSPECT
              </span>
              <span className="text-[11px] font-mono text-pink-400">
                {selectedCandidateId ? '1 SUSPECT SELECTED' : 'SELECTION REQUIRED'}
              </span>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {candidates.map((cand) => {
                const isSelected = selectedCandidateId === cand.id || selectedCandidateId === cand.user_id;
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
                          className={`min-w-10 h-10 px-2 rounded-xl flex items-center justify-center font-mono font-bold text-xs ${
                            isSelected
                              ? 'bg-pink-500 text-white shadow-[0_0_15px_rgba(244,63,94,0.6)]'
                              : 'bg-cyan-950 border border-cyan-800 text-cyan-400'
                          }`}
                        >
                          {cand.user_id || cand.id}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-tech text-xl sm:text-2xl font-bold text-cyan-300 tracking-wide">
                              {cand.name}
                            </h3>
                          </div>
                          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mt-0.5">
                            <span className="text-cyan-400 font-semibold">{cand.role || cand.designation}</span>
                            <span className="text-slate-600">•</span>
                            <span>ID: {cand.user_id || cand.id}</span>
                          </div>
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

                  </div>
                );
              })}
            </div>
          </div>

          {/* RIGHT 5 COLUMNS: Connected Round 2 Findings (Evidence Logs & AI Analyst Q&As) */}
          <div className="lg:col-span-5 space-y-3 flex flex-col justify-between">
            <div>
              {/* Tab Selector */}
              <div className="flex items-center gap-1.5 p-1 bg-[#05070c] border border-cyan-900/60 rounded-xl mb-3">
                <button
                  type="button"
                  onClick={() => {
                    soundFx.playKeystroke();
                    setActiveRightTab('evidence_logs');
                  }}
                  className={`flex-1 py-1.5 px-2.5 rounded-lg font-mono text-xs font-bold transition flex items-center justify-center gap-1.5 cursor-pointer ${
                    activeRightTab === 'evidence_logs'
                      ? 'bg-cyan-600 text-slate-950 shadow-[0_0_12px_rgba(6,182,212,0.4)]'
                      : 'text-slate-400 hover:text-cyan-300'
                  }`}
                >
                  <FileCheck2 className="w-3.5 h-3.5" />
                  <span>EVIDENCE LOGS ({evidenceList.length})</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    soundFx.playKeystroke();
                    setActiveRightTab('ai_inquiries');
                  }}
                  className={`flex-1 py-1.5 px-2.5 rounded-lg font-mono text-xs font-bold transition flex items-center justify-center gap-1.5 cursor-pointer relative ${
                    activeRightTab === 'ai_inquiries'
                      ? 'bg-cyan-600 text-slate-950 shadow-[0_0_12px_rgba(6,182,212,0.4)]'
                      : 'text-slate-400 hover:text-cyan-300'
                  }`}
                >
                  <Bot className="w-3.5 h-3.5" />
                  <span>ANALYST Q&A ({chatMessages.length})</span>
                  {chatMessages.length > 0 && (
                    <span className="relative flex h-2 w-2 ml-1">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                  )}
                </button>
              </div>

              {/* TAB 1: Supporting Evidence Logs */}
              {activeRightTab === 'evidence_logs' && (
                <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
                  <div className="text-[11px] font-mono text-slate-400 px-1">
                    ROUND 2 EVIDENCE ARCHIVE & LOGS
                  </div>

                  {evidenceList.map((ev) => (
                      <div
                        key={ev.id}
                        className="p-3.5 rounded-xl border border-cyan-900/40 bg-[#070c18]/80 flex flex-col gap-2"
                      >
                        <div className="flex items-start justify-between gap-2.5">
                          <div className="flex items-start gap-2.5 flex-1">
                            <FileText className="w-4 h-4 mt-0.5 shrink-0 text-cyan-500" />
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-mono font-bold text-xs text-cyan-300">
                                  {ev.title || ev.label || ev.source_file}
                                </span>
                                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-black/60 border border-cyan-900 text-slate-400 uppercase">
                                  {ev.source_tag || ev.category || 'LOG'}
                                </span>
                              </div>
                              <p className="text-[11px] font-mono text-slate-400 mt-1 leading-relaxed">
                                {ev.excerpt || ev.description}
                              </p>
                            </div>
                          </div>

                        </div>

                        {/* Full Text Expander if available */}
                        {ev.full_text && (
                          <div className="text-right pt-1 border-t border-cyan-950/60">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                soundFx.playWhoosh();
                                setViewingFileModal(ev);
                              }}
                              className="text-[10px] font-mono text-cyan-400 hover:text-cyan-200 inline-flex items-center gap-1 cursor-pointer"
                            >
                              <span>READ FULL LOG</span>
                              <ExternalLink className="w-3 h-3" />
                            </button>
                          </div>
                        )}
                      </div>
                  ))}
                </div>
              )}

              {/* TAB 2: Round 2 AI Analyst Inquiries & API Responses */}
              {activeRightTab === 'ai_inquiries' && (
                <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 px-2 py-1.5 bg-cyan-950/40 rounded-lg border border-cyan-900/50">
                    <span className="flex items-center gap-1.5 text-cyan-300 font-bold">
                      <Bot className="w-3.5 h-3.5 text-cyan-400" />
                      ROUND 2 INTERROGATION TRANSCRIPT
                    </span>
                    <span className="text-emerald-400 font-bold font-mono">
                      {chatMessages.length} / 3 INQUIRIES LOGGED
                    </span>
                  </div>

                  {chatMessages.length === 0 ? (
                    <div className="p-6 rounded-2xl bg-[#070c18] border border-cyan-900/60 text-center space-y-2">
                      <Bot className="w-8 h-8 text-cyan-400 mx-auto opacity-70" />
                      <div className="font-tech text-white font-bold text-sm">NO AI INQUIRIES FILED</div>
                      <p className="text-xs font-mono text-slate-400 leading-relaxed">
                        Team asked no analyst questions during Round 2. Check the Evidence Logs tab for audit trails.
                      </p>
                    </div>
                  ) : (
                    chatMessages.map((msg, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 sm:p-4 rounded-xl bg-[#070c18]/95 border border-cyan-800/60 space-y-3 shadow-md"
                      >
                        <div className="flex items-center justify-between border-b border-cyan-950 pb-2">
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-700 text-cyan-300 uppercase font-bold tracking-wider">
                            INQUIRY #{msg.question_number || idx + 1} OF 3
                          </span>
                          <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block"></span>
                            ROUND 2 RECORD
                          </span>
                        </div>

                        {/* Team Question */}
                        <div className="text-xs font-mono bg-black/60 p-2.5 sm:p-3 rounded-lg border border-cyan-950 space-y-1">
                          <span className="text-cyan-400 font-bold flex items-center gap-1 text-[10px] tracking-wider uppercase">
                            <User className="w-3 h-3 text-cyan-400" />
                            TEAM QUESTION:
                          </span>
                          <p className="italic text-slate-200 leading-relaxed">"{msg.user_prompt}"</p>
                        </div>

                        {/* AI Analyst Response */}
                        <div className="bg-cyan-950/25 p-3 sm:p-3.5 rounded-lg border border-cyan-900/50 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-emerald-400 font-bold text-[10px] font-mono tracking-wider flex items-center gap-1.5">
                              <Bot className="w-3.5 h-3.5 text-emerald-400" />
                              CHRONOS AI ANALYST ASSESSMENT:
                            </span>
                          </div>
                          <p className="text-xs sm:text-[13px] font-sans text-slate-100 leading-relaxed whitespace-pre-wrap">
                            {msg.ai_response || "(No response recorded)"}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* Submission CTA Block */}
            <div className="pt-3">
              <button
                type="button"
                disabled={isSubmitting}
                onClick={handleInitiateSubmission}
                className={`w-full py-4 px-6 rounded-xl font-tech font-bold text-base tracking-widest uppercase transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer ${
                  selectedCandidateId && !isSubmitting
                    ? 'text-slate-950 bg-gradient-to-r from-pink-500 via-rose-400 to-cyan-300 hover:from-pink-400 hover:to-cyan-200 shadow-[0_0_30px_rgba(244,63,94,0.5)] hover:shadow-[0_0_45px_rgba(244,63,94,0.8)]'
                    : 'bg-slate-800 text-slate-300 border border-slate-600 hover:border-rose-500 hover:text-rose-300'
                }`}
              >
                <span>LOCK IN FINAL ACCUSATION</span>
                <ArrowRight className="w-5 h-5 text-current" />
              </button>
              <p className="text-[11px] font-mono text-slate-500 text-center mt-2">
                {!selectedCandidateId
                  ? 'Select a suspect above to lock in your final accusation.'
                  : 'Ready to submit final accusation.'}
              </p>
              {submissionError && (
                <p className="text-xs font-mono text-rose-400 text-center mt-2" role="alert">
                  {submissionError}
                </p>
              )}
            </div>
          </div>

        </div>

        {/* Modal: Full Evidence Text Viewer */}
        {viewingFileModal && (
          <div className="fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div className="max-w-3xl w-full bg-[#070c18] border border-cyan-800 rounded-2xl p-6 space-y-4 shadow-[0_0_50px_rgba(6,182,212,0.3)] max-h-[85vh] flex flex-col">
              <div className="flex items-center justify-between border-b border-cyan-900 pb-3">
                <div>
                  <h3 className="font-tech text-xl font-bold text-cyan-300">
                    {viewingFileModal.title || viewingFileModal.filename}
                  </h3>
                  <span className="text-[11px] font-mono text-slate-400 uppercase">
                    {viewingFileModal.source_tag || viewingFileModal.category}
                  </span>
                </div>
                <button
                  onClick={() => setViewingFileModal(null)}
                  className="p-1 text-slate-400 hover:text-white cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto bg-black/60 p-4 rounded-xl border border-cyan-950 font-mono text-xs text-slate-200 whitespace-pre-wrap leading-relaxed">
                {viewingFileModal.full_text}
              </div>

              <div className="text-right">
                <button
                  onClick={() => setViewingFileModal(null)}
                  className="px-5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-mono font-bold text-xs uppercase cursor-pointer"
                >
                  Close Document
                </button>
              </div>
            </div>
          </div>
        )}

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
                  className="p-1 text-slate-400 hover:text-white cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <p className="text-xs sm:text-sm font-mono text-slate-300 leading-relaxed whitespace-pre-wrap">
                {scenarioData?.mission_brief || scenarioData?.incident_brief || 'Synthesize your Round 2 audit logs, access history, and Analyst interrogation responses to identify which suspect was responsible for the timeline collapse.'}
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
                  YOU ARE SELECTING <span className="text-white font-bold">{activeCandidate?.name?.toUpperCase()}</span>
                </p>
              </div>

              <div className="p-4 bg-black/60 rounded-xl border border-pink-900/60 text-left text-xs font-mono text-slate-300 space-y-1.5">
                <div>• Accused Suspect: <strong className="text-pink-400">{activeCandidate?.name}</strong></div>
                <div>• Role: <span className="text-cyan-300">{activeCandidate?.role || activeCandidate?.designation}</span></div>
                <div>• User ID: <span className="text-slate-300">{activeCandidate?.user_id || activeCandidate?.id}</span></div>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  disabled={isSubmitting}
                  onClick={() => setIsConfirmModalOpen(false)}
                  className="flex-1 py-3 rounded-xl border border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-300 font-mono font-bold text-xs uppercase cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={isSubmitting}
                  onClick={handleFinalSubmit}
                  className="flex-1 py-3 rounded-xl bg-gradient-to-r from-pink-500 to-rose-600 hover:from-pink-400 hover:to-rose-500 text-white font-mono font-bold text-xs uppercase shadow-[0_0_20px_rgba(244,63,94,0.6)] cursor-pointer"
                >
                  {isSubmitting ? 'TRANSMITTING...' : 'YES, TRANSMIT'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Full-Screen Transition HUD Overlay when transmitting */}
        {isSubmitting && (
          <div className="fixed inset-0 z-[60] bg-[#05070c]/95 backdrop-blur-xl flex flex-col items-center justify-center p-6 text-center space-y-5 animate-fadeIn">
            <div className="w-16 h-16 rounded-full border-4 border-cyan-400 border-t-pink-500 animate-spin shadow-[0_0_40px_rgba(6,182,212,0.7)]" />
            <div className="space-y-2">
              <span className="px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-500/50 text-cyan-300 font-mono text-[10px] tracking-widest uppercase inline-block">
                TEMPORAL PROTOCOL // LOCKING
              </span>
              <h3 className="font-orbitron font-bold text-2xl text-white tracking-widest">
                LOCKING PARADOX COORDINATES...
              </h3>
              <p className="font-mono text-xs text-cyan-400 tracking-widest max-w-md">
                TRANSMITTING VERDICT TO CHRONOS MAINFRAME • INITIATING TIMELINE CONVERGENCE
              </p>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
