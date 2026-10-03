import React, { useState, useEffect } from 'react';
import { Terminal, RotateCcw, Activity } from 'lucide-react';
import { soundEngine } from '../components/AudioEngine';
import { api } from '../services/api';

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const res = await api.getAdminLogs(100);
      if (res.logs) {
        setLogs(res.logs);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6 font-space text-[var(--text-body)]">
      <div className="flex items-center justify-between pb-4 border-b border-white/15">
        <div className="flex items-center gap-3">
          <Terminal className="w-7 h-7 text-[var(--neon-light)]" />
          <div>
            <h2 className="font-orbitron font-black text-2xl text-white">
              LIVE AUDIT & TELEMETRY STREAM
            </h2>
            <p className="text-sm font-mono text-[var(--text-muted)]">
              Real-time audit log of team decisions, logins, and state transitions
            </p>
          </div>
        </div>
        
        <button
          onClick={() => {
            soundEngine.playClick();
            fetchLogs();
          }}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 border border-white/15 text-sm font-mono text-[var(--text-muted)] hover:text-white hover:border-[var(--neon-primary)] transition-all cursor-pointer"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      <div className="space-y-3 max-h-[650px] overflow-y-auto font-mono text-sm pr-2">
        {logs.map((log) => {
          const isSubmit = log.event_type.includes('SUBMIT');
          const isStart = log.event_type.includes('START');
          const isLogin = log.event_type.includes('LOGIN');

          return (
            <div 
              key={log.id} 
              className="p-4 bg-black/60 rounded-xl border border-white/10 flex flex-wrap items-center justify-between gap-3 hover:border-[var(--neon-primary)] transition-all"
            >
              <div className="flex items-center gap-3 flex-wrap">
                <span 
                  className="px-2.5 py-1 rounded-md font-bold text-xs uppercase tracking-wider border"
                  style={{
                    backgroundColor: isSubmit ? 'rgba(16, 185, 129, 0.2)' : isStart ? 'rgba(6, 182, 212, 0.2)' : 'var(--theme-accent-badge-bg)',
                    borderColor: isSubmit ? 'rgba(16, 185, 129, 0.4)' : isStart ? 'rgba(6, 182, 212, 0.4)' : 'var(--theme-accent-badge-border)',
                    color: isSubmit ? '#34D399' : isStart ? '#38BDF8' : 'var(--neon-light)'
                  }}
                >
                  {log.event_type}
                </span>

                <span className="text-white font-bold font-space text-base">
                  {log.team_name || `Team #${log.team_id}`}
                </span>

                <span className="text-[var(--text-muted)] text-xs truncate max-w-xl bg-black/40 px-2.5 py-1 rounded border border-white/5">
                  {log.event_data}
                </span>
              </div>

              <span className="text-[var(--text-dim)] text-xs">
                {log.created_at}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

