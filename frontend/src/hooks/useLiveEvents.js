import { useEffect, useRef } from 'react';

const WS_BASE = import.meta.env.VITE_VOICE_SERVER_URL || 'ws://localhost:8000';

export function useLiveEvents(onEvent) {
  const wsRef = useRef(null);
  const onEventRef = useRef(onEvent);
  const reconnectTimeoutRef = useRef(null);
  const reconnectDelayRef = useRef(1000);
  const isMountedRef = useRef(true);

  // Keep onEvent callback fresh without triggering effect re-run
  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    isMountedRef.current = true;

    function connect() {
      if (!isMountedRef.current) return;

      try {
        const wsUrl = `${WS_BASE}/ws/events`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isMountedRef.current) {
            ws.close(1000, 'Unmounted');
            return;
          }
          // Reset reconnect delay on successful connection
          reconnectDelayRef.current = 1000;

          // Heartbeat ping every 25s
          const pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send('ping');
            }
          }, 25000);
          ws._pingInterval = pingInterval;
        };

        ws.onmessage = (event) => {
          if (event.data === 'pong') return;
          try {
            const payload = JSON.parse(event.data);
            if (onEventRef.current && isMountedRef.current) {
              onEventRef.current(payload);
            }
          } catch (e) {
            // Non-json payload ignored
          }
        };

        ws.onclose = (event) => {
          if (ws._pingInterval) clearInterval(ws._pingInterval);
          wsRef.current = null;

          // Reconnect with exponential backoff if still mounted and not clean manual close
          if (isMountedRef.current && event.code !== 1000) {
            const delay = reconnectDelayRef.current;
            reconnectDelayRef.current = Math.min(delay * 1.5, 15000);
            reconnectTimeoutRef.current = setTimeout(connect, delay);
          }
        };

        ws.onerror = () => {
          // If error occurs while connecting, close cleanly to avoid unhandled state
          if (ws.readyState === WebSocket.OPEN) {
            ws.close();
          }
        };
      } catch (err) {
        if (isMountedRef.current) {
          const delay = reconnectDelayRef.current;
          reconnectDelayRef.current = Math.min(delay * 1.5, 15000);
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        }
      }
    }

    connect();

    return () => {
      isMountedRef.current = false;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      const ws = wsRef.current;
      if (ws) {
        if (ws._pingInterval) clearInterval(ws._pingInterval);
        ws.onopen = null;
        ws.onmessage = null;
        ws.onerror = null;
        ws.onclose = null;
        if (ws.readyState === WebSocket.OPEN) {
          ws.close(1000, 'Component unmounted');
        } else if (ws.readyState === WebSocket.CONNECTING) {
          // Delay close until connection is established to prevent "closed before established" error
          ws.onopen = () => {
            try {
              ws.close(1000, 'Component unmounted');
            } catch (e) {}
          };
        }
        wsRef.current = null;
      }
    };
  }, []); // Run connection lifecycle once on mount
}
