import React from 'react';

export function WaveformVisualizer({ audioLevel = 0, state = 'CONNECTED' }) {
  // Generate 24 animated bars
  const barsCount = 24;

  const getGlowColor = () => {
    switch (state) {
      case 'SPEAKING':
        return 'from-emerald-500 to-teal-400';
      case 'THINKING':
        return 'from-indigo-500 to-purple-400';
      case 'LISTENING':
      case 'CONNECTED':
        return 'from-cyan-400 to-blue-500';
      default:
        return 'from-slate-600 to-slate-500';
    }
  };

  return (
    <div className="flex items-center justify-center space-x-1.5 h-16 px-4">
      {Array.from({ length: barsCount }).map((_, index) => {
        // Compute pseudo-random height variation modulated by live audioLevel
        const offset = Math.sin((index / barsCount) * Math.PI) * 0.8;
        const baseHeight = 12;
        const reactiveHeight = Math.max(8, baseHeight + audioLevel * 48 * offset);
        
        return (
          <div
            key={index}
            className={`w-1.5 rounded-full bg-gradient-to-t ${getGlowColor()} transition-all duration-75`}
            style={{
              height: `${reactiveHeight}px`,
              opacity: state === 'IDLE' ? 0.3 : Math.max(0.4, audioLevel * 1.5 + 0.4)
            }}
          />
        );
      })}
    </div>
  );
}
