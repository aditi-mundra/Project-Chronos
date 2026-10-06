import { useState, useEffect } from 'react';
import { 
  Trophy, 
  Download, 
  Search, 
  RefreshCw, 
  Users, 
  Award, 
  Activity, 
  Clock, 
  ArrowLeft,
  ShieldCheck,
  Trash2,
  AlertTriangle,
  ShieldAlert,
  Lock,
  X,
  CheckCircle
} from 'lucide-react';
import api from '../services/api.js';
import { soundFx } from '../utils/audio.js';

/**
 * Master Host Leaderboard View
 * Real-time team rankings, statistics, PRN lookups, CSV export, and database purge control.
 */
export default function Leaderboard({ onBack }) {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState(null);

  // Clear Database State (Two Warnings + Password 'admin')
  const [clearDbStep, setClearDbStep] = useState(0); // 0: Closed, 1: Warning 1, 2: Warning 2
  const [adminPassword, setAdminPassword] = useState('');
  const [clearDbLoading, setClearDbLoading] = useState(false);
  const [clearDbError, setClearDbError] = useState('');
  const [clearDbSuccess, setClearDbSuccess] = useState('');

  const fetchLeaderboard = async () => {
    try {
      const data = await api.getAdminLeaderboard();
      setTeams(Array.isArray(data) ? data : []);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Failed to fetch leaderboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return undefined;
    const interval = setInterval(fetchLeaderboard, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleExportCsv = () => {
    soundFx.playAccessGranted();
    if (!teams.length) {
      alert('No leaderboard data available to export.');
      return;
    }

    const headers = [
      'Rank',
      'Team Name',
      'Operator 1',
      'PRN 1',
      'Operator 2',
      'PRN 2',
      'Round 1 Score',
      'Round 1 Time (s)',
      'Round 1 Time Formatted',
      'Round 1 Auth Code',
      'Round 2 Score',
      'Round 3 Score',
      'Total Score',
      'Status'
    ];

    const rows = teams.map((t) => [
      t.rank,
      `"${(t.team_name || '').replace(/"/g, '""')}"`,
      `"${(t.member_1_name || t.member1_name || '').replace(/"/g, '""')}"`,
      `"${(t.member_1_prn || t.member1_prn || '').replace(/"/g, '""')}"`,
      `"${(t.member_2_name || t.member2_name || '').replace(/"/g, '""')}"`,
      `"${(t.member_2_prn || t.member2_prn || '').replace(/"/g, '""')}"`,
      t.round1_score ?? t.r1_score ?? 0,
      t.r1_time_diff != null ? t.r1_time_diff : '',
      `"${t.r1_time_formatted || '--:--'}"`,
      `"${t.round1_auth_code || ''}"`,
      t.round2_score ?? t.r2_score ?? 0,
      t.round3_score ?? t.r3_score ?? 0,
      t.total_score ?? 0,
      `"${t.status || 'ACTIVE'}"`
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `chronos_master_leaderboard_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleStartClearDb = () => {
    soundFx.playKeystroke();
    setClearDbError('');
    setClearDbSuccess('');
    setAdminPassword('');
    setClearDbStep(1); // Warning 1
  };

  const handleProceedToStep2 = () => {
    soundFx.playKeystroke();
    setClearDbStep(2); // Warning 2
  };

  const handleAbortClearDb = () => {
    soundFx.playKeystroke();
    setClearDbStep(0);
    setAdminPassword('');
    setClearDbError('');
  };

  const handleConfirmClearDb = async (e) => {
    if (e) e.preventDefault();
    const cleanPw = (adminPassword || '').trim().replace(/^["']|["']$/g, '');
    if (!cleanPw) {
      setClearDbError('Password is required.');
      soundFx.playError();
      return;
    }
    try {
      setClearDbLoading(true);
      setClearDbError('');
      const res = await api.clearDatabase(cleanPw);
      soundFx.playAccessGranted();
      setClearDbSuccess(res?.message || 'Database successfully cleared. All team records have been purged.');
      setClearDbStep(0);
      setAdminPassword('');
      await fetchLeaderboard();
    } catch (err) {
      soundFx.playError();
      const msg = err?.data?.detail || err?.message || 'Invalid administrator password. Clearance denied.';
      setClearDbError(msg);
    } finally {
      setClearDbLoading(false);
    }
  };

  const filteredTeams = teams.filter((t) => {
    const q = searchTerm.toLowerCase();
    return (
      (t.team_name || '').toLowerCase().includes(q) ||
      (t.member_1_name || t.member1_name || '').toLowerCase().includes(q) ||
      (t.member_2_name || t.member2_name || '').toLowerCase().includes(q) ||
      (t.member_1_prn || t.member1_prn || '').toLowerCase().includes(q) ||
      (t.member_2_prn || t.member2_prn || '').toLowerCase().includes(q)
    );
  });

  const totalRegistered = teams.length;
  const finishedTeams = teams.filter((t) => t.status === 'FINISHED' || t.current_state === 'COMPLETED').length;
  const activeTeams = totalRegistered - finishedTeams;
  const topScore = teams.length ? Math.max(...teams.map((t) => t.total_score || 0)) : 0;

  return (
    <div className="relative min-h-[calc(100vh-2.5rem)] flex flex-col p-4 sm:p-6 lg:p-8 space-y-6 font-mono">
      <div className="absolute inset-0 cyber-grid opacity-30 pointer-events-none" />
      <div className="absolute inset-0 bg-radial from-transparent via-[#05070c]/85 to-[#05070c] pointer-events-none" />

      {/* Header Bar */}
      <div className="relative z-10 bg-[#070c18]/95 border border-cyan-800/60 rounded-2xl p-5 sm:p-6 shadow-[0_0_40px_rgba(6,182,212,0.15)] backdrop-blur-xl flex flex-col lg:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {onBack && (
            <button
              onClick={() => {
                soundFx.playWhoosh();
                onBack();
              }}
              className="p-2.5 rounded-xl bg-slate-900 border border-slate-700 hover:border-cyan-500 text-slate-300 hover:text-white transition cursor-pointer"
              title="Return to Game Terminal"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <div className="p-3 rounded-2xl bg-cyan-950/80 border border-cyan-500 text-cyan-300 shadow-[0_0_20px_rgba(6,182,212,0.4)]">
            <Trophy className="w-7 h-7 text-cyan-400" />
          </div>
          <div>
            <span className="text-[10px] uppercase tracking-[0.3em] text-slate-400 block">
              CHRONOS MAINFRAME // EVENT SUPERVISOR
            </span>
            <h1 className="text-2xl sm:text-3xl font-black font-tech text-white tracking-wide">
              MASTER <span className="text-cyan-400">LEADERBOARD</span>
            </h1>
          </div>
        </div>

        {/* Search & Export Buttons */}
        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search callsign or PRN..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-black/60 border border-cyan-900/80 focus:border-cyan-400 text-xs text-slate-200 placeholder:text-slate-500 outline-none"
            />
          </div>

          <button
            onClick={() => {
              soundFx.playKeystroke();
              fetchLeaderboard();
            }}
            className="px-3 py-2 rounded-xl bg-cyan-950/80 border border-cyan-700 text-cyan-300 hover:text-white text-xs font-bold flex items-center gap-1.5 transition cursor-pointer"
            title="Refresh Leaderboard"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>SYNC</span>
          </button>

          <button
            onClick={handleExportCsv}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 text-xs font-bold font-tech uppercase tracking-wider flex items-center gap-2 shadow-[0_0_20px_rgba(16,185,129,0.4)] transition cursor-pointer"
          >
            <Download className="w-4 h-4 text-slate-950" />
            <span>EXPORT CSV</span>
          </button>

          <button
            onClick={handleStartClearDb}
            className="px-3.5 py-2 rounded-xl bg-rose-950/80 hover:bg-rose-900 border border-rose-700/80 hover:border-rose-500 text-rose-300 hover:text-white text-xs font-bold font-tech uppercase tracking-wider flex items-center gap-1.5 shadow-[0_0_15px_rgba(244,63,94,0.3)] transition cursor-pointer active:scale-95"
            title="Clear Competition Database (Supervisor Authorization Required)"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-400" />
            <span>CLEAR DB</span>
          </button>
        </div>
      </div>

      {/* Success Notification Banner */}
      {clearDbSuccess && (
        <div className="relative z-10 p-3.5 rounded-xl bg-emerald-950/90 border border-emerald-500/80 text-emerald-200 text-xs flex items-center justify-between shadow-[0_0_20px_rgba(16,185,129,0.3)] animate-in fade-in">
          <div className="flex items-center gap-2.5">
            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="font-mono">{clearDbSuccess}</span>
          </div>
          <button
            onClick={() => setClearDbSuccess('')}
            className="p-1 text-emerald-400 hover:text-white transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Stats Cards */}
      <div className="relative z-10 grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="p-4 rounded-xl bg-[#070c18]/90 border border-cyan-900/60 flex items-center justify-between">
          <div>
            <span className="text-[10px] text-slate-400 uppercase tracking-widest block">TOTAL REGISTERED</span>
            <span className="text-2xl font-bold font-tech text-white block mt-0.5">{totalRegistered}</span>
          </div>
          <Users className="w-7 h-7 text-cyan-400 opacity-80" />
        </div>

        <div className="p-4 rounded-xl bg-[#070c18]/90 border border-emerald-900/60 flex items-center justify-between">
          <div>
            <span className="text-[10px] text-slate-400 uppercase tracking-widest block">CONCLUDED UNITS</span>
            <span className="text-2xl font-bold font-tech text-emerald-300 block mt-0.5">{finishedTeams}</span>
          </div>
          <ShieldCheck className="w-7 h-7 text-emerald-400 opacity-80" />
        </div>

        <div className="p-4 rounded-xl bg-[#070c18]/90 border border-amber-900/60 flex items-center justify-between">
          <div>
            <span className="text-[10px] text-slate-400 uppercase tracking-widest block">ACTIVE IN FLIGHT</span>
            <span className="text-2xl font-bold font-tech text-amber-300 block mt-0.5">{activeTeams}</span>
          </div>
          <Activity className="w-7 h-7 text-amber-400 opacity-80" />
        </div>

        <div className="p-4 rounded-xl bg-[#070c18]/90 border border-pink-900/60 flex items-center justify-between">
          <div>
            <span className="text-[10px] text-slate-400 uppercase tracking-widest block">TOP SCORE</span>
            <span className="text-2xl font-bold font-tech text-pink-300 block mt-0.5">{topScore.toFixed(1)}</span>
          </div>
          <Award className="w-7 h-7 text-pink-400 opacity-80" />
        </div>
      </div>

      {/* Main Table */}
      <div className="relative z-10 bg-[#070c18]/95 border border-cyan-800/60 rounded-2xl shadow-2xl overflow-hidden backdrop-blur-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-cyan-900/70 bg-black/60 text-slate-400 font-mono text-[11px] uppercase tracking-wider">
                <th className="py-3 px-4">RANK</th>
                <th className="py-3 px-4">CALLSIGN</th>
                <th className="py-3 px-4">OPERATORS & PRN</th>
                <th className="py-3 px-4 text-center">R1 TIME</th>
                <th className="py-3 px-4 text-center">R1 SCORE</th>
                <th className="py-3 px-4 text-center">R2 SCORE</th>
                <th className="py-3 px-4 text-center">R3 SCORE</th>
                <th className="py-3 px-4 text-center font-bold text-cyan-300">TOTAL</th>
                <th className="py-3 px-4 text-center">STATUS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cyan-950/60">
              {filteredTeams.length === 0 ? (
                <tr>
                  <td colSpan="9" className="text-center py-12 text-slate-500">
                    No matching teams found in master database.
                  </td>
                </tr>
              ) : (
                filteredTeams.map((t) => {
                  const isTop3 = t.rank <= 3;
                  const rankBadge =
                    t.rank === 1 ? 'bg-amber-500/20 text-amber-300 border-amber-500/60' :
                    t.rank === 2 ? 'bg-slate-300/20 text-slate-200 border-slate-400/60' :
                    t.rank === 3 ? 'bg-amber-700/20 text-amber-400 border-amber-700/60' :
                    'bg-slate-900 text-slate-400 border-slate-800';

                  const isFinished = t.status === 'FINISHED' || t.current_state === 'COMPLETED';

                  return (
                    <tr
                      key={t.team_id || t.rank}
                      className={`hover:bg-cyan-950/30 transition ${isTop3 ? 'bg-cyan-950/15' : ''}`}
                    >
                      <td className="py-3 px-4">
                        <span className={`px-2.5 py-1 rounded-lg border font-mono font-bold text-xs inline-block ${rankBadge}`}>
                          #{t.rank}
                        </span>
                      </td>

                      <td className="py-3 px-4 font-bold font-tech text-sm text-white">
                        {t.team_name}
                      </td>

                      <td className="py-3 px-4 text-slate-300 space-y-0.5">
                        <div className="text-[11px]">
                          <strong>{t.member_1_name || t.member1_name}</strong>{' '}
                          <span className="text-cyan-400/80">[{t.member_1_prn || t.member1_prn || 'PRN'}]</span>
                        </div>
                        <div className="text-[11px]">
                          <strong>{t.member_2_name || t.member2_name}</strong>{' '}
                          <span className="text-cyan-400/80">[{t.member_2_prn || t.member2_prn || 'PRN'}]</span>
                        </div>
                      </td>

                      <td className="py-3 px-4 text-center text-slate-400 font-mono">
                        {t.r1_time_formatted || '--:--'}
                      </td>

                      <td className="py-3 px-4 text-center font-bold text-slate-200">
                        {(t.round1_score ?? t.r1_score ?? 0).toFixed(1)}
                      </td>

                      <td className="py-3 px-4 text-center font-bold text-slate-200">
                        {(t.round2_score ?? t.r2_score ?? 0).toFixed(1)}
                      </td>

                      <td className="py-3 px-4 text-center font-bold text-slate-200">
                        {(t.round3_score ?? t.r3_score ?? 0).toFixed(1)}
                      </td>

                      <td className="py-3 px-4 text-center font-extrabold text-sm text-cyan-300 font-tech">
                        {(t.total_score ?? 0).toFixed(1)}
                      </td>

                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                            isFinished
                              ? 'bg-emerald-950/80 text-emerald-300 border-emerald-600/70'
                              : 'bg-cyan-950/80 text-cyan-300 border-cyan-700/70 animate-pulse'
                          }`}
                        >
                          {t.status}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <div className="p-3 bg-black/60 border-t border-cyan-950 text-slate-500 text-[10px] flex items-center justify-between">
          <span>Auto-sync enabled (every 5 seconds)</span>
          <span>Last sync: {lastRefreshed || 'Just now'}</span>
        </div>
      </div>

      {/* =========================================================================
          MODAL 1 OF 2: FIRST CLEAR DATABASE WARNING
          ========================================================================= */}
      {clearDbStep === 1 && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in">
          <div className="bg-[#0b0f19] border-2 border-amber-500/80 rounded-2xl max-w-lg w-full p-6 shadow-[0_0_50px_rgba(245,158,11,0.3)] space-y-4">
            <div className="flex items-start gap-3">
              <div className="p-2.5 rounded-xl bg-amber-950/80 border border-amber-600/80 text-amber-400">
                <AlertTriangle className="w-6 h-6 animate-pulse" />
              </div>
              <div className="flex-1">
                <span className="text-[10px] uppercase tracking-[0.25em] text-amber-400 font-bold block">
                  WARNING 1 OF 2 // PURGE CONFIRMATION
                </span>
                <h3 className="text-xl font-bold font-tech text-white mt-0.5">
                  Clear Competition Database?
                </h3>
              </div>
              <button
                onClick={handleAbortClearDb}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 rounded-xl bg-black/60 border border-amber-900/60 text-xs text-slate-300 leading-relaxed space-y-2.5">
              <p>
                You are about to initiate a <strong>complete system wipe</strong>. This operation will permanently delete:
              </p>
              <ul className="list-disc list-inside space-y-1 text-slate-400 pl-1">
                <li>All registered team profiles, credentials, and PRNs</li>
                <li>Round 1 submissions, fragment placements, and clocks</li>
                <li>Round 2 forensic transcripts and clues</li>
                <li>Round 3 accusation cases, decisions, and scores</li>
                <li>Game telemetry and audit trail logs</li>
              </ul>
              <p className="text-amber-300 font-bold pt-1 border-t border-amber-950">
                Do you want to proceed to security authorization?
              </p>
            </div>

            <div className="flex items-center justify-end gap-3 pt-1">
              <button
                onClick={handleAbortClearDb}
                className="px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 hover:border-slate-500 text-slate-300 hover:text-white text-xs font-bold transition cursor-pointer"
              >
                ABORT / CANCEL
              </button>
              <button
                onClick={handleProceedToStep2}
                className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold font-tech uppercase tracking-wider flex items-center gap-1.5 shadow-[0_0_20px_rgba(245,158,11,0.4)] transition cursor-pointer"
              >
                <span>CONTINUE TO FINAL STEP</span>
                <ArrowLeft className="w-3.5 h-3.5 rotate-180" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          MODAL 2 OF 2: CRITICAL WARNING & PASSWORD 'admin' VERIFICATION
          ========================================================================= */}
      {clearDbStep === 2 && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md animate-in fade-in">
          <div className="bg-[#0b0f19] border-2 border-rose-600 rounded-2xl max-w-lg w-full p-6 shadow-[0_0_60px_rgba(225,29,72,0.4)] space-y-4">
            <div className="flex items-start gap-3">
              <div className="p-2.5 rounded-xl bg-rose-950/80 border border-rose-600 text-rose-400 animate-pulse">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <span className="text-[10px] uppercase tracking-[0.25em] text-rose-400 font-bold block">
                  WARNING 2 OF 2 // CRITICAL CLEARANCE
                </span>
                <h3 className="text-xl font-bold font-tech text-white mt-0.5">
                  Final Destruction Authorization
                </h3>
              </div>
              <button
                onClick={handleAbortClearDb}
                disabled={clearDbLoading}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-900/80 text-xs text-rose-200 leading-relaxed space-y-2">
              <p className="font-bold text-rose-300">
                🚨 IRREVERSIBLE OPERATION: Once confirmed, all teams and competition data will be permanently wiped from the mainframe database.
              </p>
              <p className="text-slate-300">
                To authorize the wipe, please enter the administrator password (<span className="font-mono text-cyan-300 font-bold">admin</span>):
              </p>
            </div>

            <form onSubmit={handleConfirmClearDb} className="space-y-3.5">
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  autoFocus
                  placeholder='Enter password "admin"...'
                  value={adminPassword}
                  onChange={(e) => {
                    setAdminPassword(e.target.value);
                    setClearDbError('');
                  }}
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-black/80 border border-rose-800 focus:border-rose-400 text-sm font-mono text-white placeholder:text-slate-500 outline-none shadow-inner"
                />
              </div>

              {clearDbError && (
                <div className="p-2.5 rounded-lg bg-rose-950/80 border border-rose-600 text-rose-300 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
                  <span>{clearDbError}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-1">
                <button
                  type="button"
                  onClick={handleAbortClearDb}
                  disabled={clearDbLoading}
                  className="px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 hover:border-slate-500 text-slate-300 hover:text-white text-xs font-bold transition cursor-pointer"
                >
                  CANCEL / ABORT
                </button>
                <button
                  type="submit"
                  disabled={clearDbLoading}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white text-xs font-bold font-tech uppercase tracking-wider flex items-center gap-2 shadow-[0_0_25px_rgba(225,29,72,0.5)] transition cursor-pointer disabled:opacity-50"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>{clearDbLoading ? 'PURGING MAINFRAME...' : 'CONFIRM & WIPE DATABASE'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

