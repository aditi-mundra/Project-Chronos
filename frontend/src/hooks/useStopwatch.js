import { useState, useRef, useCallback, useEffect } from 'react';

// Count-up stopwatch driven by wall-clock timestamps, not by counting ticks, so the value
// stays correct when rendering is delayed or the tab is throttled while in the background.
// start() is idempotent; stop() freezes the final duration and clears the interval.

const TICK_MS = 250;

export function formatElapsed(ms) {
  const total = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return [h, m, s].map((n) => String(n).padStart(2, '0')).join(':');
}

export function useStopwatch() {
  const startedAtRef = useRef(null);
  const [status, setStatus] = useState('idle'); // 'idle' | 'running' | 'stopped'
  const [elapsedMs, setElapsedMs] = useState(0);

  const start = useCallback(() => {
    if (startedAtRef.current !== null) return; // duplicate start guard
    startedAtRef.current = Date.now();
    setElapsedMs(0);
    setStatus('running');
  }, []);

  // Reload: keep running from the value the server holds (it does not restart from zero).
  const resume = useCallback((elapsed) => {
    startedAtRef.current = Date.now() - Math.max(0, elapsed || 0);
    setElapsedMs(Math.max(0, elapsed || 0));
    setStatus('running');
  }, []);

  // Reload after END STOPWATCH: show the frozen value, never count again.
  const freeze = useCallback((ms) => {
    startedAtRef.current = startedAtRef.current ?? 0;
    setElapsedMs(Math.max(0, ms || 0));
    setStatus('stopped');
  }, []);

  const stop = useCallback(() => {
    if (startedAtRef.current === null || status !== 'running') return elapsedMs;
    const finalMs = Date.now() - startedAtRef.current;
    setElapsedMs(finalMs);
    setStatus('stopped');
    return finalMs;
  }, [status, elapsedMs]);

  useEffect(() => {
    if (status !== 'running') return undefined;
    const update = () => setElapsedMs(Date.now() - startedAtRef.current);
    const id = setInterval(update, TICK_MS);
    // Catch up immediately when a hidden tab becomes visible again.
    document.addEventListener('visibilitychange', update);
    return () => {
      clearInterval(id);
      document.removeEventListener('visibilitychange', update);
    };
  }, [status]);

  return { status, elapsedMs, display: formatElapsed(elapsedMs), start, stop, resume, freeze };
}
