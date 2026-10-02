import React, { useState, useEffect } from 'react';
import { Clock, AlertTriangle } from 'lucide-react';

/**
 * Project Chronos — Synchronized Countdown Timer Component
 * Black-heavy surface with neon purple telemetry ring and dynamic critical alarm state.
 */
export default function Timer({ 
  initialMinutes = 5, 
  startedAt = null,
  onExpire = null,
  className = "" 
}) {
  const [secondsRemaining, setSecondsRemaining] = useState(initialMinutes * 60);

  useEffect(() => {
    let totalTargetSec = initialMinutes * 60;

    if (startedAt) {
      try {
        const startTime = new Date(startedAt).getTime();
        const nowTime = Date.now();
        const elapsedSec = Math.floor((nowTime - startTime) / 1000);
        totalTargetSec = Math.max(0, initialMinutes * 60 - elapsedSec);
      } catch (e) {
        console.error("Timer parse error:", e);
      }
    }

    setSecondsRemaining(totalTargetSec);

    const interval = setInterval(() => {
      setSecondsRemaining(prev => {
        if (prev <= 1) {
          clearInterval(interval);
          if (onExpire) onExpire();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [initialMinutes, startedAt, onExpire]);

  const minutes = Math.floor(secondsRemaining / 60);
  const seconds = secondsRemaining % 60;
  const isUrgent = secondsRemaining < 90; // under 1.5 minutes
  const isCritical = secondsRemaining < 30; // under 30 seconds

  const progressPercent = Math.min(100, Math.max(0, (secondsRemaining / (initialMinutes * 60)) * 100));

  return (
    <div className={`flex items-center gap-3 bg-surface-dark/95 border ${
      isCritical 
        ? 'border-danger-crimson text-danger-crimson animate-pulse glow-danger' 
        : isUrgent 
          ? 'border-[#F59E0B] text-[#F59E0B]' 
          : 'border-neon-purple/35 text-solar-cream glow-neon-subtle'
    } px-4 py-2 rounded-xl backdrop-blur-xl transition-all ${className}`}>
      <div className="relative w-8 h-8 flex items-center justify-center">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
          <circle
            cx="18"
            cy="18"
            r="15.5"
            fill="none"
            stroke="rgba(168, 85, 247, 0.15)"
            strokeWidth="3"
          />
          <circle
            cx="18"
            cy="18"
            r="15.5"
            fill="none"
            stroke={isCritical ? "#EF4444" : isUrgent ? "#F59E0B" : "#A855F7"}
            strokeWidth="3"
            strokeDasharray="97.4"
            strokeDashoffset={97.4 - (97.4 * progressPercent) / 100}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-linear"
          />
        </svg>
        {isCritical ? (
          <AlertTriangle className="w-4 h-4 absolute text-danger-crimson animate-bounce" />
        ) : (
          <Clock className="w-4 h-4 absolute text-neon-light opacity-90" />
        )}
      </div>

      <div>
        <div className="text-[10px] tracking-widest uppercase font-mono text-dusty-lavender">
          {isCritical ? "CRITICAL LOCK" : "SYNC TIME"}
        </div>
        <div className="font-orbitron font-bold text-lg tracking-wider text-white">
          {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
        </div>
      </div>
    </div>
  );
}
