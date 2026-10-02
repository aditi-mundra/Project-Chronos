import React, { useState, useEffect } from 'react';
import { Terminal, RotateCcw } from 'lucide-react';
import { api } from '../services/api';

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const res = await api.getAdminLogs(50);
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
  }, []);

  return (
    <div className="space-y-4 font-space text-[#F5F0FF]">
      <div className="flex items-center justify-between pb-3 border-b border-neon-purple/20">
        <div className="flex items-center gap-2">
          <Terminal className="w-6 h-6 text-neon-light" />
          <h2 className="font-orbitron font-bold text-xl text-white">
            TELEMETRY & AUDIT <span className="text-neon-purple">LOGS</span>
          </h2>
        </div>
        <button
          onClick={fetchLogs}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-void-black border border-neon-purple/30 text-xs font-mono text-dusty-lavender hover:text-neon-light hover:border-neon-purple transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>REFRESH LOGS</span>
        </button>
      </div>

      <div className="space-y-2 max-h-[600px] overflow-y-auto font-mono text-xs">
        {logs.map((log) => (
          <div key={log.id} className="p-3 bg-void-black rounded-xl border border-neon-purple/20 flex flex-wrap items-center justify-between gap-2 hover:border-neon-purple/40 transition-all">
            <div className="flex items-center gap-3">
              <span className="px-2 py-0.5 rounded bg-neon-purple/25 border border-neon-purple/40 text-neon-light font-bold text-[10px]">
                {log.event_type}
              </span>
              <span className="text-white font-bold">{log.team_name || `Team #${log.team_id}`}</span>
              <span className="text-dusty-lavender text-[11px] truncate max-w-lg">{log.event_data}</span>
            </div>
            <span className="text-dusty-lavender/70 text-[10px]">{log.created_at}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
