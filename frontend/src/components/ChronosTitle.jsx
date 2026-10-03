import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'motion/react';

const WORD    = 'CHRONOS';
const LETTERS = WORD.split('');
const CENTER  = (LETTERS.length - 1) / 2;

// Pool of glitch replacement chars — numbers, symbols, Greek, binary fragments
const GLITCH_POOL = '0123456789Δ∑ΨΩΞ!#%@8̷3̴1̸0̵7̷2̶9̸Φ∂Γ01';

function randChar() {
  return GLITCH_POOL[Math.floor(Math.random() * GLITCH_POOL.length)];
}

export default function ChronosTitle() {
  const stageRef   = useRef(null);
  const glitchRaf  = useRef(null);           // RAF handle for glitch loop
  const [phase, setPhase]           = useState('intro');
  const [chromaSplit, setChromaSplit] = useState(false);
  const [glitching, setGlitching]   = useState(false);
  // charMap: { [letterIndex]: replacementChar | null }
  const [charMap, setCharMap]       = useState({});
  // jitterMap: { [letterIndex]: { x, y, skew } } for per-cell micro-jitter
  const [jitterMap, setJitterMap]   = useState({});

  const reducedMotion = useMemo(
    () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    [],
  );

  // ── Entrance: letters land → chroma flash → idle ──────────────────────────
  useEffect(() => {
    if (reducedMotion) { setPhase('idle'); return undefined; }

    setPhase('intro');
    setChromaSplit(false);
    setCharMap({});
    setJitterMap({});

    const t1 = setTimeout(() => setChromaSplit(true),  720);
    const t2 = setTimeout(() => setChromaSplit(false), 950);
    const t3 = setTimeout(() => setPhase('idle'),     1010);

    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, [reducedMotion]);

  // ── Core glitch engine — runs via RAF for buttery frame-level chaos ────────
  const fireGlitch = useCallback(() => {
    if (reducedMotion) return;

    // Cancel any in-flight glitch RAF
    if (glitchRaf.current) cancelAnimationFrame(glitchRaf.current);

    setGlitching(true);

    const totalMs    = 280 + Math.random() * 220;   // 280–500 ms burst
    const cycleMs    = 38 + Math.random() * 22;      // swap chars every 38–60 ms
    const startTime  = performance.now();
    let   lastCycle  = 0;

    const tick = (now) => {
      const elapsed = now - startTime;

      // On each cycle-tick: scramble 1–4 random letter positions
      if (now - lastCycle >= cycleMs) {
        lastCycle = now;

        const count   = 1 + Math.floor(Math.random() * 4);
        const newMap  = {};
        const jitter  = {};

        for (let k = 0; k < count; k++) {
          const idx = Math.floor(Math.random() * LETTERS.length);
          newMap[idx]   = randChar();
          // Per-cell micro-jitter: tiny translate + skew for each scrambled cell
          jitter[idx] = {
            x:    (Math.random() - 0.5) * 7,
            y:    (Math.random() - 0.5) * 4,
            skew: (Math.random() - 0.5) * 10,
          };
        }

        setCharMap(newMap);
        setJitterMap(jitter);
      }

      if (elapsed < totalMs) {
        glitchRaf.current = requestAnimationFrame(tick);
      } else {
        // Clean up — restore all letters
        setCharMap({});
        setJitterMap({});
        setGlitching(false);
        glitchRaf.current = null;
      }
    };

    glitchRaf.current = requestAnimationFrame(tick);
  }, [reducedMotion]);

  // ── Idle glitch scheduler ──────────────────────────────────────────────────
  useEffect(() => {
    if (phase !== 'idle' || reducedMotion) return undefined;
    let timerId;
    let cancelled = false;

    const schedule = () => {
      timerId = setTimeout(() => {
        if (cancelled) return;
        fireGlitch();
        schedule();
      }, 3200 + Math.random() * 2600);   // fire every 3.2–5.8 s
    };
    schedule();

    return () => {
      cancelled = true;
      clearTimeout(timerId);
      if (glitchRaf.current) cancelAnimationFrame(glitchRaf.current);
    };
  }, [phase, reducedMotion, fireGlitch]);

  // Ghost layers activate during entrance chroma flash OR active glitch
  const ghostsActive = chromaSplit || glitching;

  return (
    <div ref={stageRef} className={`chrono-stage ${phase === 'idle' ? 'is-locked' : ''}`}>
      <div className="chrono-seam" />
      <div className={`chrono-bloom ${phase === 'intro' ? 'is-firing' : ''}`} />

      <div className="chrono-rig">
        {/* Blurred aura glow behind the word */}
        <span className="chrono-aura font-title" aria-hidden="true">{WORD}</span>

        <h1
          className={`chrono-word font-title ${ghostsActive ? 'is-glitching' : ''}`}
          aria-label="CHRONOS"
        >
          {LETTERS.map((letter, i) => {
            const dist       = Math.abs(i - CENTER);
            const startY     = reducedMotion ? 0 : 56 + dist * 8;
            const startScale = reducedMotion ? 1 : 0.78 + dist * 0.03;
            const delay      = reducedMotion ? 0 : 0.05 + dist * 0.065;

            // What character is currently shown for this cell?
            const displayChar = charMap[i] ?? letter;
            const isScrambled = !!charMap[i];
            const jitter      = jitterMap[i] ?? null;

            return (
              <motion.span
                key={`${letter}-${i}`}
                className={`chrono-cell ${isScrambled ? 'is-scrambled' : ''}`}
                initial={reducedMotion ? false : {
                  opacity: 0, y: startY, scale: startScale, filter: 'blur(6px)',
                }}
                animate={{
                  opacity: 1,
                  y:       jitter ? jitter.y : 0,
                  x:       jitter ? jitter.x : 0,
                  scale:   isScrambled ? 0.92 + Math.random() * 0.16 : 1,
                  skewX:   jitter ? jitter.skew : 0,
                  filter: 'blur(0px)',
                }}
                transition={isScrambled
                  ? { duration: 0.04, ease: 'linear' }   // near-instant snap for scramble
                  : {
                      delay,
                      duration: 0.7,
                      ease: [0.12, 0.9, 0.25, 1.08],
                      filter: { duration: 0.4, delay },
                    }
                }
              >
                <span className="chrono-ghost chrono-ghost--c" aria-hidden="true">
                  {displayChar}
                </span>
                <span className="chrono-ghost chrono-ghost--m" aria-hidden="true">
                  {displayChar}
                </span>
                <span className={`chrono-solid ${isScrambled ? 'is-corrupt' : ''}`}>
                  {displayChar}
                </span>
              </motion.span>
            );
          })}
        </h1>

        <div className="chrono-scan" />
        <div className="chrono-underline" />
      </div>
    </div>
  );
}
