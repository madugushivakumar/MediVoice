import React, { useEffect, useRef } from 'react';
import { Bot, User } from 'lucide-react';

export function TranscriptView({ transcript = [], callState }) {
  const scrollRef = useRef(null);
  const isNearBottomRef = useRef(true);

  // Monitor user scroll position: if scrolled up, don't force-jump to bottom
  const handleScroll = () => {
    if (scrollRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
      isNearBottomRef.current = scrollHeight - scrollTop - clientHeight < 80;
    }
  };

  useEffect(() => {
    if (scrollRef.current && isNearBottomRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [transcript, callState]);

  if (transcript.length === 0 && callState !== 'THINKING') {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-slate-500 text-sm">
        <Bot className="w-8 h-8 text-slate-600 mb-2 opacity-50" />
        <p>Live conversation transcript will appear here...</p>
      </div>
    );
  }

  return (
    <div
      ref={scrollRef}
      onScroll={handleScroll}
      className="space-y-3 max-h-72 overflow-y-auto pr-2 scroll-smooth"
    >
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
                  : 'bg-blue-600 text-white rounded-tr-none shadow-sm shadow-blue-900/20'
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

      {/* Real-time Thinking & Reasoning Indicator */}
      {callState === 'THINKING' && (
        <div className="flex items-start space-x-2.5 justify-start animate-fade-in">
          <div className="w-7 h-7 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center shrink-0 mt-0.5">
            <Bot className="w-4 h-4 text-blue-400" />
          </div>
          <div className="rounded-2xl px-4 py-2.5 bg-slate-900 border border-slate-800 text-slate-300 text-sm flex items-center space-x-2">
            <span className="text-[11px] font-semibold text-blue-400">MediVoice AI</span>
            <div className="flex items-center space-x-1 pl-1">
              <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
              <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
              <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce"></span>
              <span className="ml-1 text-[11px] text-slate-400">is reasoning...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
