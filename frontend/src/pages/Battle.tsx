import React, { useState, useEffect } from "react";
import { Swords, Play, Square, Pause, PlayCircle, RefreshCw, Trophy, Skull, Coins, Zap } from "lucide-react";
import { api } from "../api/client";
import { BattleSummary, Account } from "../types";
import { StatusBadge } from "../components/StatusBadge";

interface BattleProps {
  account: Account | null;
}

export const Battle: React.FC<BattleProps> = ({ account }) => {
  const [data, setData] = useState<BattleSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Configuration (Section 41)
  const [strategy, setStrategy] = useState("highest_power");
  const [maxBattles, setMaxBattles] = useState(50);
  const [minGold, setMinGold] = useState(1000);
  const [maxOppDefense, setMaxOppDefense] = useState(100000);
  const [autoHeal, setAutoHeal] = useState(true);
  const [autoCooldown, setAutoCooldown] = useState(true);
  const [delayMin, setDelayMin] = useState(3.0);
  const [delayMax, setDelayMax] = useState(6.0);

  const fetchBattles = async () => {
    if (!account) return;
    setLoading(true);
    try {
      const res = await api.battles.get(account.id);
      setData(res);
    } catch (e) {
      console.error("Error fetching battles", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBattles();
  }, [account?.id]);

  const handleStart = async () => {
    if (!account) return;
    setActionLoading(true);
    try {
      await api.battles.start(account.id, {
        strategy,
        max_battles: Number(maxBattles),
        min_gold: Number(minGold),
        max_opponent_defense: Number(maxOppDefense),
        delay_min: Number(delayMin),
        delay_max: Number(delayMax)
      });
      await fetchBattles();
    } catch (e: any) {
      alert(e.message || "Failed to start battle worker");
    } finally {
      setActionLoading(false);
    }
  };

  const handleStop = async () => {
    if (!account) return;
    setActionLoading(true);
    try {
      await api.battles.stop(account.id);
      await fetchBattles();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handlePause = async () => {
    if (!account) return;
    setActionLoading(true);
    try {
      await api.battles.pause(account.id);
      await fetchBattles();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    if (!account) return;
    setActionLoading(true);
    try {
      await api.battles.resume(account.id);
      await fetchBattles();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setActionLoading(false);
    }
  };

  if (!account) {
    return (
      <div className="card-panel" style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
        Please select an account from the top bar to inspect Battle automation.
      </div>
    );
  }

  const workerStatus = account.battle_worker_status || "STOPPED";

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1>Battle Operations</h1>
          <p className="subtitle">
            Account: <b>{account.name}</b> • Status: <StatusBadge status={workerStatus} />
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={fetchBattles} disabled={loading}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Control Buttons */}
      <div className="card-panel" style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginBottom: 20 }}>
        <button
          className="btn btn-success"
          onClick={handleStart}
          disabled={actionLoading || workerStatus === "RUNNING"}
        >
          <Play size={16} /> Start Auto Battle
        </button>
        <button
          className="btn btn-danger"
          onClick={handleStop}
          disabled={actionLoading || workerStatus === "STOPPED"}
        >
          <Square size={16} /> Stop Auto Battle
        </button>
        <button
          className="btn btn-warning"
          onClick={handlePause}
          disabled={actionLoading || workerStatus !== "RUNNING"}
        >
          <Pause size={16} /> Pause
        </button>
        <button
          className="btn btn-primary"
          onClick={handleResume}
          disabled={actionLoading || workerStatus !== "PAUSED"}
        >
          <PlayCircle size={16} /> Resume
        </button>
      </div>

      {/* Stats Summary (Section 41) */}
      <div className="grid-cards">
        <div className="stat-card">
          <div className="stat-header">
            <span>Battles Today</span>
            <Swords size={18} color="var(--primary)" />
          </div>
          <div className="stat-value">{data?.total_battles_today || 0}</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Wins / Losses</span>
            <Trophy size={18} color="var(--success)" />
          </div>
          <div className="stat-value">
            <span style={{ color: "var(--success)" }}>{data?.wins_today || 0}</span> /{" "}
            <span style={{ color: "var(--danger)" }}>{data?.losses_today || 0}</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Win Rate</span>
            <Zap size={18} color="#a855f7" />
          </div>
          <div className="stat-value" style={{ color: "#a855f7" }}>
            {data?.win_rate_today || 0}%
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Gold Earned</span>
            <Coins size={18} color="var(--warning)" />
          </div>
          <div className="stat-value" style={{ color: "var(--warning)" }}>
            +{(data?.gold_earned_today || 0).toLocaleString()}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>XP Earned</span>
            <Trophy size={18} color="var(--primary)" />
          </div>
          <div className="stat-value" style={{ color: "var(--primary)" }}>
            +{(data?.xp_earned_today || 0).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Battle Configuration (Section 41) */}
      <div className="card-panel">
        <h2>Battle Automation Configuration</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14 }}>
          <div className="form-group">
            <label>Strategy</label>
            <select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
              <option value="highest_power">Highest Attack Deck</option>
              <option value="weakest_defense">Target Lowest Defense</option>
              <option value="gold_farming">Target Highest Gold</option>
            </select>
          </div>

          <div className="form-group">
            <label>Maximum Battles</label>
            <input
              type="number"
              value={maxBattles}
              onChange={(e) => setMaxBattles(Number(e.target.value))}
              min={1}
              max={500}
            />
          </div>

          <div className="form-group">
            <label>Minimum Gold</label>
            <input
              type="number"
              value={minGold}
              onChange={(e) => setMinGold(Number(e.target.value))}
              min={0}
            />
          </div>

          <div className="form-group">
            <label>Max Opponent Defense</label>
            <input
              type="number"
              value={maxOppDefense}
              onChange={(e) => setMaxOppDefense(Number(e.target.value))}
            />
          </div>

          <div className="form-group">
            <label>Delay Range (sec)</label>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <input
                type="number"
                value={delayMin}
                onChange={(e) => setDelayMin(Number(e.target.value))}
                step="0.5"
                min="1"
                style={{ width: 80 }}
              />
              <span>to</span>
              <input
                type="number"
                value={delayMax}
                onChange={(e) => setDelayMax(Number(e.target.value))}
                step="0.5"
                min="2"
                style={{ width: 80 }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Last 20 Battles Table (Section 41) */}
      <div className="card-panel">
        <h2>Last 20 Battles</h2>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Opponent</th>
                <th>Opponent Power</th>
                <th>Result</th>
                <th>Gold</th>
                <th>XP</th>
                <th>Cards</th>
                <th>Duration</th>
              </tr>
            </thead>
            <tbody>
              {!data?.recent_battles || data.recent_battles.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: "center", color: "var(--text-muted)", padding: 24 }}>
                    No battles recorded yet. Start auto-battle to begin.
                  </td>
                </tr>
              ) : (
                data.recent_battles.map((b) => (
                  <tr key={b.id}>
                    <td>{b.time}</td>
                    <td style={{ fontWeight: 600 }}>{b.opponent}</td>
                    <td>🛡️ {b.opponent_power.toLocaleString()}</td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          background: b.result === "WIN" ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                          color: b.result === "WIN" ? "var(--success)" : "var(--danger)"
                        }}
                      >
                        {b.result === "WIN" ? "🏆 WIN" : "💀 LOSS"}
                      </span>
                    </td>
                    <td style={{ color: "var(--warning)", fontWeight: 600 }}>+{b.gold.toLocaleString()}</td>
                    <td style={{ color: "var(--primary)", fontWeight: 600 }}>+{b.xp.toLocaleString()}</td>
                    <td>
                      <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                        {b.cards?.length ? `${b.cards.length} cards` : "—"}
                      </span>
                    </td>
                    <td>{b.duration}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
