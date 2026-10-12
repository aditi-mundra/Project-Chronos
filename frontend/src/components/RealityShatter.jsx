import { useEffect, useRef } from 'react';
import { soundFx } from '../utils/audio.js';
import { runRealityShatter } from './realityShatterEngine.js';
import '../styles/reality-shatter.css';

/**
 * REALITY SHATTER 2.0: the cinematic between the Round 1 lobby and the Physical Transition Round.
 *
 * This component only owns the overlay DOM. All animation logic lives in
 * `realityShatterEngine.js` (one clock, ordered phases, guarded callbacks, full cleanup).
 *
 * Props
 *   appRootRef  ref to the element that holds the visible interface (cloned for the shards)
 *   onSwap      called exactly once while the screen is black: mount the next round underneath
 *   onDone      called exactly once when the overlay is gone (never after an unmount)
 */
export default function RealityShatter({ appRootRef, onSwap, onDone }) {
  const rootRef = useRef(null);
  const bgRef = useRef(null);
  const bandsRef = useRef(null);
  const fragsRef = useRef(null);
  const canvasRef = useRef(null);
  const scanRef = useRef(null);
  const msgRef = useRef(null);
  const flashRef = useRef(null);
  const swapRef = useRef(onSwap);
  const doneRef = useRef(onDone);
  useEffect(() => {
    swapRef.current = onSwap;
    doneRef.current = onDone;
  });

  useEffect(() => {
    const app = appRootRef.current;
    const els = {
      root: rootRef.current,
      bg: bgRef.current,
      bands: bandsRef.current,
      frags: fragsRef.current,
      canvas: canvasRef.current,
      scan: scanRef.current,
      msg: msgRef.current,
      flash: flashRef.current,
    };
    let run = null;
    try {
      if (!app) throw new Error('missing app root');
      run = runRealityShatter({
        els,
        app,
        soundFx,
        onSwap: () => swapRef.current?.(),
        onDone: () => doneRef.current?.(),
      });
    } catch (err) {
      // never trap the player: skip the effect and go straight to the next round
      console.error('RealityShatter could not start:', err);
      swapRef.current?.();
      doneRef.current?.();
    }
    return () => run?.cancel();
  }, [appRootRef]);

  return (
    <div ref={rootRef} className="rs-root" role="presentation" aria-hidden="true">
      <div ref={bgRef} className="rs-bg" />
      <div ref={bandsRef} className="rs-layer" />
      <div ref={fragsRef} className="rs-layer rs-frags" />
      <canvas ref={canvasRef} className="rs-canvas" />
      <div ref={scanRef} className="rs-scan" />
      <div ref={msgRef} className="rs-msg font-title" />
      <div ref={flashRef} className="rs-flash" />
    </div>
  );
}
