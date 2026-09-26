import React, { useState, useEffect } from "react";
import { Pickaxe, Play, Square, Pause, PlayCircle, Coins, Clock, Zap, RefreshCw } from "lucide-react";
import { api } from "../api/client";
import { MineInfo, Account } from "../types";
import { StatusBadge } from "../components/StatusBadge";

interface MineProps {
  account: Account | null;
}

export const Mine: React.FC<MineProps> = ({ account }) => {
  const [mineData, setMineData] = useState<MineInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState("00:00:00");

  const fetchMine = async () => {
    if (!account) return;
    setLoading(true);
    try {
      const res = await api.mine.get(account.id);
      setMineData(res);
      setCountdown(res.countdown || "00:00:00");
    } catch (e) {
      console.error("Error fetching mine", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMine();
  }, [account?.id]);

  // Live seconds countdown ticker
  useEffect(() => {
    if (!mineData?.next_collection_time) return;

    const interval = setInterval(() => {
      const target = new Date(mineData.next_collection_time).getTime();
      const now = new Date().getTime();
      const diff = Math.max(0, Math.floor((target - now) / 1000));

      const h = Math.floor(diff / 3600);
      const m = Math.floor((diff % 3600) / 60);
      const s = diff % 60;
      setCountdown(
        `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`
      );
    }, 1000);

    return () => clearInterval(interval);
  }, [mineData?.next_collection_time]);

  const handleStart = async () => {
    if (!account) return;
    await api.mine.start(account.id);
    await fetchMine();
  };

  const handleStop = async () => {
    if (!account) return;
    await api.mine.stop(account.id);
    await fetchMine();
  };

  const handlePause = async () => {
    if (!account) return;
    await api.mine.pause(account.id);
    await fetchMine();
  };

  const handleResume = async () => {
    if (!account) return;
    await api.mine.resume(account.id);
    await fetchMine();
  };

  const handleCollectNow = async () => {
    if (!account) return;
    try {
      const res = await api.mine.collect(account.id);
      alert(`Successfully collected ${res.gold_collected.toLocaleString()} gold!`);
      await fetchMine();
    } catch (e: any) {
      alert(e.message);
    }
  };

  if (!account) {
    return (
      <div className="card-panel" style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
        Please select an account from the top bar to inspect Mine automation.
      </div>
    );
  }

  const workerStatus = account.mine_worker_status || "STOPPED";

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1>Gold Mine Operations</h1>
          <p className="subtitle">
            Account: <b>{account.name}</b> • Status: <StatusBadge status={workerStatus} />
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={fetchMine} disabled={loading}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Controls */}
      <div className="card-panel" style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginBottom: 20 }}>
        <button
          className="btn btn-success"
          onClick={handleStart}
          disabled={workerStatus === "RUNNING"}
        >
          <Play size={16} /> Start Mine Worker
        </button>
        <button
          className="btn btn-danger"
          onClick={handleStop}
          disabled={workerStatus === "STOPPED"}
        >
          <Square size={16} /> Stop Mine Worker
        </button>
        <button
          className="btn btn-warning"
          onClick={handlePause}
          disabled={workerStatus !== "RUNNING"}
        >
          <Pause size={16} /> Pause
        </button>
        <button
          className="btn btn-primary"
          onClick={handleResume}
          disabled={workerStatus !== "PAUSED"}
        >
          <PlayCircle size={16} /> Resume
        </button>
        <button className="btn btn-secondary" onClick={handleCollectNow} style={{ marginLeft: "auto" }}>
          <Coins size={16} color="var(--warning)" /> Collect Gold Now
        </button>
      </div>

      {/* Countdown Box (Section 42) */}
      <div className="card-panel" style={{ textAlign: "center", padding: 32, marginBottom: 24 }}>
        <div style={{ fontSize: 14, color: "var(--text-muted)", fontWeight: 600, marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>
          Next Collection Countdown
        </div>
        <div className="countdown-box">{countdown}</div>
        <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 12 }}>
          Collection Status: <b>{mineData?.collection_status || "Ready"}</b>
        </div>
      </div>

      {/* Mine Metrics Grid (Section 42) */}
      <div className="grid-cards">
        <div className="stat-card">
          <div className="stat-header">
            <span>Current Gold</span>
            <Coins size={18} color="var(--warning)" />
          </div>
          <div className="stat-value" style={{ color: "var(--warning)" }}>
            {(account.gold || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Player balance</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Collected Today</span>
            <Coins size={18} color="var(--success)" />
          </div>
          <div className="stat-value" style={{ color: "var(--success)" }}>
            +{(mineData?.gold_collected_today || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
            {mineData?.number_of_collections || 0} collections
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Mine Power</span>
            <Zap size={18} color="var(--primary)" />
          </div>
          <div className="stat-value">{mineData?.mine_power || 100} / hr</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Production rate</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Mine Capacity</span>
            <Pickaxe size={18} color="#a855f7" />
          </div>
          <div className="stat-value">{(mineData?.mine_capacity || 50000).toLocaleString()}</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Max accumulator</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Last Collection</span>
            <Clock size={18} color="var(--text-muted)" />
          </div>
          <div className="stat-value" style={{ fontSize: 16 }}>
            {mineData?.last_collection_time && mineData.last_collection_time !== "Never"
              ? new Date(mineData.last_collection_time).toLocaleTimeString()
              : "Never"}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Previous collection</div>
        </div>
      </div>
    </div>
  );
};
