import React, { useState, useEffect } from "react";
import { Activity as ActivityIcon, RefreshCw, Zap } from "lucide-react";
import { api } from "../api/client";
import { ActivityEvent } from "../types";
import { useWebSocket } from "../context/WebSocketContext";

export const Activity: React.FC = () => {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const { recentEvents } = useWebSocket();

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const res = await api.events.list(undefined, 100);
      setEvents(res);
    } catch (e) {
      console.error("Failed to load activity logs", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  // Merge live WS events with historical events
  const combined = [...recentEvents, ...events].filter(
    (item, index, self) =>
      index === self.findIndex((t) => t.timestamp === item.timestamp && t.message === item.message)
  );

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1>Real-Time Activity Feed</h1>
          <p className="subtitle">Live stream of automation events, battle outcomes, and system updates</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={fetchEvents} disabled={loading}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="card-panel">
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {combined.length === 0 ? (
            <div style={{ textAlign: "center", color: "var(--text-muted)", padding: 40 }}>
              No activities logged yet.
            </div>
          ) : (
            combined.map((ev, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 14,
                  padding: "12px 14px",
                  background: "var(--bg-secondary)",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--border)"
                }}
              >
                <div style={{ marginTop: 2 }}>
                  <ActivityIcon size={16} color="var(--primary)" />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span
                      style={{
                        fontSize: 11,
                        fontWeight: 700,
                        background: "rgba(56, 189, 248, 0.15)",
                        color: "var(--primary)",
                        padding: "2px 6px",
                        borderRadius: 4
                      }}
                    >
                      {ev.event_type}
                    </span>
                    <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-main)" }}>
                      {ev.account_name || "System"}
                    </span>
                    <span style={{ fontSize: 11, color: "var(--text-muted)", marginLeft: "auto" }}>
                      {new Date(ev.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div style={{ fontSize: 13, color: "var(--text-main)" }}>{ev.message}</div>
                  {ev.metadata && Object.keys(ev.metadata).length > 0 && (
                    <pre
                      style={{
                        marginTop: 6,
                        background: "var(--bg-primary)",
                        padding: "6px 10px",
                        borderRadius: 4,
                        fontSize: 11,
                        color: "var(--text-muted)",
                        overflowX: "auto"
                      }}
                    >
                      {JSON.stringify(ev.metadata, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
