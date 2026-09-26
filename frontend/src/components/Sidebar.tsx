import React from "react";
import {
  LayoutDashboard,
  Users,
  Swords,
  Pickaxe,
  Scroll,
  Layers,
  Trophy,
  Shield,
  Cpu,
  Activity,
  Bell,
  Settings
} from "lucide-react";

export type NavTab =
  | "dashboard"
  | "accounts"
  | "battle"
  | "mine"
  | "quests"
  | "cards"
  | "rankings"
  | "tribe"
  | "workers"
  | "activity"
  | "notifications"
  | "settings";

interface SidebarProps {
  currentTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  unreadAlertsCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onTabChange, unreadAlertsCount = 0 }) => {
  const navItems: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: "dashboard", label: "Dashboard", icon: <LayoutDashboard size={18} /> },
    { id: "accounts", label: "Accounts", icon: <Users size={18} /> },
    { id: "battle", label: "Battle", icon: <Swords size={18} /> },
    { id: "mine", label: "Mine", icon: <Pickaxe size={18} /> },
    { id: "quests", label: "Quests", icon: <Scroll size={18} /> },
    { id: "cards", label: "Cards", icon: <Layers size={18} /> },
    { id: "rankings", label: "Rankings", icon: <Trophy size={18} /> },
    { id: "tribe", label: "Tribe", icon: <Shield size={18} /> },
    { id: "workers", label: "Workers", icon: <Cpu size={18} /> },
    { id: "activity", label: "Activity", icon: <Activity size={18} /> },
    { id: "notifications", label: "Notifications", icon: <Bell size={18} /> },
    { id: "settings", label: "Settings", icon: <Settings size={18} /> }
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <span style={{ fontSize: 22 }}>🍉</span>
        <div>
          <span>FRUITCRAFT</span>
          <div style={{ fontSize: 10, color: "var(--text-muted)" }}>Control Center v1.6</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <div
            key={item.id}
            className={`nav-item ${currentTab === item.id ? "active" : ""}`}
            onClick={() => onTabChange(item.id)}
          >
            {item.icon}
            <span style={{ flex: 1 }}>{item.label}</span>
            {item.id === "notifications" && unreadAlertsCount > 0 && (
              <span
                style={{
                  background: "var(--danger)",
                  color: "#fff",
                  fontSize: 10,
                  fontWeight: 700,
                  padding: "1px 6px",
                  borderRadius: 10
                }}
              >
                {unreadAlertsCount}
              </span>
            )}
          </div>
        ))}
      </nav>
    </aside>
  );
};
