import React from "react";
import { Shield, Users, Coins } from "lucide-react";
import { Account } from "../types";

interface TribeProps {
  account: Account | null;
}

export const Tribe: React.FC<TribeProps> = ({ account }) => {
  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h1>Tribe Operations</h1>
        <p className="subtitle">Tribe membership and coordination</p>
      </div>

      <div className="grid-cards">
        <div className="stat-card">
          <div className="stat-header">
            <span>Tribe Name</span>
            <Shield size={18} color="var(--primary)" />
          </div>
          <div className="stat-value" style={{ fontSize: 20 }}>
            {account?.tribe_name || "No Tribe"}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
            ID: {account?.id ? "Connected" : "None"}
          </div>
        </div>
      </div>

      <div className="card-panel">
        <h2>Tribe Details</h2>
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>
          Tribe status and contributions are tracked through FruitCraft player updates.
        </p>
      </div>
    </div>
  );
};
