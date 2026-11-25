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
  const [bookingConfirmation, setBookingConfirmation] = useState(null);
  const [lastToolExecution, setLastToolExecution] = useState(null);

  const wsRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animFrameRef = useRef(null);
  const timerIntervalRef = useRef(null);

  // Clean audio resources
  const cleanupAudio = useCallback(() => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
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

    try {
      // 1. Get browser microphone stream
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true
        }
      });
      streamRef.current = stream;

      // 2. Set up Web Audio API Analyser for real-time waveform visualization
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyser.smoothingTimeConstant = 0.5;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Monitor audio levels for reactive waveform
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateLevel = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        // Normalize 0.0 to 1.0
        setAudioLevel(Math.min(1.0, avg / 128.0));
        animFrameRef.current = requestAnimationFrame(updateLevel);
      };
      animFrameRef.current = requestAnimationFrame(updateLevel);

      // 3. Request Session from Backend
      const sessionData = await api.startCall();
      const newSessionId = sessionData.session_id;
      setSessionId(newSessionId);

      // 4. Open WebSocket connection to Voice Pipeline
      const wsUrl = `${WS_BASE}/ws/call/${newSessionId}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setCallState('CONNECTED');
        // Start duration timer
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
            } else if (msg.type === 'TRANSCRIPT_UPDATE') {
              setTranscript((prev) => {
                // Check if last message is from same speaker and was partial
                const last = prev[prev.length - 1];
                if (last && last.speaker === msg.data.speaker && last.status === 'partial') {
                  return [...prev.slice(0, -1), msg.data];
                }
                return [...prev, msg.data];
              });
            } else if (msg.type === 'TOOL_EXECUTED') {
              setLastToolExecution(msg.data);
              if (msg.data.tool === 'book_appointment' && msg.data.result?.success) {
                setBookingConfirmation(msg.data.result);
              }
            }
          } catch (e) {
            // Non-json
          }
        } else if (event.data instanceof Blob) {
          // Received synthesized audio WAV from server; play through Audio
          const audioUrl = URL.createObjectURL(event.data);
          const audio = new Audio(audioUrl);
          audio.play().catch(() => {});
        }
      };

      ws.onerror = (err) => {
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
    if (streamRef.current) {
      const audioTracks = streamRef.current.getAudioTracks();
      if (audioTracks.length > 0) {
        const nextMuted = !isMuted;
        audioTracks[0].enabled = !nextMuted;
        setIsMuted(nextMuted);
      }
    }
  }, [isMuted]);

  // End Call
  const endCall = useCallback(async () => {
    setCallState('ENDING');
    if (sessionId) {
      try {
        await api.endCall(sessionId);
      } catch (e) {}
    }
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'END_CALL' }));
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
    bookingConfirmation,
    lastToolExecution,
    startCall,
    endCall,
    toggleMute,
    sendSpokenInput
  };
}
