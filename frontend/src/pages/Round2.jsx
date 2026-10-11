import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext.jsx';

/**
 * Round 2 (CHRONOS terminal investigation, investigation-only: no culprit submission).
 *
 * The page itself is a self-contained screen in public/round2/index.html. It talks to
 * /api/round2/* with the team id given here; the backend owns the case, the timer, the
 * AI questions and the scoring, and the page shows the Round 3 lobby when the round ends.
 * `boot` is true only when the team arrives from the Round 2 lobby (boot screen + intro
 * sound). On a page reload (`boot` false) the page opens straight to where the team was.
 */
export default function Round2({ onLogout, boot = true, onRound3Started }) {
  const { team } = useAuth();
  // The page inside the iframe is a plain static file. A changing query value stops the
  // browser from showing an older cached copy of it after an update.
  const [version] = useState(() => Date.now());

  // The Round 3 lobby inside the page asks this app to log out (LOGOUT button) or to open
  // Round 3 (START ROUND 3 button, after the server accepted the start).
  useEffect(() => {
    const onMessage = (event) => {
      if (event.origin !== window.location.origin) return;
      if (event.data?.type === 'chronos-logout') onLogout?.();
      if (event.data?.type === 'chronos-round3-started') onRound3Started?.();
    };
    window.addEventListener('message', onMessage);
    return () => window.removeEventListener('message', onMessage);
  }, [onLogout, onRound3Started]);

  return (
    <iframe
      title="Round 2"
      src={`/round2/index.html?team_id=${encodeURIComponent(team?.team_id ?? '')}${boot ? '' : '&boot=0'}&v=${version}`}
      allow="autoplay"
      style={{ position: 'fixed', inset: 0, width: '100%', height: '100%', border: 0, background: '#000', zIndex: 40 }}
    />
  );
}
