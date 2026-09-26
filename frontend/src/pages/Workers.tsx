import React from "react";
import { Cpu, Play, Square, Pause, PlayCircle, RotateCw, RefreshCw } from "lucide-react";
import { api } from "../api/client";
import { WorkerInfo } from "../types";
import { StatusBadge } from "../components/StatusBadge";

interface WorkersProps {
  workers: WorkerInfo[];
  onRefresh: () => void;
}

export const Workers: React.FC<WorkersProps> = ({ workers, onRefresh }) => {
  const handleControl = async (w: WorkerInfo, action: string) => {
    try {
      await api.workers.control(w.account_id, w.worker, action);
      onRefresh();
    } catch (e: any) {
      alert(`Worker control failed: ${e.message}`);
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1>Worker Control Center</h1>
          <p className="subtitle">Real-time automation worker management across all accounts</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={onRefresh}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="card-panel">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Worker</th>
                <th>Account</th>
                <th>Status</th>
                <th>Started At</th>
                <th>Last Action</th>
                <th>Next Action</th>
                <th>Last Error</th>
                <th style={{ textAlign: "right" }}>Controls</th>
              </tr>
            </thead>
            <tbody>
              {workers.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: "center", color: "var(--text-muted)", padding: 30 }}>
                    No workers currently active.
                  </td>
                </tr>
              ) : (
                workers.map((w, idx) => (
                  <tr key={`${w.account_id}-${w.worker}-${idx}`}>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 600 }}>
                        <Cpu size={16} color="var(--primary)" />
                        <span>{w.worker}</span>
                      </div>
                    </td>
                    <td>
                      <b>{w.account}</b>
                      <div style={{ fontSize: 11, color: "var(--text-muted)" }}>ID: {w.account_id}</div>
                    </td>
                    <td>
                      <StatusBadge status={w.status} />
                    </td>
                    <td>
                      <span style={{ fontSize: 12 }}>
                        {w.started_at ? new Date(w.started_at).toLocaleTimeString() : "—"}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: 12, color: "var(--text-main)" }}>
                        {w.last_action || "None"}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: 12, color: "var(--primary)" }}>
                        {w.next_action || "Idle"}
                      </span>
                    </td>
                    <td>
                      {w.last_error ? (
                        <span style={{ color: "var(--danger)", fontSize: 12 }}>⚠️ {w.last_error}</span>
                      ) : (
                        <span style={{ color: "var(--text-muted)", fontSize: 12 }}>None</span>
                      )}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <div style={{ display: "inline-flex", gap: 4 }}>
                        <button
                          className="btn btn-success btn-sm"
                          onClick={() => handleControl(w, "start")}
                          disabled={w.status === "RUNNING"}
                          title="Start Worker"
                        >
                          <Play size={12} />
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleControl(w, "stop")}
                          disabled={w.status === "STOPPED"}
                          title="Stop Worker"
                        >
                          <Square size={12} />
                        </button>
                        <button
                          className="btn btn-warning btn-sm"
                          onClick={() => handleControl(w, "pause")}
                          disabled={w.status !== "RUNNING"}
                          title="Pause Worker"
                        >
                          <Pause size={12} />
                        </button>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => handleControl(w, "resume")}
                          disabled={w.status !== "PAUSED"}
                          title="Resume Worker"
                        >
                          <PlayCircle size={12} />
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleControl(w, "restart")}
                          title="Restart Worker"
                        >
                          <RotateCw size={12} />
                        </button>
                      </div>
                    </td>
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
