import React, { useState, useEffect } from "react";
import { Scroll, Play, Square, Pause, PlayCircle, Coins, Trophy, RefreshCw } from "lucide-react";
import { api } from "../api/client";
import { QuestInfo, Account } from "../types";
import { StatusBadge } from "../components/StatusBadge";

interface QuestsProps {
  account: Account | null;
  onRefresh?: () => void;
}

export const Quests: React.FC<QuestsProps> = ({ account, onRefresh }) => {
  const [questData, setQuestData] = useState<QuestInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const fetchQuests = async () => {
    if (!account) return;
    setLoading(true);
    try {
      const res = await api.quests.get(account.id);
      setQuestData(res);
    } catch (e) {
      console.error("Error fetching quest info", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuests();
    const interval = setInterval(fetchQuests, 4000);
    return () => clearInterval(interval);
  }, [account?.id]);

  const handleStart = async () => {
    if (!account) return;
    setActionLoading(true);
    try {
      await api.quests.start(account.id);
      setFeedback("Quest worker started! 🚀 Running weakest card with 8s delay.");
      setTimeout(() => setFeedback(null), 4000);
      await fetchQuests();
      onRefresh?.();
    } catch (e: any) {
      alert("Error starting worker: " + (e.message || e));
    } finally {
      setActionLoading(false);
    }
  };

  const handleStop = async () => {
    if (!account) return;
    setActionLoading(true);
    try {
      await api.quests.stop(account.id);
      setFeedback("Quest worker stopped.");
      setTimeout(() => setFeedback(null), 3000);
      await fetchQuests();
      onRefresh?.();
    } catch (e: any) {
      alert("Error stopping worker: " + (e.message || e));
    } finally {
      setActionLoading(false);
    }
  };

  const handlePause = async () => {
    if (!account) return;
    setActionLoading(true);
    try {
      await api.quests.pause(account.id);
      setFeedback("Quest worker paused.");
      setTimeout(() => setFeedback(null), 3000);
      await fetchQuests();
      onRefresh?.();
    } catch (e: any) {
      alert("Error pausing worker: " + (e.message || e));
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    if (!account) return;
    setActionLoading(true);
    try {
      await api.quests.resume(account.id);
      setFeedback("Quest worker resumed.");
      setTimeout(() => setFeedback(null), 3000);
      await fetchQuests();
      onRefresh?.();
    } catch (e: any) {
      alert("Error resuming worker: " + (e.message || e));
    } finally {
      setActionLoading(false);
    }
  };

  const handleExecuteNow = async () => {
    if (!account) return;
    setActionLoading(true);
    try {
      const res = await api.quests.execute(account.id);
      if (res.result === "WAITING_COOLDOWN") {
        alert("⚠️ All 10 weakest cards are cooling down. Please wait a moment.");
      } else {
        alert(`✅ Quest executed! +${res.gold_earned.toLocaleString()} Gold, +${res.xp_earned.toLocaleString()} XP`);
      }
      await fetchQuests();
      onRefresh?.();
    } catch (e: any) {
      alert(e.message || "Quest failed.");
    } finally {
      setActionLoading(false);
    }
  };

  if (!account) {
    return (
      <div className="card-panel" style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
        Please select an account from the top bar to inspect Quests automation.
      </div>
    );
  }

  const workerStatus = questData?.worker_status || account.quest_worker_status || "STOPPED";

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1>Quest Operations</h1>
          <p className="subtitle">
            Account: <b>{account.name}</b> • Status: <StatusBadge status={workerStatus} />
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={fetchQuests} disabled={loading}>
          <RefreshCw size={14} className={loading ? "spin" : ""} /> Refresh
        </button>
      </div>

      {feedback && (
        <div style={{
          background: "rgba(16, 185, 129, 0.15)",
          border: "1px solid var(--success)",
          padding: "10px 16px",
          borderRadius: 8,
          marginBottom: 16,
          color: "var(--success)",
          fontWeight: 500
        }}>
          {feedback}
        </div>
      )}

      {/* Controls */}
      <div className="card-panel" style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginBottom: 20 }}>
        <button
          className="btn btn-success"
          onClick={handleStart}
          disabled={actionLoading || workerStatus === "RUNNING"}
        >
          <Play size={16} /> Start Quest Worker
        </button>
        <button
          className="btn btn-danger"
          onClick={handleStop}
          disabled={actionLoading || workerStatus === "STOPPED"}
        >
          <Square size={16} /> Stop Quest Worker
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
        <button
          className="btn btn-secondary"
          onClick={handleExecuteNow}
          disabled={actionLoading}
          style={{ marginLeft: "auto" }}
        >
          <Scroll size={16} color="var(--primary)" /> Execute Single Quest
        </button>
      </div>

      {/* Quest Metrics */}
      <div className="grid-cards">
        <div className="stat-card">
          <div className="stat-header">
            <span>Quests Completed Today</span>
            <Scroll size={18} color="var(--primary)" />
          </div>
          <div className="stat-value">{questData?.quests_completed_today || 0}</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Daily adventures</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Current Quest</span>
            <Scroll size={18} color="var(--text-muted)" />
          </div>
          <div className="stat-value" style={{ fontSize: 18 }}>
            {questData?.current_quest || "Idle"}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Target quest adventure</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Last Quest Result</span>
            <Trophy size={18} color="var(--success)" />
          </div>
          <div className="stat-value" style={{ fontSize: 18, color: "var(--success)" }}>
            {questData?.last_quest_result || "None"}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Recent outcome</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>Gold Earned</span>
            <Coins size={18} color="var(--warning)" />
          </div>
          <div className="stat-value" style={{ color: "var(--warning)" }}>
            +{(questData?.gold_earned || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>From quests today</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>XP Earned</span>
            <Trophy size={18} color="var(--primary)" />
          </div>
          <div className="stat-value" style={{ color: "var(--primary)" }}>
            +{(questData?.xp_earned || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>From quests today</div>
        </div>
      </div>
    </div>
  );
};
