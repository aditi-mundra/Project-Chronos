import React from 'react';
import { Palette } from 'lucide-react';
import { useTheme, THEMES } from '../context/ThemeContext';
import { soundEngine } from './AudioEngine';

/**
 * Universal Chromatic Theme Switcher Component
 * Switches between Neon Purple, Neon Cyan/Blue, and Neon Matrix Green.
 */
export default function ThemeSelector({ className = "" }) {
  const { currentTheme, setTheme } = useTheme();

  return (
    <div className={`flex items-center gap-1.5 bg-black/60 border border-white/10 rounded-xl p-1 backdrop-blur-md ${className}`}>
      <span className="text-[10px] font-mono text-dusty-lavender px-1 flex items-center gap-1">
        <Palette className="w-3 h-3 text-dusty-lavender" />
      </span>

      {/* Purple Pill */}
      <button
        type="button"
        onClick={() => {
          soundEngine.playClick();
          setTheme('purple');
        }}
        title="Neon Purple Theme"
        className={`w-5 h-5 rounded-lg flex items-center justify-center transition-all ${
          currentTheme === 'purple'
            ? 'bg-purple-500 ring-2 ring-purple-300 scale-110 shadow-[0_0_12px_rgba(168,85,247,0.8)]'
            : 'bg-purple-950/80 border border-purple-800 hover:border-purple-400 opacity-60 hover:opacity-100'
        }`}
      />

      {/* Blue / Cyan Pill */}
      <button
        type="button"
        onClick={() => {
          soundEngine.playClick();
          setTheme('blue');
        }}
        title="Neon Cyan Theme"
        className={`w-5 h-5 rounded-lg flex items-center justify-center transition-all ${
          currentTheme === 'blue'
            ? 'bg-cyan-400 ring-2 ring-cyan-200 scale-110 shadow-[0_0_12px_rgba(6,182,212,0.8)]'
            : 'bg-cyan-950/80 border border-cyan-800 hover:border-cyan-400 opacity-60 hover:opacity-100'
        }`}
      />

      {/* Green / Matrix Pill */}
      <button
        type="button"
        onClick={() => {
          soundEngine.playClick();
          setTheme('green');
        }}
        title="Neon Emerald Theme"
        className={`w-5 h-5 rounded-lg flex items-center justify-center transition-all ${
          currentTheme === 'green'
            ? 'bg-emerald-400 ring-2 ring-emerald-200 scale-110 shadow-[0_0_12px_rgba(16,185,129,0.8)]'
            : 'bg-emerald-950/80 border border-emerald-800 hover:border-emerald-400 opacity-60 hover:opacity-100'
        }`}
      />
    </div>
  );
}
