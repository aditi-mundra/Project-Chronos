/**
 * Project Chronos — Unified API Service
 * Manages communication with the central FastAPI backend.
 */

const API_BASE = '/api';

/**
 * Helper to handle fetch responses and parse errors.
 */
async function handleResponse(res) {
  if (!res.ok) {
    let errorDetail = 'Network response was not ok';
    try {
      const errData = await res.json();
      errorDetail = errData.detail || errData.message || JSON.stringify(errData);
    } catch {
      errorDetail = res.statusText || `HTTP ${res.status}`;
    }
    throw new Error(errorDetail);
  }
  return await res.json();
}

export const api = {
  // =========================================================================
  // Auth & Team Session
  // =========================================================================
  async login(payload) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  // =========================================================================
  // Game State
  // =========================================================================
  async getGameState(teamId) {
    const res = await fetch(`${API_BASE}/game/state?team_id=${teamId}`);
    return handleResponse(res);
  },

  // =========================================================================
  // Round 3: Final Decision / Wisdom Round
  // =========================================================================
  async startRound3(teamId) {
    const res = await fetch(`${API_BASE}/round3/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team_id: teamId })
    });
    return handleResponse(res);
  },

  async getRound3Scenario(teamId) {
    const res = await fetch(`${API_BASE}/round3/scenario?team_id=${teamId}`);
    return handleResponse(res);
  },

  async submitRound3Decision(teamId, selectedCandidateId, selectedEvidenceIds) {
    const res = await fetch(`${API_BASE}/round3/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team_id: teamId,
        selected_candidate_id: selectedCandidateId,
        selected_evidence_ids: selectedEvidenceIds
      })
    });
    return handleResponse(res);
  },

  async getRound3Verdict(teamId) {
    const res = await fetch(`${API_BASE}/round3/verdict?team_id=${teamId}`);
    return handleResponse(res);
  },

  // =========================================================================
  // Admin Endpoints
  // =========================================================================
  async getAdminLeaderboard() {
    const res = await fetch(`${API_BASE}/admin/leaderboard`);
    return handleResponse(res);
  },

  async getAdminLogs(limit = 100) {
    const res = await fetch(`${API_BASE}/admin/logs?limit=${limit}`);
    return handleResponse(res);
  },

  getExportCsvUrl() {
    return `${API_BASE}/admin/export-csv`;
  }
};
