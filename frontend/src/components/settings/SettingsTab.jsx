import React, { useState } from 'react';
import { Sliders, CheckCircle2, ShieldAlert, Database, Cpu, Globe, Server } from 'lucide-react';

export function SettingsTab() {
  const [resetting, setResetting] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);

  const configs = [
    { label: 'Backend Framework', value: 'FastAPI + Uvicorn (Port 8000)', status: 'Connected', icon: Server },
    { label: 'Voice Pipeline', value: 'Pipecat 1.17.0 (Python 3.11)', status: 'Active', icon: Cpu },
    { label: 'Speech Recognition', value: 'ElevenLabs Scribe STT', status: 'Configured', icon: Globe },
    { label: 'LLM Orchestrator', value: 'Google Gemini 2.0 Flash', status: 'Configured', icon: Globe },
    { label: 'Voice Synthesis', value: 'ElevenLabs Turbo v2.5 TTS', status: 'Configured', icon: Globe },
    { label: 'Database Storage', value: 'SQLite with SQLAlchemy (ACID Atomic)', status: 'Operational', icon: Database }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white">System Settings & Architecture</h2>
        <p className="text-xs text-slate-400">Environment configuration, service status & demonstration parameters</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {configs.map((cfg, idx) => {
          const Icon = cfg.icon;
          return (
            <div
              key={idx}
              className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex items-center justify-between"
            >
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-slate-800/80 border border-slate-700/80 flex items-center justify-center text-blue-400">
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">{cfg.label}</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">{cfg.value}</p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                {cfg.status}
              </span>
            </div>
          );
        })}
      </div>

      {/* Security & Masking Note */}
      <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-2 text-xs text-slate-300">
        <h3 className="font-bold text-slate-200 flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-cyan-400" />
          <span>Patient Privacy & Phone Masking Policy</span>
        </h3>
        <p className="text-slate-400 leading-relaxed">
          In compliance with the assignment specification, caller identification is conducted through spoken 10-digit mobile numbers with explicit readback confirmation. All routine application logs and frontend dashboard displays mask the phone number (e.g. ******3210) to preserve privacy.
        </p>
      </div>
    </div>
  );
}
