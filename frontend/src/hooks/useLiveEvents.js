import { useEffect, useRef } from 'react';

const WS_BASE = import.meta.env.VITE_VOICE_SERVER_URL || 'ws://localhost:8000';

export function useLiveEvents(onEvent) {
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    let isMounted = true;

    function connect() {
      try {
        const wsUrl = `${WS_BASE}/ws/events`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
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
            if (onEvent && isMounted) {
              onEvent(payload);
            }
          } catch (e) {
            // Ignore non-json
          }
        };

        ws.onclose = () => {
          if (ws._pingInterval) clearInterval(ws._pingInterval);
          if (isMounted) {
            reconnectTimeoutRef.current = setTimeout(connect, 3000);
          }
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (err) {
        if (isMounted) {
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        }
      }
    }

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        if (wsRef.current._pingInterval) clearInterval(wsRef.current._pingInterval);
        wsRef.current.close();
      }
    };
  }, [onEvent]);
}
