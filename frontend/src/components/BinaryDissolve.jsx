import { useEffect, useLayoutEffect, useRef } from 'react';

/**
 * Full-screen "everything turns into binary" layer used by the Round 3 entry transition.
 *
 *   mode="cover":  cells flip from the live screen to 0 / 1 glyphs (top-down, with scatter)
 *                  until the whole screen is binary.
 *   mode="reveal": the same grid, played backwards: binary cells fall away and the screen
 *                  underneath appears.
 *
 * Timer driven (not rAF) so it also runs while the browser throttles animation frames.
 */
const CELL = 16;
const BG = 'rgba(1, 5, 10, 0.96)';
const DIM = 'rgba(34, 211, 238, 0.55)';
const HOT = '#e8fdff';
const ACCENT = 'rgba(244, 114, 182, 0.85)';

export default function BinaryDissolve({ mode = 'cover', duration = 1000, onComplete }) {
  const ref = useRef(null);
  const doneRef = useRef(onComplete);
  useEffect(() => {
    doneRef.current = onComplete;
  });

  useLayoutEffect(() => {
    const cv = ref.current;
    const ctx = cv.getContext('2d');
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = window.innerWidth;
    const h = window.innerHeight;
    cv.width = w * dpr;
    cv.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const cols = Math.ceil(w / CELL);
    const rows = Math.ceil(h / CELL);
    const thr = new Float32Array(cols * rows);
    const glyph = new Uint8Array(cols * rows);
    for (let i = 0; i < thr.length; i++) {
      const y = Math.floor(i / cols);
      thr[i] = Math.min(0.999, 0.7 * Math.random() + 0.3 * (y / rows));
      glyph[i] = Math.random() < 0.5 ? 1 : 0;
    }
    ctx.font = `${CELL - 3}px "Share Tech", ui-monospace, Consolas, monospace`;
    ctx.textBaseline = 'top';
    const cover = mode === 'cover';

    // p runs 0 -> 1.05 so that every cell (threshold < 1) is covered / uncovered at the end
    const draw = (p) => {
      ctx.clearRect(0, 0, w, h);
      for (let i = 0; i < thr.length; i++) {
        if (Math.random() < 0.18) glyph[i] ^= 1;
        const x = (i % cols) * CELL;
        const y = Math.floor(i / cols) * CELL;
        // d > 0: the cell shows binary; -0.12 < d <= 0: the cell flickers just ahead of the front
        const d = cover ? p - thr[i] : thr[i] - p;
        if (d > 0) {
          ctx.fillStyle = BG;
          ctx.fillRect(x, y, CELL, CELL);
          ctx.fillStyle = d < 0.08 ? HOT : Math.random() < 0.04 ? ACCENT : DIM;
          ctx.fillText(glyph[i] ? '1' : '0', x + 3, y + 1);
        } else if (d > -0.12 && Math.random() < 0.22) {
          ctx.fillStyle = DIM;
          ctx.fillText(glyph[i] ? '1' : '0', x + 3, y + 1);
        }
      }
    };

    const start = Date.now();
    // reveal starts fully covered (matches the last frame of the cover); first frame is
    // painted synchronously so there is no blank flash between the two
    draw(cover ? 0 : -0.001);
    const iv = setInterval(() => {
      const raw = Math.min(1, (Date.now() - start) / duration);
      const p = raw * 1.05;
      draw(cover ? p : p);
      if (raw >= 1) {
        clearInterval(iv);
        if (!cover) ctx.clearRect(0, 0, w, h);
        doneRef.current?.();
      }
    }, 40);
    return () => clearInterval(iv);
  }, [mode, duration]);

  return (
    <canvas
      ref={ref}
      aria-hidden="true"
      style={{ position: 'fixed', inset: 0, width: '100vw', height: '100vh', zIndex: 80, pointerEvents: 'none' }}
    />
  );
}
