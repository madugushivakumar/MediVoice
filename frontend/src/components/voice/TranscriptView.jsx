import React, { useEffect, useRef } from 'react';
import { Bot, User, Clock } from 'lucide-react';

export function TranscriptView({ transcript = [] }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript]);

  if (transcript.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-slate-500 text-sm">
        <Bot className="w-8 h-8 text-slate-600 mb-2 opacity-50" />
        <p>Live conversation transcript will appear here...</p>
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="space-y-3 max-h-72 overflow-y-auto pr-2">
      {transcript.map((msg, idx) => {
        const isAI = msg.speaker === 'AI';
        const timeStr = msg.timestamp
          ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
          : '';

        return (
          <div
            key={idx}
            className={`flex items-start space-x-2.5 ${isAI ? 'justify-start' : 'justify-end'}`}
          >
            {isAI && (
              <div className="w-7 h-7 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="w-4 h-4 text-blue-400" />
              </div>
            )}
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                isAI
                  ? 'bg-slate-900 border border-slate-800 text-slate-200'
                  : 'bg-blue-600 text-white rounded-tr-none'
              }`}
            >
              <div className="flex items-center justify-between space-x-2 mb-1">
                <span className={`text-[11px] font-semibold ${isAI ? 'text-blue-400' : 'text-blue-100'}`}>
                  {isAI ? 'MediVoice AI' : 'Caller'}
                </span>
                {timeStr && (
                  <span className={`text-[10px] ${isAI ? 'text-slate-500' : 'text-blue-200'}`}>
                    {timeStr}
                  </span>
                )}
              </div>
              <p className="whitespace-pre-wrap">{msg.message}</p>
            </div>
            {!isAI && (
              <div className="w-7 h-7 rounded-lg bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center shrink-0 mt-0.5">
                <User className="w-4 h-4 text-cyan-400" />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
