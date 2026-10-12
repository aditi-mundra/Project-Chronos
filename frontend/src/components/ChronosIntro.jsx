import React, { useEffect, useRef, useCallback } from 'react';
import '../styles/glossy-skip.css';

/**
 * ChronosIntro
 * ------------
 * Renders the project-chronos.html GSAP intro inside a full-screen iframe.
 * Listens for the 'CHRONOS_INTRO_DONE' postMessage from the iframe,
 * then fires a smooth fade-out before calling onComplete.
 *
 * Props:
 *   onComplete — called when the intro is fully done and faded out
 */
export default function ChronosIntro({ onComplete }) {
  const iframeRef   = useRef(null);
  const overlayRef  = useRef(null);
  const doneRef     = useRef(false);   // guard against double-fire
  const skipBtnRef  = useRef(null);

  const finish = useCallback(() => {
    if (doneRef.current) return;
    doneRef.current = true;

    // the SKIP button fades away together with the intro
    skipBtnRef.current?.classList.add('is-leaving');

    // The HTML intro already fades to black — we just wait a tiny beat then
    // fade our overlay in (extra safety black layer) and call onComplete.
    const overlay = overlayRef.current;
    if (overlay) {
      overlay.style.transition = 'opacity 0.4s ease';
      overlay.style.opacity    = '1';
    }
    setTimeout(() => onComplete?.(), 420);
  }, [onComplete]);

  useEffect(() => {
    const handler = (e) => {
      if (e.data === 'CHRONOS_INTRO_DONE') finish();
    };
    const onKey = (e) => {
      if (e.key === 'Escape') finish();
    };
    window.addEventListener('message', handler);
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('message', handler);
      window.removeEventListener('keydown', onKey);
    };
  }, [finish]);

  return (
    <div
      className="cursor-none select-none"
      style={{
        position: 'fixed',
        inset:    0,
        zIndex:   50,
        background: '#000',
        cursor:   'none',
      }}
    >
      {/* The actual GSAP intro */}
      <iframe
        ref={iframeRef}
        src="/intro/project-chronos.html"
        title="Project Chronos Intro"
        className="cursor-none"
        style={{
          position: 'absolute',
          inset:    0,
          width:    '100%',
          height:   '100%',
          border:   'none',
          display:  'block',
          cursor:   'none',
        }}
        allowFullScreen
      />

      {/* SKIP: jumps straight to the login screen */}
      <button ref={skipBtnRef} type="button" className="chronos-skip" onClick={finish} title="Skip the intro (Esc)">
        <span className="chronos-skip__in">
          <span>Skip</span>
          <span className="chronos-skip__chev" aria-hidden="true"><i /><i /></span>
        </span>
      </button>

      {/* Black overlay — starts transparent, snaps to opaque on finish for a
          seamless cut into the Register screen */}
      <div
        ref={overlayRef}
        style={{
          position:   'absolute',
          inset:       0,
          background: '#000',
          opacity:     0,
          pointerEvents: 'none',
        }}
      />
    </div>
  );
}
