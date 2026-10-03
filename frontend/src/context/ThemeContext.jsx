import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const THEMES = {
  purple: {
    id: 'purple',
    name: 'Neon Violet',
    primary: '#A855F7',
    light: '#C084FC',
    glowColor: 'rgba(168, 85, 247, 0.45)',
    gradient: 'from-purple-600 via-fuchsia-600 to-purple-500',
    ring: 'ring-purple-500',
    border: 'border-purple-500/40',
    text: 'text-purple-400',
    bgBadge: 'bg-purple-500/20 text-purple-300 border-purple-500/40'
  },
  blue: {
    id: 'blue',
    name: 'Neon Cyan',
    primary: '#06B6D4',
    light: '#67E8F9',
    glowColor: 'rgba(6, 182, 212, 0.45)',
    gradient: 'from-cyan-600 via-blue-600 to-cyan-400',
    ring: 'ring-cyan-500',
    border: 'border-cyan-500/40',
    text: 'text-cyan-400',
    bgBadge: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
  },
  green: {
    id: 'green',
    name: 'Neon Matrix',
    primary: '#10B981',
    light: '#34D399',
    glowColor: 'rgba(16, 185, 129, 0.45)',
    gradient: 'from-emerald-600 via-teal-600 to-emerald-400',
    ring: 'ring-emerald-500',
    border: 'border-emerald-500/40',
    text: 'text-emerald-400',
    bgBadge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
  }
};

export function ThemeProvider({ children }) {
  const [currentTheme, setCurrentTheme] = useState(() => {
    return localStorage.getItem('chronos_theme') || 'purple';
  });

  useEffect(() => {
    localStorage.setItem('chronos_theme', currentTheme);
    document.documentElement.setAttribute('data-theme', currentTheme);
  }, [currentTheme]);

  const setTheme = (themeId) => {
    if (THEMES[themeId]) {
      setCurrentTheme(themeId);
    }
  };

  const themeConfig = THEMES[currentTheme] || THEMES.purple;

  return (
    <ThemeContext.Provider value={{ currentTheme, setTheme, themeConfig, THEMES }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
