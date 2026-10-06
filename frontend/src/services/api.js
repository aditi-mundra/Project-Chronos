/**
 * PROJECT CHRONOS — Unified API Client
 * Manages communication with the central FastAPI backend.
 *
 * Base URL:
 *  - Production: leave VITE_API_BASE unset -> same origin (FastAPI serves the built frontend).
 *  - Development: frontend/.env sets VITE_API_BASE (e.g. http://localhost:8000).
 */

const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '');

async function apiRequest(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const message = data?.detail || data?.message || `HTTP ${res.status}: ${res.statusText}`;
    const error = new Error(typeof message === 'string' ? message : 'Request failed.');
    error.status = res.status;
    error.data = data;
    throw error;
  }
  return data;
}

// Round 1 endpoints report business errors as 200 + { error: "..." }
function unwrapRound1(data) {
  if (data?.error) {
    const error = new Error(data.error);
    error.status = 200;
    throw error;
  }
  return data;
}

// Asset URL helper for Round 1 static image paths
export function assetUrl(path) {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  return `${API_BASE}${encodeURI(path)}`;
}

export const api = {
  // =========================================================================
  // Auth & Team Session
  // =========================================================================
  async login(payload) {
    return apiRequest('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getSession(teamId) {
    try {
      return await apiRequest(`/api/auth/session?team_id=${encodeURIComponent(teamId)}`);
    } catch (err) {
      if (err.status === 404) return { notFound: true };
      return null;
    }
  },

  // =========================================================================
  // Round 1 Subsystem
  // =========================================================================
  async getRound1Status(teamId) {
    const data = await apiRequest(`/api/round1/status?team_id=${encodeURIComponent(teamId)}`);
    return unwrapRound1(data);
  },

  async getRound1Items(teamId) {
    const data = await apiRequest(`/api/round1/items?team_id=${encodeURIComponent(teamId)}`);
    return unwrapRound1(data);
  },

  async submitRound1Answer(teamId, itemId, answer) {
    const query = new URLSearchParams({ team_id: teamId, item_id: itemId, answer });
    const data = await apiRequest(`/api/round1/submit?${query}`, { method: 'POST' });
    return unwrapRound1(data);
  },

  async finishRound1(teamId) {
    const data = await apiRequest(`/api/round1/finish?team_id=${encodeURIComponent(teamId)}`, {
      method: 'POST',
    });
    return unwrapRound1(data);
  },

  // =========================================================================
  // Round 2 Subsystem
  // =========================================================================
  async getRound2Files(teamId) {
    const query = teamId ? `?team_id=${encodeURIComponent(teamId)}` : '';
    return apiRequest(`/api/round2/files${query}`);
  },

  async askRound2Ai(teamId, userPrompt) {
    return apiRequest('/api/round2/chat', {
      method: 'POST',
      body: JSON.stringify({ team_id: teamId, user_prompt: userPrompt }),
    });
  },

  // =========================================================================
  // Round 3 Subsystem (Final Accusation / Wisdom Round)
  // =========================================================================
  async startRound3(teamId) {
    return apiRequest('/api/round3/start', {
      method: 'POST',
      body: JSON.stringify({ team_id: teamId }),
    });
  },

  async getRound3Scenario(teamId) {
    return apiRequest(`/api/round3/scenario?team_id=${encodeURIComponent(teamId)}`);
  },

  async submitRound3Decision(teamId, selectedCandidateId, selectedEvidenceIds = []) {
    return apiRequest('/api/round3/submit', {
      method: 'POST',
      body: JSON.stringify({
        team_id: teamId,
        selected_candidate_id: selectedCandidateId,
        selected_evidence_ids: selectedEvidenceIds,
      }),
    });
  },

  async getRound3Verdict(teamId) {
    return apiRequest(`/api/round3/verdict?team_id=${encodeURIComponent(teamId)}`);
  },

  // =========================================================================
  // Game & Admin Telemetry
  // =========================================================================
  async getGameState(teamId) {
    return apiRequest(`/api/game/state?team_id=${encodeURIComponent(teamId)}`);
  },

  async getAdminLeaderboard() {
    return apiRequest('/api/admin/leaderboard');
  },

  async getAdminLogs(limit = 100) {
    return apiRequest(`/api/admin/logs?limit=${limit}`);
  },

  async clearDatabase(password) {
    return apiRequest('/api/admin/clear-db', {
      method: 'POST',
      body: JSON.stringify({ password }),
    });
  },

  getExportCsvUrl() {
    return `${API_BASE}/api/admin/export-csv`;
  },
};

export default api;
