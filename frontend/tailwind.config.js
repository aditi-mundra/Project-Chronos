/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Black Heavy (Primary)
        'obsidian': '#08060C',
        'void-black': '#030205',
        'surface-dark': '#100C18',
        'surface-card': '#140F1F',
        
        // Neon Purple Accents
        'neon-purple': '#A855F7',
        'neon-violet': '#9333EA',
        'neon-light': '#C084FC',
        'neon-fuchsia': '#D946EF',
        'electric-indigo': '#8B5CF6',
        
        // Soft Purple Hues from Theme
        'deep-violet': '#24142E',
        'soft-purple': '#5A3D73',
        'dusty-lavender': '#9D8BB9',
        'muted-lavender': '#7C679E',
        
        // Highlights & Semantic States
        'solar-cream': '#C8C793',
        'solar-bright': '#F0EFA8',
        'danger-crimson': '#EF4444',
      },
      fontFamily: {
        orbitron: ['Orbitron', 'sans-serif'],
        space: ['"Space Grotesk"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'neon-glow': '0 0 24px rgba(168, 85, 247, 0.45), 0 0 8px rgba(192, 132, 252, 0.50)',
        'neon-active': '0 0 36px rgba(168, 85, 247, 0.70), 0 0 16px rgba(192, 132, 252, 0.85)',
        'purple-soft': '0 0 28px rgba(124, 103, 158, 0.25)',
        'solar-glow': '0 0 20px rgba(200, 199, 147, 0.35)',
        'danger-glow': '0 0 24px rgba(239, 68, 68, 0.50)',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'neon-pulse': 'neonPulse 2s ease-in-out infinite alternate',
        'scanline': 'scanline 8s linear infinite',
      },
      keyframes: {
        neonPulse: {
          '0%': { boxShadow: '0 0 18px rgba(168, 85, 247, 0.35)' },
          '100%': { boxShadow: '0 0 32px rgba(168, 85, 247, 0.75), 0 0 12px rgba(192, 132, 252, 0.9)' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(1000%)' },
        },
      }
    },
  },
  plugins: [],
}
