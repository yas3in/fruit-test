import React, { useState, useEffect } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { WebSocketProvider, useWebSocket } from "./context/WebSocketContext";
import { Sidebar, NavTab } from "./components/Sidebar";
import { Header } from "./components/Header";
import { Dashboard } from "./pages/Dashboard";
import { Accounts } from "./pages/Accounts";
import { Battle } from "./pages/Battle";
import { Mine } from "./pages/Mine";
import { Quests } from "./pages/Quests";
import { Cards } from "./pages/Cards";
import { Rankings } from "./pages/Rankings";
import { Tribe } from "./pages/Tribe";
import { Workers } from "./pages/Workers";
import { Activity } from "./pages/Activity";
import { Notifications } from "./pages/Notifications";
import { Settings } from "./pages/Settings";
import { Login } from "./pages/Login";
import { api } from "./api/client";
import { Account, WorkerInfo, NotificationItem, HealthStatus } from "./types";

const MainApp: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { lastEvent } = useWebSocket();

  const [currentTab, setCurrentTab] = useState<NavTab>("dashboard");
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string>("");
  const [workers, setWorkers] = useState<WorkerInfo[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  const fetchInitialData = async () => {
    if (!isAuthenticated) return;
    try {
      const [accs, wrks, notifs, hlth] = await Promise.all([
        api.accounts.list(),
        api.workers.getAll(),
        api.notifications.list(undefined, 20),
        api.health.get()
      ]);

      setAccounts(accs);
      setWorkers(wrks);
      setNotifications(notifs);
      setHealth(hlth);

      if (accs.length > 0 && !selectedAccountId) {
        setSelectedAccountId(accs[0].id);
      }
    } catch (e) {
      console.error("Failed to load initial dashboard data", e);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, [isAuthenticated]);

  // Real-time reactive updates from WebSocket (Section 51)
  useEffect(() => {
    if (!lastEvent) return;

    // Reactively refresh workers if worker status changed
    if (lastEvent.event_type === "WORKER_STATUS") {
      api.workers.getAll().then(setWorkers).catch(console.error);
      api.accounts.list().then(setAccounts).catch(console.error);
    } else if (
      lastEvent.event_type === "BATTLE_FINISHED" ||
      lastEvent.event_type === "GOLD_COLLECTED" ||
      lastEvent.event_type === "QUEST_FINISHED" ||
      lastEvent.event_type === "PLAYER_SYNC"
    ) {
      api.accounts.list().then(setAccounts).catch(console.error);
      api.notifications.list(undefined, 20).then(setNotifications).catch(console.error);
    } else if (lastEvent.event_type === "HEALTH_STATUS" && lastEvent.metadata) {
      setHealth(lastEvent.metadata as HealthStatus);
    }
  }, [lastEvent]);

  if (!isAuthenticated) {
    return <Login />;
  }

  const selectedAccount = accounts.find((a) => a.id === selectedAccountId) || accounts[0] || null;
  const unreadAlerts = notifications.filter(
    (n) => (n.priority === "CRITICAL" || n.priority === "ERROR") && !n.is_read
  ).length;

  return (
    <div className="app-container">
      <Sidebar
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        unreadAlertsCount={unreadAlerts}
      />

      <div className="main-content">
        <Header
          accounts={accounts}
          selectedAccountId={selectedAccountId}
          onSelectAccount={setSelectedAccountId}
          health={health}
        />

        <main className="content-body">
          {currentTab === "dashboard" && (
            <Dashboard
              accounts={accounts}
              workers={workers}
              notifications={notifications}
              onRefresh={fetchInitialData}
              onSelectAccount={(id) => {
                setSelectedAccountId(id);
                setCurrentTab("accounts");
              }}
            />
          )}

          {currentTab === "accounts" && (
            <Accounts accounts={accounts} onRefresh={fetchInitialData} />
          )}

          {currentTab === "battle" && <Battle account={selectedAccount} onRefresh={fetchInitialData} />}

          {currentTab === "mine" && <Mine account={selectedAccount} onRefresh={fetchInitialData} />}

          {currentTab === "quests" && <Quests account={selectedAccount} onRefresh={fetchInitialData} />}

          {currentTab === "cards" && <Cards account={selectedAccount} />}

          {currentTab === "rankings" && <Rankings account={selectedAccount} />}

          {currentTab === "tribe" && <Tribe account={selectedAccount} />}

          {currentTab === "workers" && (
            <Workers workers={workers} onRefresh={fetchInitialData} />
          )}

          {currentTab === "activity" && <Activity />}

          {currentTab === "notifications" && <Notifications />}

          {currentTab === "settings" && <Settings />}
        </main>
      </div>
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <WebSocketProvider>
        <MainApp />
      </WebSocketProvider>
    </AuthProvider>
  );
}
