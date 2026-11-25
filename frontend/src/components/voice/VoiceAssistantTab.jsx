import React from 'react';
import {
  Mic,
  Bot,
  Sparkles,
  PhoneCall,
  Volume2,
  Cpu,
  ShieldCheck,
  CheckCircle,
  Database,
  ArrowRight
} from 'lucide-react';

export function VoiceAssistantTab({ onOpenCall }) {
  const pipelineSteps = [
    { title: '1. Browser Microphone', desc: 'Audio captured via WebRTC / WebSocket pcm stream', icon: Mic },
    { title: '2. Silero VAD', desc: 'Voice activity detection for natural turn-taking & silence handling', icon: Volume2 },
    { title: '3. ElevenLabs STT', desc: 'Real-time conversational speech-to-text recognition', icon: Cpu },
    { title: '4. Google Gemini LLM', desc: 'Intent classification, reasoning & tool calling', icon: Bot },
    { title: '5. Appointment Service', desc: 'SQLite DB check, phone confirmation & atomic booking', icon: Database },
    { title: '6. ElevenLabs TTS', desc: 'High-fidelity natural human voice synthesis', icon: Sparkles }
  ];

  return (
    <div className="space-y-6">
      <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800/80 shadow-sm flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-2 max-w-xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs font-semibold text-blue-400">
            <Bot className="w-3.5 h-3.5" />
            <span>Real-Time Voice Assistant</span>
          </div>
          <h2 className="text-2xl font-bold text-white">
            MediVoice Phone Call Assistant
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed">
            Connect to the live voice agent. Talk directly through your microphone to query doctors, check slot availability, confirm your phone number, and schedule or cancel appointments.
          </p>
        </div>

        <button
          onClick={onOpenCall}
          className="flex items-center space-x-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-bold text-base shadow-xl shadow-blue-500/30 transition-all duration-200 active:scale-95 shrink-0"
        >
          <PhoneCall className="w-5 h-5" />
          <span>Start Voice Call Now</span>
        </button>
      </div>

      {/* Voice Architecture Flow */}
      <div className="p-6 rounded-3xl bg-slate-900/50 border border-slate-800/70 space-y-4">
        <h3 className="text-base font-bold text-white">
          Real-Time Voice Pipeline Architecture
        </h3>
        <p className="text-xs text-slate-400">
          End-to-end processing path implemented with Pipecat:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
          {pipelineSteps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div key={idx} className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 flex items-start space-x-3.5">
                <div className="w-9 h-9 rounded-xl bg-blue-600/15 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0 mt-0.5">
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-200">{step.title}</h4>
                  <p className="text-[11px] text-slate-400 mt-1 leading-snug">{step.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Operational Rules Card */}
      <div className="p-5 rounded-2xl bg-blue-950/20 border border-blue-500/20 text-xs text-slate-300 space-y-2">
        <span className="font-bold text-blue-400 flex items-center space-x-1.5 uppercase tracking-wider text-[11px]">
          <ShieldCheck className="w-4 h-4" />
          <span>Strict Caller Identification Rules</span>
        </span>
        <ul className="list-disc list-inside space-y-1 text-slate-300">
          <li>Callers identify themselves only via a spoken 10-digit mobile number during the call.</li>
          <li>The AI repeats the spoken number digit-by-digit (e.g. 9-8-7-6-5-4-3-2-1-0) and requires explicit confirmation.</li>
          <li>Phone confirmation and appointment confirmation are strictly two separate steps.</li>
          <li>Slots are booked atomically in the SQLite database to prevent double bookings.</li>
        </ul>
      </div>
    </div>
  );
}
