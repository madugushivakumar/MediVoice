import React, { useState } from 'react';
import {
  Phone,
  PhoneOff,
  Mic,
  MicOff,
  X,
  Bot,
  Activity,
  Send,
  Sparkles,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { WaveformVisualizer } from './WaveformVisualizer';
import { TranscriptView } from './TranscriptView';
import { BookingConfirmationCard } from './BookingConfirmationCard';

// Predefined lists for dynamic quick prompts
const SPECIALIZATIONS = [
  'Cardiologist',
  'Neurologist',
  'Dermatologist',
  'Orthopedic',
  'Dentist',
  'General Physician',
  'ENT Specialist',
  'Ophthalmologist',
  'Gynecologist',
  'Pediatrician'
];

const APPOINTMENT_TIMES = [
  '09:00 AM',
  '09:30 AM',
  '10:00 AM',
  '10:30 AM',
  '11:00 AM',
  '11:30 AM',
  '12:00 PM',
  '02:00 PM',
  '02:30 PM',
  '03:00 PM',
  '04:00 PM',
  '04:30 PM'
];

const generateRandomPhoneNumber = () => {
  const firstDigit = Math.floor(Math.random() * 4) + 6; // 6, 7, 8, or 9
  let remaining = '';
  for (let i = 0; i < 9; i++) {
    remaining += Math.floor(Math.random() * 10);
  }
  return `${firstDigit}${remaining}`;
};

const getRandomItem = (items) => items[Math.floor(Math.random() * items.length)];
const formatSpecialization = (spec) => (spec === 'ENT Specialist' ? 'ENT specialist' : spec.toLowerCase());

// Generated once per page session; refreshed on every browser reload
const SESSION_QUICK_PROMPTS = [
  `I need an appointment with a ${formatSpecialization(getRandomItem(SPECIALIZATIONS))} tomorrow`,
  `What about ${getRandomItem(APPOINTMENT_TIMES)}?`,
  generateRandomPhoneNumber(),
  'Yes, that is correct',
  'Yes, book it',
  'I want to cancel my appointment'
];

export function PhoneCallModal({
  isOpen,
  onClose,
  callState,
  pipelineMode,
  callDuration,
  isMuted,
  transcript,
  audioLevel,
  errorMessage,
  bookingConfirmation,
  lastToolExecution,
  onStartCall,
  onEndCall,
  onToggleMute,
  onSendSpokenInput
}) {
  const [inputText, setInputText] = useState('');
  const [quickPrompts] = useState(SESSION_QUICK_PROMPTS);

  if (!isOpen) return null;

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    onSendSpokenInput(inputText.trim());
    setInputText('');
  };

  const getStateBadge = () => {
    switch (callState) {
      case 'CONNECTING':
        return { label: 'Connecting...', bg: 'bg-amber-500/10 text-amber-400 border-amber-500/20' };
      case 'CONNECTED':
        return { label: 'Connected', bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' };
      case 'LISTENING':
        return { label: 'Listening to you...', bg: 'bg-blue-500/10 text-blue-400 border-blue-500/20' };
      case 'THINKING':
        return { label: 'AI Reasoning...', bg: 'bg-purple-500/10 text-purple-400 border-purple-500/20' };
      case 'SPEAKING':
        return { label: 'AI Speaking...', bg: 'bg-teal-500/10 text-teal-400 border-teal-500/20' };
      case 'ENDING':
      case 'ENDED':
        return { label: 'Call Ended', bg: 'bg-slate-500/10 text-slate-400 border-slate-500/20' };
      case 'ERROR':
        return { label: 'Call Error', bg: 'bg-rose-500/10 text-rose-400 border-rose-500/20' };
      default:
        return { label: 'Idle', bg: 'bg-slate-500/10 text-slate-400 border-slate-500/20' };
    }
  };

  const stateInfo = getStateBadge();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-3xl bg-slate-950 border border-slate-800 shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Phone Header */}
        <div className="p-4 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-500 border-2 border-slate-950"></span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-bold text-white">MediVoice Assistant</h3>
                {pipelineMode && (
                  <span className={`px-2 py-0.2 text-[9px] font-bold rounded-full uppercase tracking-wider ${
                    pipelineMode === 'LIVE_VOICE'
                      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                      : 'bg-blue-500/10 text-cyan-400 border border-cyan-500/20'
                  }`}>
                    {pipelineMode === 'LIVE_VOICE' ? 'Live Pipecat Voice' : 'Text / Prompt Mode'}
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-2 mt-0.5">
                <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-full border ${stateInfo.bg}`}>
                  {stateInfo.label}
                </span>
                {callState !== 'ENDED' && callState !== 'IDLE' && (
                  <span className="font-mono text-xs text-slate-400">
                    {formatTimer(callDuration)}
                  </span>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={() => {
              if (callState !== 'ENDED' && callState !== 'IDLE') {
                onEndCall();
              }
              onClose();
            }}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Call Body */}
        <div className="p-5 flex-1 overflow-y-auto space-y-4">
          
          {/* Error notice if any */}
          {errorMessage && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Mode information banner if cloud keys not yet configured */}
          {pipelineMode === 'TEXT_FALLBACK' && (
            <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-slate-300 text-xs flex items-start space-x-2.5">
              <Sparkles className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-white block mb-0.5">Microphone streaming active</span>
                <span className="text-[11px] text-slate-400">
                  Microphone audio is actively streamed to the backend. To enable real-time speech recognition via ElevenLabs STT & Gemini LLM, configure <code className="text-cyan-300 bg-slate-900 px-1 py-0.5 rounded">ELEVENLABS_API_KEY</code> and <code className="text-cyan-300 bg-slate-900 px-1 py-0.5 rounded">GEMINI_API_KEY</code> in <code className="text-cyan-300 bg-slate-900 px-1 py-0.5 rounded">voice-agent/.env</code>. All appointment tools can also be demonstrated below.
                </span>
              </div>
            </div>
          )}

          {/* Waveform Visualizer */}
          <div className="p-3 rounded-2xl bg-slate-900/50 border border-slate-800/70">
            <WaveformVisualizer audioLevel={audioLevel} state={callState} />
          </div>

          {/* Booking Confirmation Card if booking just occurred */}
          {bookingConfirmation && (
            <BookingConfirmationCard confirmation={bookingConfirmation} />
          )}

          {/* Conversation Transcript */}
          <div className="p-3.5 rounded-2xl bg-slate-900/40 border border-slate-800/60">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
              Live Transcript
            </span>
            <TranscriptView transcript={transcript} callState={callState} />
          </div>

          {/* Quick Voice / Text Prompts for Demonstration */}
          {callState !== 'ENDED' && (
            <div className="space-y-1.5">
              <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
                Quick Spoken Prompts (click to simulate speech):
              </span>
              <div className="flex flex-wrap gap-1.5">
                {quickPrompts.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => onSendSpokenInput(prompt)}
                    className="px-2.5 py-1 rounded-lg text-xs bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition-all text-left"
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Call Footer Controls */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/60 space-y-3">
          
          {/* Spoken text input fallback */}
          {callState !== 'ENDED' && (
            <form onSubmit={handleSend} className="flex items-center space-x-2">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Speak into microphone or type here..."
                className="flex-1 px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
              />
              <button
                type="submit"
                className="p-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          )}

          {/* Action Call Buttons */}
          <div className="flex items-center justify-center space-x-6">
            {callState === 'ENDED' || callState === 'IDLE' ? (
              <button
                onClick={onStartCall}
                className="flex items-center space-x-2 px-6 py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-lg shadow-emerald-600/30 transition-all active:scale-95"
              >
                <Phone className="w-4 h-4" />
                <span>Call Again</span>
              </button>
            ) : (
              <>
                {/* Mute Button */}
                <button
                  onClick={onToggleMute}
                  className={`p-3.5 rounded-2xl border transition-all active:scale-90 ${
                    isMuted
                      ? 'bg-amber-500/20 border-amber-500/40 text-amber-400'
                      : 'bg-slate-800/80 border-slate-700 text-slate-200 hover:bg-slate-700'
                  }`}
                  title={isMuted ? 'Unmute microphone' : 'Mute microphone'}
                >
                  {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                </button>

                {/* End Call Button */}
                <button
                  onClick={onEndCall}
                  className="p-4 rounded-2xl bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30 transition-all active:scale-90"
                  title="End Call"
                >
                  <PhoneOff className="w-6 h-6" />
                </button>
              </>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
