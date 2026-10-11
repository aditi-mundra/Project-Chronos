import { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext(null);

export const THEMES = [
  { id: 'neon-blue', name: 'Neon Blue (Cyan)', primaryColor: '#06b6d4', glowColor: 'rgba(6, 182, 212, 0.6)' },
  { id: 'neon-purple', name: 'Neon Purple (Synth)', primaryColor: '#a855f7', glowColor: 'rgba(168, 85, 247, 0.6)' },
  { id: 'neon-green', name: 'Neon Green (Matrix)', primaryColor: '#10b981', glowColor: 'rgba(16, 185, 129, 0.6)' }
];

function getRandomThemeId() {
  const randomIndex = Math.floor(Math.random() * THEMES.length);
  return THEMES[randomIndex].id;
}

export const ThemeProvider = ({ children }) => {
  // Randomly select one of 3 themes on initial load
  const [theme, setTheme] = useState(() => {
    try {
      const stored = sessionStorage.getItem('chronos_theme');
      return stored || getRandomThemeId();
    } catch {
      return getRandomThemeId();
    }
  });

  useEffect(() => {
    try {
      sessionStorage.setItem('chronos_theme', theme);
    } catch {
      // Ignore sessionStorage issues
    }
    // Set attribute on document element for CSS variables
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.classList.remove('theme-neon-blue', 'theme-neon-purple', 'theme-neon-green');
    document.documentElement.classList.add(`theme-${theme}`);
  }, [theme]);

  const selectRandomTheme = () => {
    let nextTheme = getRandomThemeId();
    while (nextTheme === theme && THEMES.length > 1) {
      nextTheme = getRandomThemeId();
    }
    setTheme(nextTheme);
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, selectRandomTheme, availableThemes: THEMES }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    return {
      theme: 'neon-blue',
      setTheme: () => {},
      selectRandomTheme: () => {},
      availableThemes: THEMES
    };
  }
  return context;
};

export default ThemeContext;
