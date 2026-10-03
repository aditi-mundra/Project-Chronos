/**
 * PROJECT CHRONOS — API client
 *
 * Base URL:
 *  - Production: leave VITE_API_BASE unset -> same origin (FastAPI serves the built frontend).
 *  - Development: frontend/.env sets VITE_API_BASE (e.g. http://localhost:8000).
 */
const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '');

async function apiRequest(endpoint, options = {}) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const message = data?.detail || data?.message || `HTTP ${res.status}: ${res.statusText}`;
    const error = new Error(typeof message === 'string' ? message : 'Request failed.');
    error.status = res.status;
    throw error;
  }
  return data;
}

// Round 1 endpoints report business errors as 200 + { error: "..." } (see
// docs/round1_api_contract.md), so those are turned into thrown errors here.
function unwrapRound1(data) {
  if (data?.error) {
    const error = new Error(data.error);
    error.status = 200;
    throw error;
  }
  return data;
}

// Round 1 image paths come from the backend (e.g. "/static/round1/x.png", may contain spaces).
export function assetUrl(path) {
  return `${API_BASE}${encodeURI(path)}`;
}

export const api = {
  // --- Auth: POST /api/auth/login (registers a new team, or logs in a returning team) ---
  login(payload) {
    return apiRequest('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // --- Auth: GET /api/auth/session (validates a stored session after a page reload) ---
  async getSession(teamId) {
    try {
      return await apiRequest(`/api/auth/session?team_id=${encodeURIComponent(teamId)}`);
    } catch (err) {
      if (err.status === 404) return { notFound: true };
      return null; // network / server hiccup: caller keeps the session
    }
  },

  // --- Round 1: GET /api/round1/status (state, server-side remaining time, result once done) ---
  async getRound1Status(teamId) {
    const data = await apiRequest(`/api/round1/status?team_id=${encodeURIComponent(teamId)}`);
    return unwrapRound1(data);
  },

  // --- Round 1: GET /api/round1/items (first call assigns the team's items and starts its clock) ---
  async getRound1Items(teamId) {
    const data = await apiRequest(`/api/round1/items?team_id=${encodeURIComponent(teamId)}`);
    return unwrapRound1(data);
  },

  // --- Round 1: POST /api/round1/submit (one classification per item) ---
  async submitRound1Answer(teamId, itemId, answer) {
    const query = new URLSearchParams({ team_id: teamId, item_id: itemId, answer });
    const data = await apiRequest(`/api/round1/submit?${query}`, { method: 'POST' });
    return unwrapRound1(data);
  },

  // --- Round 1: POST /api/round1/finish (backend decides whether the round is really complete) ---
  async finishRound1(teamId) {
    const data = await apiRequest(`/api/round1/finish?team_id=${encodeURIComponent(teamId)}`, {
      method: 'POST',
    });
    return unwrapRound1(data);
  },
};

export default api;
