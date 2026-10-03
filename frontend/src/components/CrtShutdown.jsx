import React, { useEffect, useRef } from 'react';
import { soundFx } from '../utils/audio.js';

/**
 * CrtShutdown
 * -----------
 * Authentic CRT TV power-off transition effect.
 *
 * Visual Stages:
 * 1. Immediate power cutoff surge & tube scanlines flare.
 * 2. Full-screen compresses vertically from top and bottom into center.
 * 3. UI collapses into a razor-thin glowing phosphor line (electric cyan / phosphor blue).
 * 4. Line holds briefly with bright phosphor bloom (#00f0ff / #06b6d4 / white hot core).
 * 5. Line shrinks from left and right inward into a pinpoint glowing dot.
 * 6. Dot micro-flickers with phosphor decay and fades into deep blackness.
 * 7. On complete, transitions seamlessly to the cinematic intro scene.
 */
export default function CrtShutdown({ onComplete }) {
  const audioRef = useRef(null);
  const completedRef = useRef(false);

  useEffect(() => {
    // 1. Play CRT Sound immediately upon trigger
    audioRef.current = soundFx.playCrtShutdown();

    // 2. Schedule transition handoff aligned with audio (1.26s)
    const timer = setTimeout(() => {
      if (!completedRef.current) {
        completedRef.current = true;
        onComplete?.();
      }
    }, 1260);

    return () => {
      clearTimeout(timer);
      if (audioRef.current) {
        try {
          audioRef.current.pause();
        } catch (_) {}
      }
    };
  }, [onComplete]);

  return (
    <div
      className="fixed inset-0 z-[100] pointer-events-none select-none overflow-hidden cursor-none"
      style={{ cursor: 'none' }}
      aria-hidden="true"
    >
      {/* Dark CRT Tube Curvature & Edge Vignette */}
      <div className="crt-tube-vignette" />

      {/* Dynamic Scanlines Raster */}
      <div className="crt-shutdown-scanlines" />

      {/* Phosphor Flash & Ambient Haze */}
      <div className="crt-ambient-flash" />

      {/* Horizontal Collapsing Phosphor Line */}
      <div className="crt-beam-line" />

      {/* Center Pinpoint Phosphor Dot with Micro-Flicker Decay */}
      <div className="crt-center-dot" />
    </div>
  );
}
