import React, { useState, useEffect } from "react";
import { Settings as SettingsIcon, Save, Send, ShieldCheck, CheckCircle2 } from "lucide-react";
import { api } from "../api/client";
import { SystemSettings } from "../types";

export const Settings: React.FC = () => {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    const fetchSettings = async () => {
      setLoading(true);
      try {
        const res = await api.settings.get();
        setSettings(res);
      } catch (e) {
        console.error("Failed to load settings", e);
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!settings) return;
    setSaving(true);
    setSavedSuccess(false);

    try {
      await api.settings.update(settings);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (e: any) {
      alert(`Save failed: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  if (!settings) {
    return (
      <div className="card-panel" style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
        {loading ? "Loading system settings..." : "Settings unavailable."}
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1>System Settings</h1>
          <p className="subtitle">Configure automation defaults, network proxy (port 10501), and Telegram notifications</p>
        </div>
      </div>

      <form onSubmit={handleSave}>
        {savedSuccess && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              background: "rgba(16, 185, 129, 0.15)",
              color: "#10b981",
              padding: "12px 16px",
              borderRadius: 8,
              fontSize: 13,
              marginBottom: 16
            }}
          >
            <CheckCircle2 size={16} />
            <span>Settings successfully saved and applied!</span>
          </div>
        )}

        {/* Network & Proxy Configuration (Port 10501) */}
        <div className="card-panel">
          <h2>Network & Connection (Port 10501)</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
            <div className="form-group">
              <label>Proxy Port</label>
              <input
                type="number"
                value={settings.proxy_port}
                onChange={(e) => setSettings({ ...settings, proxy_port: Number(e.target.value) })}
              />
              <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Default connection port: 10501</span>
            </div>

            <div className="form-group">
              <label>Proxy URL</label>
              <input
                type="text"
                value={settings.proxy_url}
                onChange={(e) => setSettings({ ...settings, proxy_url: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Enable Proxy</label>
              <select
                value={settings.proxy_enabled ? "true" : "false"}
                onChange={(e) => setSettings({ ...settings, proxy_enabled: e.target.value === "true" })}
              >
                <option value="true">Enabled (Use Port 10501)</option>
                <option value="false">Disabled (Direct Connection)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Automation Defaults (Section 58) */}
        <div className="card-panel">
          <h2>Automation Defaults</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
            <div className="form-group">
              <label>Battle Delay Min (sec)</label>
              <input
                type="number"
                step="0.5"
                value={settings.battle_delay_min}
                onChange={(e) => setSettings({ ...settings, battle_delay_min: Number(e.target.value) })}
              />
            </div>

            <div className="form-group">
              <label>Battle Delay Max (sec)</label>
              <input
                type="number"
                step="0.5"
                value={settings.battle_delay_max}
                onChange={(e) => setSettings({ ...settings, battle_delay_max: Number(e.target.value) })}
              />
            </div>

            <div className="form-group">
              <label>Mine Interval (minutes)</label>
              <input
                type="number"
                value={settings.mine_delay_minutes}
                onChange={(e) => setSettings({ ...settings, mine_delay_minutes: Number(e.target.value) })}
              />
            </div>

            <div className="form-group">
              <label>Quest Delay Min (sec)</label>
              <input
                type="number"
                step="0.5"
                value={settings.quest_delay_min}
                onChange={(e) => setSettings({ ...settings, quest_delay_min: Number(e.target.value) })}
              />
            </div>

            <div className="form-group">
              <label>Quest Delay Max (sec)</label>
              <input
                type="number"
                step="0.5"
                value={settings.quest_delay_max}
                onChange={(e) => setSettings({ ...settings, quest_delay_max: Number(e.target.value) })}
              />
            </div>
          </div>
        </div>

        {/* Worker Policy & Telegram Settings */}
        <div className="card-panel">
          <h2>Worker Restart Policy & Telegram Notifications</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
            <div className="form-group">
              <label>Worker Auto-Restart Policy</label>
              <select
                value={settings.auto_restart_workers ? "true" : "false"}
                onChange={(e) => setSettings({ ...settings, auto_restart_workers: e.target.value === "true" })}
              >
                <option value="true">Auto-Restart Enabled (AUTO_RESTART_WORKERS=true)</option>
                <option value="false">Disabled (Stop on Crash)</option>
              </select>
            </div>

            <div className="form-group">
              <label>Telegram Notifications</label>
              <select
                value={settings.telegram_enabled ? "true" : "false"}
                onChange={(e) => setSettings({ ...settings, telegram_enabled: e.target.value === "true" })}
              >
                <option value="true">Enabled</option>
                <option value="false">Disabled</option>
              </select>
            </div>

            <div className="form-group">
              <label>Telegram Chat ID</label>
              <input
                type="text"
                value={settings.telegram_chat_id || ""}
                onChange={(e) => setSettings({ ...settings, telegram_chat_id: e.target.value })}
                placeholder="e.g. 123456789"
              />
            </div>

            <div className="form-group">
              <label>Bot Token Status</label>
              <div style={{ display: "flex", alignItems: "center", gap: 8, height: 38 }}>
                {settings.has_telegram_token ? (
                  <span style={{ color: "var(--success)", fontSize: 13, fontWeight: 600 }}>
                    <ShieldCheck size={16} style={{ verticalAlign: "middle", marginRight: 4 }} />
                    Configured securely in environment
                  </span>
                ) : (
                  <span style={{ color: "var(--text-muted)", fontSize: 13 }}>
                    Not set (set TELEGRAM_BOT_TOKEN in .env)
                  </span>
                )}
              </div>
            </div>

            <div className="form-group">
              <label>Timezone</label>
              <input
                type="text"
                value={settings.timezone}
                onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Daily Report Schedule Time</label>
              <input
                type="text"
                value={settings.daily_report_time}
                onChange={(e) => setSettings({ ...settings, daily_report_time: e.target.value })}
                placeholder="00:00"
              />
            </div>
          </div>
        </div>

        <button type="submit" className="btn btn-primary" style={{ padding: "10px 24px" }} disabled={saving}>
          <Save size={16} /> {saving ? "Saving Changes..." : "Save Settings"}
        </button>
      </form>
    </div>
  );
};
