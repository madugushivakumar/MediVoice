import { useState, useRef, useEffect, useCallback } from 'react';
import { api } from '../services/api';

const WS_BASE = import.meta.env.VITE_VOICE_SERVER_URL || 'ws://localhost:8000';

export function useVoiceCall() {
  const [callState, setCallState] = useState('IDLE'); // IDLE, CONNECTING, CONNECTED, LISTENING, THINKING, SPEAKING, ENDING, ENDED, ERROR
  const [sessionId, setSessionId] = useState(null);
  const [callDuration, setCallDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const [audioLevel, setAudioLevel] = useState(0);
  const [errorMessage, setErrorMessage] = useState(null);
  const [pipelineMode, setPipelineMode] = useState('CONNECTING'); // LIVE_VOICE, TEXT_FALLBACK
  const [bookingConfirmation, setBookingConfirmation] = useState(null);
  const [lastToolExecution, setLastToolExecution] = useState(null);

  const wsRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const sourceRef = useRef(null);
  const processorRef = useRef(null);
  const muteGainRef = useRef(null);
  const animFrameRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const isMutedRef = useRef(false);
  const nextPlaybackTimeRef = useRef(0);
  const activeAudioSourcesRef = useRef([]);
  const thinkingTimeoutRef = useRef(null);

  // Sync ref with state
  useEffect(() => {
    isMutedRef.current = isMuted;
  }, [isMuted]);

  // Clean audio and stream resources
  const cleanupAudio = useCallback(() => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    if (thinkingTimeoutRef.current) {
      clearTimeout(thinkingTimeoutRef.current);
      thinkingTimeoutRef.current = null;
    }

    // Disconnect Web Audio processor nodes
    if (processorRef.current) {
      try {
        processorRef.current.disconnect();
        processorRef.current.onaudioprocess = null;
      } catch (e) {}
      processorRef.current = null;
    }
    if (muteGainRef.current) {
      try {
        muteGainRef.current.disconnect();
      } catch (e) {}
      muteGainRef.current = null;
    }
    if (sourceRef.current) {
      try {
        sourceRef.current.disconnect();
      } catch (e) {}
      sourceRef.current = null;
    }
    if (analyserRef.current) {
      try {
        analyserRef.current.disconnect();
      } catch (e) {}
      analyserRef.current = null;
    }

    // Stop MediaStream tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch (e) {}
      });
      streamRef.current = null;
    }

    // Stop and disconnect any actively playing assistant audio sources
    if (activeAudioSourcesRef.current) {
      activeAudioSourcesRef.current.forEach((src) => {
        try {
          src.stop();
          src.disconnect();
        } catch (e) {}
      });
      activeAudioSourcesRef.current = [];
    }
    nextPlaybackTimeRef.current = 0;

    // Close AudioContext
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      const ws = wsRef.current;
      ws.onopen = null;
      ws.onmessage = null;
      ws.onerror = null;
      ws.onclose = null;
      if (ws.readyState === WebSocket.OPEN) {
        ws.close(1000, 'Call cleanup');
      }
      wsRef.current = null;
    }
    setAudioLevel(0);
  }, []);

  // Start Voice Call
  const startCall = useCallback(async () => {
    cleanupAudio();
    setCallState('CONNECTING');
    setErrorMessage(null);
    setTranscript([]);
    setBookingConfirmation(null);
    setLastToolExecution(null);
    setCallDuration(0);
    setIsMuted(false);
    isMutedRef.current = false;

    try {
      // 1. Request microphone permission & capture audio
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      streamRef.current = stream;

      // 2. Set up Web Audio API: 16kHz context for Pipecat/STT compatibility
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioCtx({ sampleRate: 16000 });
      audioContextRef.current = audioCtx;

      // Ensure AudioContext is active (handles browser autoplay policies)
      if (audioCtx.state === 'suspended') {
        await audioCtx.resume();
      }

      const source = audioCtx.createMediaStreamSource(stream);
      sourceRef.current = source;

      // Analyser for real-time visual waveform
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyser.smoothingTimeConstant = 0.5;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Waveform level loop
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateLevel = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        setAudioLevel(Math.min(1.0, avg / 128.0));
        animFrameRef.current = requestAnimationFrame(updateLevel);
      };
      animFrameRef.current = requestAnimationFrame(updateLevel);

      // 3. ScriptProcessorNode for streaming raw 16-bit PCM frames to WebSocket
      const bufferSize = 2048;
      const processor = audioCtx.createScriptProcessor(bufferSize, 1, 1);
      processorRef.current = processor;

      // Zero-gain node to keep processor alive in Web Audio graph without acoustic echo
      const muteGain = audioCtx.createGain();
      muteGain.gain.value = 0;
      muteGainRef.current = muteGain;

      source.connect(processor);
      processor.connect(muteGain);
      muteGain.connect(audioCtx.destination);

      // 4. Request Call Session from Backend
      const sessionData = await api.startCall();
      const newSessionId = sessionData.session_id;
      setSessionId(newSessionId);

      // 5. Connect WebSocket to Voice Pipeline
      const wsUrl = `${WS_BASE}/ws/call/${newSessionId}`;
      const ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';
      wsRef.current = ws;

      // Process PCM audio frames and send to backend
      processor.onaudioprocess = (e) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        if (isMutedRef.current) return;

        const inputData = e.inputBuffer.getChannelData(0);
        // Convert Float32Array [-1.0, 1.0] to 16-bit signed PCM integers
        const pcm16 = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]));
          pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
        }

        try {
          wsRef.current.send(pcm16.buffer);
        } catch (err) {
          // Socket write error handled by ws.onerror
        }
      };

      ws.onopen = () => {
        setCallState('CONNECTED');
        timerIntervalRef.current = setInterval(() => {
          setCallDuration((prev) => prev + 1);
        }, 1000);
      };

      ws.onmessage = async (event) => {
        if (typeof event.data === 'string') {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'CALL_STATE_CHANGED') {
              setCallState(msg.data.state);
              if (thinkingTimeoutRef.current) {
                clearTimeout(thinkingTimeoutRef.current);
                thinkingTimeoutRef.current = null;
              }
              if (msg.data.state === 'THINKING') {
                thinkingTimeoutRef.current = setTimeout(() => {
                  setCallState((curr) => (curr === 'THINKING' ? 'CONNECTED' : curr));
                }, 15000);
              }
              if (msg.data.state === 'LISTENING') {
                // Interruption: cut off any pending assistant audio playback immediately
                if (activeAudioSourcesRef.current) {
                  activeAudioSourcesRef.current.forEach((src) => {
                    try {
                      src.stop();
                      src.disconnect();
                    } catch (e) {}
                  });
                  activeAudioSourcesRef.current = [];
                }
                nextPlaybackTimeRef.current = 0;
              }
            } else if (msg.type === 'PIPELINE_MODE') {
              setPipelineMode(msg.data.mode);
            } else if (msg.type === 'TRANSCRIPT_UPDATE') {
              setTranscript((prev) => {
                const last = prev[prev.length - 1];
                if (last && last.speaker === msg.data.speaker) {
                  if (last.status === 'partial') {
                    return [...prev.slice(0, -1), msg.data];
                  }
                  // Deduplicate consecutive identical messages from the same speaker
                  if (
                    last.message &&
                    msg.data.message &&
                    last.message.trim().toLowerCase() === msg.data.message.trim().toLowerCase()
                  ) {
                    return prev;
                  }
                }
                return [...prev, msg.data];
              });
            } else if (msg.type === 'TOOL_EXECUTED') {
              setLastToolExecution(msg.data);
              if (msg.data.tool === 'book_appointment' && msg.data.result?.success) {
                setBookingConfirmation(msg.data.result);
              }
            } else if (msg.type === 'VOICE_MODE_NOTICE') {
              // Helpful notification when in text fallback mode
              if (msg.data?.message) {
                console.info('Voice pipeline notice:', msg.data.message);
              }
            }
          } catch (e) {
            // Non-json
          }
        } else if (event.data instanceof ArrayBuffer || event.data instanceof Blob) {
          // Received synthesized PCM/WAV audio from ElevenLabs / TTS service
          try {
            const rawBuffer = event.data instanceof Blob
              ? await event.data.arrayBuffer()
              : event.data;

            if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
              const audioCtx = audioContextRef.current;
              if (audioCtx.state === 'suspended') {
                await audioCtx.resume().catch(() => {});
              }

              // Check for 44-byte RIFF/WAV header; strip if present to access raw PCM samples
              let pcmBuffer = rawBuffer;
              if (rawBuffer.byteLength > 44) {
                const headerView = new DataView(rawBuffer);
                // "RIFF" in ASCII is 0x52494646
                if (
                  headerView.getUint8(0) === 0x52 &&
                  headerView.getUint8(1) === 0x49 &&
                  headerView.getUint8(2) === 0x46 &&
                  headerView.getUint8(3) === 0x46
                ) {
                  pcmBuffer = rawBuffer.slice(44);
                }
              }

              const int16Samples = new Int16Array(pcmBuffer);
              if (int16Samples.length > 0) {
                const audioBuffer = audioCtx.createBuffer(1, int16Samples.length, 16000);
                const channelData = audioBuffer.getChannelData(0);
                for (let i = 0; i < int16Samples.length; i++) {
                  channelData[i] = int16Samples[i] / 32768.0;
                }

                const sourceNode = audioCtx.createBufferSource();
                sourceNode.buffer = audioBuffer;
                sourceNode.connect(audioCtx.destination);

                // Schedule seamlessly with existing queue to prevent overlap or gaps
                const currentTime = audioCtx.currentTime;
                const startTime = Math.max(currentTime, nextPlaybackTimeRef.current);
                sourceNode.start(startTime);
                nextPlaybackTimeRef.current = startTime + audioBuffer.duration;

                activeAudioSourcesRef.current.push(sourceNode);
                sourceNode.onended = () => {
                  activeAudioSourcesRef.current = activeAudioSourcesRef.current.filter((s) => s !== sourceNode);
                };
              }
            }
          } catch (e) {
            console.warn('Audio playback error:', e);
          }
        }
      };

      ws.onerror = () => {
        setCallState('ERROR');
        setErrorMessage('Voice connection encountered an error.');
      };

      ws.onclose = () => {
        setCallState('ENDED');
        cleanupAudio();
      };
    } catch (err) {
      cleanupAudio();
      setCallState('ERROR');
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setErrorMessage('Microphone access was denied. Please allow microphone permissions in your browser.');
      } else if (err.name === 'NotFoundError') {
        setErrorMessage('No microphone device found on your system.');
      } else {
        setErrorMessage(err.message || 'Failed to start voice call.');
      }
    }
  }, [cleanupAudio]);

  // Send speech or text command to voice pipeline
  const sendSpokenInput = useCallback((text) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'USER_SPEECH',
          text: text
        })
      );
    }
  }, []);

  // Toggle Mute
  const toggleMute = useCallback(() => {
    const nextMuted = !isMutedRef.current;
    isMutedRef.current = nextMuted;
    setIsMuted(nextMuted);

    if (streamRef.current) {
      streamRef.current.getAudioTracks().forEach((track) => {
        track.enabled = !nextMuted;
      });
    }

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'MUTE', muted: nextMuted }));
    }
  }, []);

  // End Call
  const endCall = useCallback(async () => {
    setCallState('ENDING');
    if (sessionId) {
      try {
        await api.endCall(sessionId);
      } catch (e) {}
    }
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({ type: 'END_CALL' }));
      } catch (e) {}
    }
    cleanupAudio();
    setCallState('ENDED');
  }, [sessionId, cleanupAudio]);

  useEffect(() => {
    return () => cleanupAudio();
  }, [cleanupAudio]);

  return {
    callState,
    sessionId,
    callDuration,
    isMuted,
    transcript,
    audioLevel,
    errorMessage,
    pipelineMode,
    bookingConfirmation,
    lastToolExecution,
    startCall,
    endCall,
    toggleMute,
    sendSpokenInput
  };
}
