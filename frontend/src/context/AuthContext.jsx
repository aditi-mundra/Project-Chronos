import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import api from '../services/api.js';
import { soundFx } from '../utils/audio.js';

const AuthContext = createContext(null);

export const SESSION_KEY = 'chronos_team_session';

function readStoredSession() {
  try {
    const stored = localStorage.getItem(SESSION_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

export const AuthProvider = ({ children }) => {
  const [team, setTeam] = useState(readStoredSession);
  const [soundEnabled, setSoundEnabled] = useState(true);

  // Persist the team session so a page reload keeps the team logged in until LOGOUT.
  useEffect(() => {
    if (team) {
      localStorage.setItem(SESSION_KEY, JSON.stringify(team));
    } else {
      localStorage.removeItem(SESSION_KEY);
    }
  }, [team]);

  const toggleSound = () => {
    setSoundEnabled((prev) => {
      const next = !prev;
      soundFx.setSoundEnabled(next);
      return next;
    });
  };

  // Stable ref so the session check below never depends on a changing `team` object.
  const teamRef = useRef(team);
  useEffect(() => {
    teamRef.current = team;
  }, [team]);

  // Verify the stored session against the server. Only an explicit 404 (team no longer
  // exists, e.g. database reset) ends the session — network errors never log the team out.
  const verifySession = useCallback(async () => {
    const current = teamRef.current;
    const teamId = current?.team_id;
    if (!teamId || current?.team_name === 'TEST-DEV-UNIT') return;

    const result = await api.getSession(teamId);
    if (result?.notFound) {
      setTeam(null);
      return;
    }
    if (result?.current_state && result.current_state !== current.current_state) {
      setTeam((prev) => (prev ? { ...prev, current_state: result.current_state } : prev));
    }
  }, []);

  useEffect(() => {
    if (team?.team_id) verifySession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [team?.team_id]);

  const loginTeamSession = (teamData) => {
    setTeam({
      team_id: teamData.team_id,
      team_name: teamData.team_name,
      member_1_name: teamData.member_1_name || '',
      member_2_name: teamData.member_2_name || '',
      member_1_prn: teamData.member_1_prn || '',
      member_2_prn: teamData.member_2_prn || '',
      current_state: teamData.current_state || 'READY',
    });
  };

  const logoutTeam = () => {
    setTeam(null);
  };

  // Keep the stored session in step with the server-side state (e.g. ROUND1_COMPLETED).
  const updateTeamState = useCallback((currentState) => {
    setTeam((prev) => (prev ? { ...prev, current_state: currentState } : prev));
  }, []);

  return (
    <AuthContext.Provider
      value={{
        team,
        soundEnabled,
        toggleSound,
        loginTeamSession,
        logoutTeam,
        updateTeamState,
        verifySession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
