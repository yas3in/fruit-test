import React, { createContext, useContext, useEffect, useState, useRef } from "react";
import { ActivityEvent } from "../types";
import { useAuth } from "./AuthContext";

interface WebSocketContextType {
  isConnected: boolean;
  lastEvent: ActivityEvent | null;
  recentEvents: ActivityEvent[];
}

const WebSocketContext = createContext<WebSocketContextType>({
  isConnected: false,
  lastEvent: null,
  recentEvents: []
});

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<ActivityEvent | null>(null);
  const [recentEvents, setRecentEvents] = useState<ActivityEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  useEffect(() => {
    if (!isAuthenticated || !token) {
      if (wsRef.current) {
        wsRef.current.close();
      }
      setIsConnected(false);
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/dashboard?token=${encodeURIComponent(token)}`;

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data: ActivityEvent = JSON.parse(event.data);
            setLastEvent(data);
            setRecentEvents((prev) => [data, ...prev.slice(0, 49)]);
          } catch (e) {
            console.error("Error parsing WS event", e);
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          // Try reconnecting after 3 seconds
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (err) {
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      }
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [token, isAuthenticated]);

  return (
    <WebSocketContext.Provider value={{ isConnected, lastEvent, recentEvents }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext);
