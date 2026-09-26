import React from "react";

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const s = (status || "").toUpperCase();

  if (s === "READY") {
    return <span className="badge badge-ready">🟢 READY</span>;
  }
  if (s === "RUNNING") {
    return <span className="badge badge-running">🟢 RUNNING</span>;
  }
  if (s === "WAITING" || s === "PAUSED") {
    return <span className="badge badge-waiting">🟡 {s}</span>;
  }
  if (s === "ERROR") {
    return <span className="badge badge-error">🔴 ERROR</span>;
  }
  if (s === "CAPTCHA REQUIRED" || s === "CAPTCHA_REQUIRED") {
    return <span className="badge badge-captcha">🟠 CAPTCHA REQUIRED</span>;
  }
  if (s === "CRITICAL") {
    return <span className="badge badge-critical">🚨 CRITICAL</span>;
  }
  if (s === "WARNING") {
    return <span className="badge badge-warning">⚠️ WARNING</span>;
  }
  if (s === "INFO") {
    return <span className="badge badge-info">ℹ️ INFO</span>;
  }

  return <span className="badge badge-stopped">⚪ {status || "STOPPED"}</span>;
};
