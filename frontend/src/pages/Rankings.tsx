import React from "react";
import { Trophy, Award } from "lucide-react";
import { Account } from "../types";

interface RankingsProps {
  account: Account | null;
}

export const Rankings: React.FC<RankingsProps> = ({ account }) => {
  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h1>Rankings & Leagues</h1>
        <p className="subtitle">FruitCraft global standings and league rankings</p>
      </div>

      <div className="grid-cards">
        <div className="stat-card">
          <div className="stat-header">
            <span>Global Rank</span>
            <Trophy size={18} color="var(--warning)" />
          </div>
          <div className="stat-value">
            #{account?.global_rank ? account.global_rank.toLocaleString() : "—"}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Current global leaderboard</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>League Rank</span>
            <Award size={18} color="var(--primary)" />
          </div>
          <div className="stat-value">
            #{account?.league_rank ? account.league_rank.toLocaleString() : "—"}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Current league division</div>
        </div>
      </div>

      <div className="card-panel">
        <h2>Rank Progression Overview</h2>
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>
          Rankings are automatically synchronized when player statistics are refreshed or battles conclude.
        </p>
      </div>
    </div>
  );
};
