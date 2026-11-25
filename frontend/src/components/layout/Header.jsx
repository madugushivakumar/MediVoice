import React from 'react';
import { Stethoscope, PhoneCall, Radio, Activity, ShieldCheck } from 'lucide-react';

export function Header({ onOpenCall, activeCallsCount = 0 }) {
  return (
    <header className="sticky top-0 z-30 h-16 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md px-6 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Stethoscope className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-lg font-bold tracking-tight text-white">MediVoice</h1>
            <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Voice AI 2.0
            </span>
          </div>
          <p className="text-xs text-slate-400">Doctor Appointment Voice Assistant</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* System Status indicator */}
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Pipecat + Gemini Engine Active</span>
        </div>

        {/* Try Call Action Button */}
        <button
          onClick={onOpenCall}
          className="relative group flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-medium text-sm shadow-lg shadow-blue-500/25 transition-all duration-200 active:scale-95"
        >
          <PhoneCall className="w-4 h-4 group-hover:rotate-12 transition-transform duration-200" />
          <span>Try Call</span>
          <span className="absolute -top-1 -right-1 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
          </span>
        </button>
      </div>
    </header>
  );
}
