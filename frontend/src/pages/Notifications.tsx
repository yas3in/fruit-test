import React, { useState, useEffect } from "react";
import { Bell, RefreshCw, AlertTriangle, AlertCircle, Info, ShieldAlert } from "lucide-react";
import { api } from "../api/client";
import { NotificationItem } from "../types";
import { StatusBadge } from "../components/StatusBadge";

export const Notifications: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [priorityFilter, setPriorityFilter] = useState<string>("");

  const fetchNotifs = async () => {
    setLoading(true);
    try {
      const res = await api.notifications.list(priorityFilter || undefined, 100);
      setNotifications(res);
    } catch (e) {
      console.error("Failed to load notifications", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifs();
  }, [priorityFilter]);

  const getPriorityIcon = (p: string) => {
    switch (p.toUpperCase()) {
      case "CRITICAL":
        return <ShieldAlert size={18} color="var(--danger)" />;
      case "ERROR":
        return <AlertCircle size={18} color="var(--danger)" />;
      case "WARNING":
        return <AlertTriangle size={18} color="var(--warning)" />;
      default:
        return <Info size={18} color="var(--primary)" />;
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1>System Alerts & Notifications</h1>
          <p className="subtitle">Configurable alerts with priority classification and duplicate suppression</p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            style={{ minWidth: 140 }}
          >
            <option value="">All Priorities</option>
            <option value="CRITICAL">Critical</option>
            <option value="ERROR">Error</option>
            <option value="WARNING">Warning</option>
            <option value="INFO">Info</option>
          </select>
          <button className="btn btn-secondary btn-sm" onClick={fetchNotifs} disabled={loading}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      <div className="card-panel">
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {notifications.length === 0 ? (
            <div style={{ textAlign: "center", color: "var(--text-muted)", padding: 40 }}>
              No notifications reported.
            </div>
          ) : (
            notifications.map((n) => (
              <div
                key={n.id}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 14,
                  padding: "14px 16px",
                  background: "var(--bg-secondary)",
                  borderRadius: "var(--radius-sm)",
                  borderLeft: `4px solid ${
                    n.priority === "CRITICAL"
                      ? "var(--danger)"
                      : n.priority === "ERROR"
                      ? "var(--danger)"
                      : n.priority === "WARNING"
                      ? "var(--warning)"
                      : "var(--primary)"
                  }`
                }}
              >
                <div style={{ marginTop: 2 }}>{getPriorityIcon(n.priority)}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span style={{ fontWeight: 700, fontSize: 14, color: "var(--text-main)" }}>
                      {n.title}
                    </span>
                    <StatusBadge status={n.priority} />
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>• {n.account_name}</span>

                    {/* Deduplication Counter (Section 56) */}
                    {n.occurrence_count > 1 && (
                      <span
                        style={{
                          background: "rgba(239, 68, 68, 0.2)",
                          color: "#f87171",
                          fontSize: 11,
                          fontWeight: 700,
                          padding: "1px 8px",
                          borderRadius: 9999
                        }}
                      >
                        {n.occurrence_count}x repeated
                      </span>
                    )}

                    <span style={{ fontSize: 11, color: "var(--text-muted)", marginLeft: "auto" }}>
                      Last: {new Date(n.last_occurrence).toLocaleTimeString()}
                    </span>
                  </div>
                  <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{n.message}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
