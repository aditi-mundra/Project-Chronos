import React, { useState, useEffect } from 'react';
import Login from './pages/Login';
import Round1 from './pages/Round1';
import Round2 from './pages/Round2';
import Round3 from './pages/Round3';
import Completion from './pages/Completion';
import AdminLogin from './admin/AdminLogin';
import Dashboard from './admin/Dashboard';
import { api } from './services/api';

/**
 * Project Chronos — Main Application Controller
 * Manages player authentication, current round lifecycle, admin console, and persistent session state.
 */
export default function App() {
  const [session, setSession] = useState(() => {
    const saved = localStorage.getItem('chronos_session');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return null;
      }
    }
    return null;
  });

  // Current Active Page: 'LOGIN' | 'ROUND_1' | 'ROUND_2' | 'ROUND_3' | 'COMPLETION' | 'ADMIN' | 'ADMIN_LOGIN'
  const [currentPage, setCurrentPage] = useState(() => {
    const saved = localStorage.getItem('chronos_page');
    return saved || 'LOGIN';
  });

  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(() => {
    return localStorage.getItem('chronos_admin_auth') === 'true';
  });

  // Persist session & page state
  useEffect(() => {
    if (session) {
      localStorage.setItem('chronos_session', JSON.stringify(session));
    } else {
      localStorage.removeItem('chronos_session');
    }
  }, [session]);

  useEffect(() => {
    localStorage.setItem('chronos_page', currentPage);
  }, [currentPage]);

  // Handle Login Success
  const handleLoginSuccess = (loginData) => {
    setSession(loginData);
    
    // Determine target page based on current_state
    const state = loginData.current_state;
    if (state === 'ROUND_1_ACTIVE') {
      setCurrentPage('ROUND_1');
    } else if (state === 'ROUND_2_ACTIVE' || state === 'OMEGA_DISCOVERED') {
      setCurrentPage('ROUND_2');
    } else if (state === 'ROUND_3_ACTIVE' || state === 'ROUND_2_COMPLETED') {
      setCurrentPage('ROUND_3');
    } else if (state === 'COMPLETED' || state === 'DECISION_SUBMITTED' || state === 'FINAL_REVEAL') {
      setCurrentPage('COMPLETION');
    } else {
      // Default to Round 3 for quick testing / final round access
      setCurrentPage('ROUND_3');
    }
  };

  // Handle Logout / Reset
  const handleReset = () => {
    localStorage.removeItem('chronos_session');
    localStorage.removeItem('chronos_page');
    setSession(null);
    setCurrentPage('LOGIN');
  };

  // Handle Admin Login Success
  const handleAdminLoginSuccess = () => {
    setIsAdminAuthenticated(true);
    localStorage.setItem('chronos_admin_auth', 'true');
    setCurrentPage('ADMIN');
  };

  const handleAdminLogout = () => {
    setIsAdminAuthenticated(false);
    localStorage.removeItem('chronos_admin_auth');
    setCurrentPage('LOGIN');
  };

  const currentTeamId = session?.team_id || 1;
  const currentTeamName = session?.team_name || "Temporal Engineers";

  return (
    <div className="min-h-screen bg-obsidian text-[#F5F0FF] selection:bg-neon-purple selection:text-white">
      
      {/* Dev/Demo Navigation Toolbar */}
      <div className="fixed top-2 right-2 z-50 flex items-center gap-1.5 bg-void-black/90 border border-neon-purple/30 rounded-lg p-1 text-[10px] font-mono opacity-50 hover:opacity-100 transition-all shadow-neon-subtle">
        <span className="text-neon-purple px-1 font-bold">NAV:</span>
        <button 
          onClick={() => setCurrentPage('LOGIN')} 
          className={`px-1.5 py-0.5 rounded transition-all ${currentPage === 'LOGIN' ? 'bg-neon-purple text-white font-bold shadow-neon-glow' : 'text-dusty-lavender hover:text-white'}`}
        >
          LOGIN
        </button>
        <button 
          onClick={() => setCurrentPage('ROUND_1')} 
          className={`px-1.5 py-0.5 rounded transition-all ${currentPage === 'ROUND_1' ? 'bg-neon-purple text-white font-bold shadow-neon-glow' : 'text-dusty-lavender hover:text-white'}`}
        >
          R1
        </button>
        <button 
          onClick={() => setCurrentPage('ROUND_2')} 
          className={`px-1.5 py-0.5 rounded transition-all ${currentPage === 'ROUND_2' ? 'bg-neon-purple text-white font-bold shadow-neon-glow' : 'text-dusty-lavender hover:text-white'}`}
        >
          R2
        </button>
        <button 
          onClick={() => setCurrentPage('ROUND_3')} 
          className={`px-1.5 py-0.5 rounded transition-all ${currentPage === 'ROUND_3' ? 'bg-neon-purple text-white font-bold shadow-neon-glow' : 'text-neon-light'}`}
        >
          R3 (MAIN)
        </button>
        <button 
          onClick={() => setCurrentPage('COMPLETION')} 
          className={`px-1.5 py-0.5 rounded transition-all ${currentPage === 'COMPLETION' ? 'bg-neon-purple text-white font-bold shadow-neon-glow' : 'text-dusty-lavender hover:text-white'}`}
        >
          END
        </button>
        <button 
          onClick={() => setCurrentPage(isAdminAuthenticated ? 'ADMIN' : 'ADMIN_LOGIN')} 
          className={`px-1.5 py-0.5 rounded transition-all ${currentPage.startsWith('ADMIN') ? 'bg-neon-purple text-white font-bold shadow-neon-glow' : 'text-dusty-lavender hover:text-white'}`}
        >
          ADMIN
        </button>
      </div>

      {/* Page Routing */}
      {currentPage === 'LOGIN' && (
        <Login onLoginSuccess={handleLoginSuccess} />
      )}

      {currentPage === 'ROUND_1' && (
        <Round1 
          teamId={currentTeamId}
          onAdvanceToRound2={() => setCurrentPage('ROUND_2')}
          onDirectToRound3={() => setCurrentPage('ROUND_3')}
        />
      )}

      {currentPage === 'ROUND_2' && (
        <Round2 
          teamId={currentTeamId}
          onAdvanceToRound3={() => setCurrentPage('ROUND_3')}
        />
      )}

      {currentPage === 'ROUND_3' && (
        <Round3 
          teamId={currentTeamId}
          teamName={currentTeamName}
          onNavigateToCompletion={() => setCurrentPage('COMPLETION')}
        />
      )}

      {currentPage === 'COMPLETION' && (
        <Completion 
          teamId={currentTeamId}
          onRestart={handleReset}
        />
      )}

      {currentPage === 'ADMIN_LOGIN' && (
        <AdminLogin onLoginSuccess={handleAdminLoginSuccess} />
      )}

      {currentPage === 'ADMIN' && (
        <Dashboard onLogout={handleAdminLogout} />
      )}

    </div>
  );
}
