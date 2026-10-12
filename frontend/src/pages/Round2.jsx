import { useEffect } from 'react';
import { useAuth } from '../context/AuthContext.jsx';

/**
 * Round 2 (CHRONOS terminal investigation).
 *
 * The page itself is a self-contained screen in public/round2/index.html. It talks to
 * /api/round2/* with the team id given here; the backend owns the case, the timer, the
 * AI questions and the scoring, and the page shows the Round 3 lobby when the round ends.
 * `boot` is true only when the team arrives from the Round 2 lobby (boot screen + intro
 * sound). On a page reload (`boot` false) the page opens straight to where the team was.
 */
export default function Round2({ team: propTeam, onLogout, boot = true, onAdvanceToRound3 }) {
  const { team: authTeam, logoutTeam } = useAuth();
  const team = propTeam || authTeam;

  // The Round 3 lobby inside the page has a LOGOUT button and ADVANCE TO ROUND 3 action.
  useEffect(() => {
    const onMessage = (event) => {
      if (event.origin === window.location.origin) {
        if (event.data?.type === 'chronos-logout') {
          if (onLogout) onLogout();
          else if (logoutTeam) logoutTeam();
        } else if (event.data?.type === 'chronos-round3') {
          if (onAdvanceToRound3) onAdvanceToRound3();
        }
      }
    };
    window.addEventListener('message', onMessage);
    return () => window.removeEventListener('message', onMessage);
  }, [onLogout, logoutTeam, onAdvanceToRound3]);

  return (
    <iframe
      title="Round 2"
      src={`/round2/index.html?team_id=${encodeURIComponent(team?.team_id ?? team?.id ?? '')}${boot ? '' : '&boot=0'}`}
      allow="autoplay"
      style={{ position: 'fixed', inset: 0, width: '100%', height: '100%', border: 0, background: '#000', zIndex: 40 }}
    />
  );
}
