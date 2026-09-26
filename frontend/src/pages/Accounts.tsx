import React, { useState } from "react";
import { Users, UserPlus, Trash2, Power, Play, Square, RefreshCw, KeyRound, AlertCircle } from "lucide-react";
import { api } from "../api/client";
import { Account } from "../types";
import { StatusBadge } from "../components/StatusBadge";
import { ConfirmModal } from "../components/ConfirmModal";

interface AccountsProps {
  accounts: Account[];
  onRefresh: () => void;
}

export const Accounts: React.FC<AccountsProps> = ({ accounts, onRefresh }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [restoreKey, setRestoreKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Delete modal state
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const handleAddAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await api.accounts.create(name, restoreKey);
      setName("");
      setRestoreKey("");
      setModalOpen(false);
      onRefresh();
    } catch (err: any) {
      setError(err.message || "Failed to add account");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleEnable = async (acc: Account) => {
    try {
      await api.accounts.update(acc.id, { is_active: !acc.is_active });
      onRefresh();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleSync = async (acc: Account) => {
    try {
      await api.accounts.sync(acc.id);
      alert(`Account ${acc.name} synced!`);
      onRefresh();
    } catch (err: any) {
      alert(`Sync failed: ${err.message}`);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteId) return;
    try {
      await api.accounts.delete(deleteId);
      setDeleteId(null);
      onRefresh();
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1>Account Management</h1>
          <p className="subtitle">Configure and monitor FruitCraft automation accounts</p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn btn-secondary btn-sm" onClick={onRefresh}>
            <RefreshCw size={14} /> Refresh
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => setModalOpen(true)}>
            <UserPlus size={14} /> Add Account
          </button>
        </div>
      </div>

      {/* Accounts Table (Section 45) */}
      <div className="card-panel">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Account</th>
                <th>Player</th>
                <th>Restore Key</th>
                <th>Status</th>
                <th>Workers</th>
                <th>Last Login</th>
                <th>Last Error</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {accounts.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: "center", color: "var(--text-muted)", padding: 30 }}>
                    No accounts added. Click "Add Account" to get started.
                  </td>
                </tr>
              ) : (
                accounts.map((acc) => (
                  <tr key={acc.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{acc.name}</div>
                      <span style={{ fontSize: 11, color: "var(--text-muted)" }}>ID: {acc.id}</span>
                    </td>
                    <td>
                      <div><b>{acc.player_name || "Not loaded"}</b></div>
                      <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Lv. {acc.level} • {acc.tribe_name || "No tribe"}</span>
                    </td>
                    <td>
                      {/* NEVER display raw keys in UI - Section 45 */}
                      <code style={{ background: "var(--bg-secondary)", padding: "3px 6px", borderRadius: 4, fontSize: 11 }}>
                        {acc.masked_restore_key}
                      </code>
                    </td>
                    <td>
                      <StatusBadge status={acc.current_state} />
                    </td>
                    <td>
                      <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                        ⚔️ {acc.battle_worker_status} • ⛏️ {acc.mine_worker_status} • 📜 {acc.quest_worker_status}
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: 12 }}>
                        {acc.last_login ? new Date(acc.last_login).toLocaleString() : "Never"}
                      </span>
                    </td>
                    <td>
                      {acc.last_error ? (
                        <span style={{ color: "var(--danger)", fontSize: 11 }} title={acc.last_error}>
                          ⚠️ {acc.last_error.slice(0, 30)}...
                        </span>
                      ) : (
                        <span style={{ color: "var(--text-muted)", fontSize: 11 }}>None</span>
                      )}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <div style={{ display: "inline-flex", gap: 6 }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleSync(acc)}
                          title="Sync Player Data"
                        >
                          <RefreshCw size={12} /> Sync
                        </button>
                        <button
                          className={`btn btn-sm ${acc.is_active ? "btn-warning" : "btn-success"}`}
                          onClick={() => handleToggleEnable(acc)}
                          title={acc.is_active ? "Disable Account" : "Enable Account"}
                        >
                          <Power size={12} /> {acc.is_active ? "Disable" : "Enable"}
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => setDeleteId(acc.id)}
                          title="Remove Account"
                        >
                          <Trash2 size={12} />
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

      {/* Add Account Modal */}
      {modalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Add FruitCraft Account</h3>
              <button
                onClick={() => setModalOpen(false)}
                style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            {error && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  background: "rgba(239, 68, 68, 0.15)",
                  color: "#ef4444",
                  padding: "10px 14px",
                  borderRadius: 6,
                  fontSize: 12,
                  marginBottom: 14
                }}
              >
                <AlertCircle size={14} />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleAddAccount}>
              <div className="form-group">
                <label>Account Label / Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. My Main Account"
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: 20 }}>
                <label>FruitCraft Restore Key</label>
                <input
                  type="text"
                  value={restoreKey}
                  onChange={(e) => setRestoreKey(e.target.value)}
                  placeholder="e.g. head9229burst65"
                  required
                />
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  Your restore key is saved securely and will never be exposed in API responses.
                </span>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setModalOpen(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? "Adding..." : "Add & Connect"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      <ConfirmModal
        isOpen={!!deleteId}
        title="Remove Account"
        message="Are you sure you want to remove this account? All associated battle records and automation workers will be stopped."
        confirmLabel="Remove Account"
        isDanger={true}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
};
