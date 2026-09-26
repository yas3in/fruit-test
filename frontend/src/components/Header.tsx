import React from "react";
import { LogOut, UserCheck, ShieldAlert, Wifi } from "lucide-react";
import { Account, HealthStatus } from "../types";
import { useWebSocket } from "../context/WebSocketContext";
import { useAuth } from "../context/AuthContext";

interface HeaderProps {
  accounts: Account[];
  selectedAccountId: string;
  onSelectAccount: (id: string) => void;
  health: HealthStatus | null;
}

export const Header: React.FC<HeaderProps> = ({
  accounts,
  selectedAccountId,
  onSelectAccount,
  health
}) => {
  const { isConnected } = useWebSocket();
  const { logout, username } = useAuth();

  const selectedAcc = accounts.find((a) => a.id === selectedAccountId);

  return (
    <header className="top-header">
      <div className="header-left">
        {/* Account switcher */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <UserCheck size={16} color="var(--primary)" />
          <span style={{ fontSize: 13, color: "var(--text-muted)", fontWeight: 600 }}>Account:</span>
          <select
            value={selectedAccountId}
            onChange={(e) => onSelectAccount(e.target.value)}
            style={{ fontWeight: 600, minWidth: 160 }}
          >
            {accounts.length === 0 && <option value="">No Accounts</option>}
            {accounts.map((acc) => (
              <option key={acc.id} value={acc.id}>
                {acc.name} ({acc.player_name || "New"})
              </option>
            ))}
          </select>
        </div>

        {selectedAcc?.captcha_status === "REQUIRED" && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "rgba(249, 115, 22, 0.2)",
              color: "#f97316",
              padding: "4px 10px",
              borderRadius: 6,
              fontSize: 12,
              fontWeight: 700
            }}
          >
            <ShieldAlert size={14} />
            CAPTCHA REQUIRED
          </div>
        )}
      </div>

      <div className="header-right">
        {/* Live WebSocket Indicator */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 12,
            color: isConnected ? "var(--success)" : "var(--text-muted)",
            background: "var(--bg-card)",
            padding: "4px 10px",
            borderRadius: 6,
            border: "1px solid var(--border)"
          }}
          title={isConnected ? "Real-time updates active" : "Reconnecting to live stream..."}
        >
          <span
            className="live-indicator"
            style={{ background: isConnected ? "#10b981" : "#94a3b8" }}
          />
          <Wifi size={13} />
          <span>{isConnected ? "LIVE" : "OFFLINE"}</span>
        </div>

        {/* System Health */}
        {health && (
          <div
            style={{
              fontSize: 12,
              color: health.status === "HEALTHY" ? "var(--success)" : "var(--warning)",
              background: "var(--bg-card)",
              padding: "4px 10px",
              borderRadius: 6,
              border: "1px solid var(--border)"
            }}
          >
            SYSTEM: {health.status}
          </div>
        )}

        {/* Admin username & logout */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-main)" }}>
            👤 {username}
          </span>
          <button
            className="btn btn-secondary btn-sm"
            onClick={logout}
            title="Log out from admin"
          >
            <LogOut size={13} />
            Exit
          </button>
        </div>
      </div>
    </header>
  );
};
