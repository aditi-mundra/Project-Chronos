import React from 'react';
import { Palette } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { soundEngine } from './AudioEngine';

const OPTIONS = [
  { id: 'neon-purple', title: 'Neon Purple Theme', on: 'bg-purple-500 ring-2 ring-purple-300 shadow-[0_0_12px_rgba(168,85,247,0.8)]', off: 'bg-purple-950/80 border border-purple-800 hover:border-purple-400' },
  { id: 'neon-blue', title: 'Neon Cyan Theme', on: 'bg-cyan-400 ring-2 ring-cyan-200 shadow-[0_0_12px_rgba(6,182,212,0.8)]', off: 'bg-cyan-950/80 border border-cyan-800 hover:border-cyan-400' },
  { id: 'neon-green', title: 'Neon Emerald Theme', on: 'bg-emerald-400 ring-2 ring-emerald-200 shadow-[0_0_12px_rgba(16,185,129,0.8)]', off: 'bg-emerald-950/80 border border-emerald-800 hover:border-emerald-400' },
];

/**
 * Chromatic theme switcher (admin console and completion screen).
 */
export default function ThemeSelector({ className = '' }) {
  const { theme, setTheme } = useTheme();

  return (
    <div className={`flex items-center gap-1.5 bg-black/60 border border-white/10 rounded-xl p-1 backdrop-blur-md ${className}`}>
      <span className="px-1 flex items-center gap-1 text-slate-400">
        <Palette className="w-3 h-3" />
      </span>
      {OPTIONS.map((o) => (
        <button
          key={o.id}
          type="button"
          title={o.title}
          onClick={() => {
            soundEngine.playClick();
            setTheme(o.id);
          }}
          className={`w-5 h-5 rounded-lg transition-all ${
            theme === o.id ? `${o.on} scale-110` : `${o.off} opacity-60 hover:opacity-100`
          }`}
        />
      ))}
    </div>
  );
}
