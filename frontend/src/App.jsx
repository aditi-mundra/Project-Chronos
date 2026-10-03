import React, { useState, useEffect } from 'react';
import Login from './pages/Login';
import Round1 from './pages/Round1';
import Round2 from './pages/Round2';
import Round3 from './pages/Round3';
import Completion from './pages/Completion';
import AdminLogin from './admin/AdminLogin';
import Dashboard from './admin/Dashboard';
import { ThemeProvider } from './context/ThemeContext';
import { api } from './services/api';

/**
 * Project Chronos — Main Application Controller
 * Manages player authentication, current round lifecycle, admin console, and persistent session state.
 */
function AppContent() {
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
    // If URL contains #admin or ?admin, open admin
    if (window.location.hash === '#admin' || window.location.pathname.includes('/admin')) {
      const isAuthed = localStorage.getItem('chronos_admin_auth') === 'true';
      return isAuthed ? 'ADMIN' : 'ADMIN_LOGIN';
    }
    const saved = localStorage.getItem('chronos_page');
    return saved || 'LOGIN';
  });

  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(() => {
    return localStorage.getItem('chronos_admin_auth') === 'true';
  });

  // Secret Admin hotkey: Ctrl + Shift + A (or Cmd + Shift + A)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'A' || e.key === 'a')) {
        e.preventDefault();
        setCurrentPage(prev => {
          if (prev === 'ADMIN' || prev === 'ADMIN_LOGIN') {
            return 'ROUND_3';
          }
          return isAdminAuthenticated ? 'ADMIN' : 'ADMIN_LOGIN';
        });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isAdminAuthenticated]);

  // Persist session & page state
  useEffect(() => {
    if (session) {
      localStorage.setItem('chronos_session', JSON.stringify(session));
    } else {
      localStorage.removeItem('chronos_session');
    }
  }, [session]);

  useEffect(() => {
    if (!currentPage.startsWith('ADMIN')) {
      localStorage.setItem('chronos_page', currentPage);
    }
  }, [currentPage]);

  // Handle Login Success
  const handleLoginSuccess = (loginData) => {
    setSession(loginData);
    
    // Direct player to appropriate stage
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
    <div className="min-h-screen bg-[#07060A] text-[#F5F0FF] selection:bg-purple-600 selection:text-white relative">
      
      {/* Page Routing */}
      {currentPage === 'LOGIN' && (
        <Login 
          onLoginSuccess={handleLoginSuccess} 
          onOpenAdmin={() => setCurrentPage(isAdminAuthenticated ? 'ADMIN' : 'ADMIN_LOGIN')}
        />
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

export default function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}
