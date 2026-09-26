import React, { useState, useEffect } from "react";
import { Layers, Sparkles, Snowflake, FlaskConical, RefreshCw, AlertTriangle } from "lucide-react";
import { api } from "../api/client";
import { CardItem, Account } from "../types";
import { ConfirmModal } from "../components/ConfirmModal";

interface CardsProps {
  account: Account | null;
}

export const Cards: React.FC<CardsProps> = ({ account }) => {
  const [cards, setCards] = useState<CardItem[]>([]);
  const [loading, setLoading] = useState(false);

  // Modal confirmation state (Section 44)
  const [modalOpen, setModalOpen] = useState(false);
  const [pendingAction, setPendingAction] = useState<{
    type: "evolve" | "cooloff" | "potionize";
    cardId: number;
    cardName: string;
  } | null>(null);

  const fetchCards = async () => {
    if (!account) return;
    setLoading(true);
    try {
      const res = await api.cards.get(account.id);
      setCards(res);
    } catch (e) {
      console.error("Error fetching cards", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCards();
  }, [account?.id]);

  const requestEvolve = (card: CardItem) => {
    setPendingAction({
      type: "evolve",
      cardId: card.id,
      cardName: card.name
    });
    setModalOpen(true);
  };

  const requestCooloff = (card: CardItem) => {
    setPendingAction({
      type: "cooloff",
      cardId: card.id,
      cardName: card.name
    });
    setModalOpen(true);
  };

  const requestPotionize = (card: CardItem) => {
    setPendingAction({
      type: "potionize",
      cardId: card.id,
      cardName: card.name
    });
    setModalOpen(true);
  };

  const handleConfirmAction = async () => {
    if (!account || !pendingAction) return;
    setModalOpen(false);

    try {
      if (pendingAction.type === "evolve") {
        await api.cards.evolve(account.id, [pendingAction.cardId], true);
        alert(`Successfully initiated evolution for ${pendingAction.cardName}!`);
      } else if (pendingAction.type === "cooloff") {
        await api.cards.cooloff(account.id, pendingAction.cardId, true);
        alert(`Successfully cooled off ${pendingAction.cardName}!`);
      } else if (pendingAction.type === "potionize") {
        await api.cards.potionize(account.id, pendingAction.cardId, 1, true);
        alert(`Applied potion to ${pendingAction.cardName}!`);
      }
      await fetchCards();
    } catch (e: any) {
      alert(`Action failed: ${e.message}`);
    } finally {
      setPendingAction(null);
    }
  };

  if (!account) {
    return (
      <div className="card-panel" style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
        Please select an account from the top bar to inspect Cards collection.
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1>Card Management</h1>
          <p className="subtitle">
            Account: <b>{account.name}</b> • Total Cards: {cards.length}
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={fetchCards} disabled={loading}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Cards Table (Section 44) */}
      <div className="card-panel">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Card Name</th>
                <th>Level</th>
                <th>Attack</th>
                <th>Defense</th>
                <th>Rarity</th>
                <th>Potion</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {cards.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: "center", color: "var(--text-muted)", padding: 30 }}>
                    {loading ? "Loading card collection..." : "No cards found for this account."}
                  </td>
                </tr>
              ) : (
                cards.map((c) => (
                  <tr key={c.id}>
                    <td>#{c.id}</td>
                    <td style={{ fontWeight: 600 }}>{c.name}</td>
                    <td>Lv. {c.level}</td>
                    <td style={{ color: "var(--danger)", fontWeight: 600 }}>⚔️ {c.attack.toLocaleString()}</td>
                    <td style={{ color: "var(--primary)", fontWeight: 600 }}>🛡️ {c.defense.toLocaleString()}</td>
                    <td>⭐ {c.rarity}</td>
                    <td>🧪 {c.potion}</td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          background: c.cooldown ? "rgba(245, 158, 11, 0.2)" : "rgba(16, 185, 129, 0.2)",
                          color: c.cooldown ? "var(--warning)" : "var(--success)"
                        }}
                      >
                        {c.status}
                      </span>
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <div style={{ display: "inline-flex", gap: 6 }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => requestPotionize(c)}
                          title="Apply Potion"
                        >
                          <FlaskConical size={13} color="var(--primary)" /> Potion
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => requestCooloff(c)}
                          title="Cool Off Card (Gold)"
                        >
                          <Snowflake size={13} color="#38bdf8" /> Cool Off
                        </button>
                        <button
                          className="btn btn-warning btn-sm"
                          onClick={() => requestEvolve(c)}
                          title="Evolve Card"
                        >
                          <Sparkles size={13} /> Evolve
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

      {/* Confirmation Modal (Section 44) */}
      <ConfirmModal
        isOpen={modalOpen}
        title={
          pendingAction?.type === "evolve"
            ? "Confirm Card Evolution"
            : pendingAction?.type === "cooloff"
            ? "Confirm Cooldown Purchase"
            : "Confirm Potion Application"
        }
        message={
          pendingAction?.type === "evolve"
            ? `Are you sure you want to evolve '${pendingAction?.cardName}'? This action cannot be undone.`
            : pendingAction?.type === "cooloff"
            ? `Are you sure you want to spend gold to cool off '${pendingAction?.cardName}'?`
            : `Are you sure you want to apply a potion to '${pendingAction?.cardName}'?`
        }
        confirmLabel={pendingAction?.type === "evolve" ? "Yes, Evolve Card" : "Yes, Proceed"}
        isDanger={pendingAction?.type === "evolve"}
        onConfirm={handleConfirmAction}
        onCancel={() => {
          setModalOpen(false);
          setPendingAction(null);
        }}
      />
    </div>
  );
};
