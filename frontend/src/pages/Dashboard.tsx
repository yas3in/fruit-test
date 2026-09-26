import React from "react";
import {
  Users,
  Cpu,
  Swords,
  Coins,
  AlertOctagon,
  BellRing,
  RefreshCw,
  Shield,
  Zap,
  Clock
} from "lucide-react";
import { Account, WorkerInfo, NotificationItem } from "../types";
import { StatusBadge } from "../components/StatusBadge";

interface DashboardProps {
  accounts: Account[];
  workers: WorkerInfo[];
  notifications: NotificationItem[];
  onRefresh: () => void;
  onSelectAccount: (id: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  accounts,
  workers,
  notifications,
  onRefresh,
  onSelectAccount
}) => {
  // Aggregate stats
  const totalAccounts = accounts.length;
  const runningWorkers = workers.filter((w) => w.status === "RUNNING").length;
  const totalGoldToday = accounts.reduce((acc, a) => acc + (a.gold || 0), 0);
  const totalErrors = accounts.filter((a) => a.current_state === "ERROR" || a.last_error).length;
  const criticalAlerts = notifications.filter(
    (n) => n.priority === "CRITICAL" || n.priority === "ERROR"
  ).length;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1>Operations Overview</h1>
          <p className="subtitle">Real-time status monitoring for all FruitCraft accounts and automation workers</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={onRefresh}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Metric Cards (Section 54) */}
      <div className="grid-cards">
        <div className="stat-card">
          <div className="stat-header">
            <span>Accounts</span>
            <Users size={18} color="var(--primary)" />
          </div>
          <div className="stat-value">{totalAccounts}</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
            {accounts.filter((a) => a.is_active).length} Active
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Running Workers</span>
            <Cpu size={18} color="var(--success)" />
          </div>
          <div className="stat-value" style={{ color: "var(--success)" }}>
            {runningWorkers}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Across all accounts
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Battles Today</span>
            <Swords size={18} color="#a855f7" />
          </div>
          <div className="stat-value">
            {workers.find((w) => w.worker === "BattleWorker")?.action_count || 0}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Auto-battles executed</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Gold Balance</span>
            <Coins size={18} color="var(--warning)" />
          </div>
          <div className="stat-value" style={{ color: "var(--warning)" }}>
            {totalGoldToday.toLocaleString()}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Total gold tracked</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>System Errors</span>
            <AlertOctagon size={18} color="var(--danger)" />
          </div>
          <div className="stat-value" style={{ color: totalErrors > 0 ? "var(--danger)" : "var(--text-muted)" }}>
            {totalErrors}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Active errors</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Current Alerts</span>
            <BellRing size={18} color="var(--orange)" />
          </div>
          <div className="stat-value" style={{ color: criticalAlerts > 0 ? "var(--orange)" : "var(--text-muted)" }}>
            {criticalAlerts}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>High priority alerts</div>
        </div>
      </div>

      {/* Account Status Grid (Section 39) */}
      <h2 style={{ marginTop: 8 }}>Real-Time Accounts</h2>
      {accounts.length === 0 ? (
        <div className="card-panel" style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
          No accounts registered yet. Go to <b>Accounts</b> tab to connect your FruitCraft account.
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: 16 }}>
          {accounts.map((acc) => (
            <div
              key={acc.id}
              className="card-panel"
              style={{
                margin: 0,
                borderLeft: `4px solid ${
                  acc.current_state === "RUNNING"
                    ? "var(--success)"
                    : acc.current_state === "ERROR"
                    ? "var(--danger)"
                    : acc.current_state === "CAPTCHA REQUIRED"
                    ? "var(--orange)"
                    : "var(--border)"
                }`
              }}
            >
              {/* Account Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                <div>
                  <h3 style={{ fontSize: 16, color: "var(--text-main)" }}>{acc.name}</h3>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    Player: <b>{acc.player_name || "Unknown"}</b> • Level {acc.level}
                  </div>
                </div>
                <StatusBadge status={acc.current_state} />
              </div>

              {/* Resource Badges */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, background: "var(--bg-secondary)", padding: 12, borderRadius: 8, marginBottom: 14 }}>
                <div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>GOLD</div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: "var(--warning)" }}>
                    🪙 {(acc.gold || 0).toLocaleString()}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>NECTAR / POTION</div>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>
                    🍯 {acc.nectar || 0} • 🧪 {acc.potion || 0}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>POWER (ATK / DEF)</div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>
                    ⚔️ {acc.attack_power.toLocaleString()} • 🛡️ {acc.defense_power.toLocaleString()}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>TRIBE & RANK</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-main)" }}>
                    {acc.tribe_name || "None"} • Rank #{acc.global_rank || "—"}
                  </div>
                </div>
              </div>

              {/* Automation State Details */}
              <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12, color: "var(--text-muted)" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>Workers:</span>
                  <span style={{ fontWeight: 600, color: "var(--text-main)" }}>
                    ⚔️ {acc.battle_worker_status} • ⛏️ {acc.mine_worker_status} • 📜 {acc.quest_worker_status}
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>Last Activity:</span>
                  <span>{acc.last_activity ? new Date(acc.last_activity).toLocaleTimeString() : "Never"}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>Next Action:</span>
                  <span style={{ color: "var(--primary)", fontWeight: 500 }}>
                    {acc.next_action || "Idle"}
                  </span>
                </div>
                {acc.last_error && (
                  <div style={{ color: "var(--danger)", background: "rgba(239, 68, 68, 0.1)", padding: "4px 8px", borderRadius: 4 }}>
                    ⚠️ {acc.last_error}
                  </div>
                )}
                {acc.captcha_status === "REQUIRED" && (
                  <div style={{ color: "var(--orange)", background: "rgba(249, 115, 22, 0.15)", padding: "4px 8px", borderRadius: 4, fontWeight: 700 }}>
                    🚨 CAPTCHA verification required!
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
