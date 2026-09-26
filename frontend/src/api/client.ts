import {
  Account,
  WorkerInfo,
  BattleSummary,
  MineInfo,
  QuestInfo,
  CardItem,
  ActivityEvent,
  NotificationItem,
  SystemSettings,
  HealthStatus
} from "../types";

const API_BASE = "";

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem("fc_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    "Content-Type": "application/json",
    ...getAuthHeader(),
    ...(options.headers || {})
  };

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    localStorage.removeItem("fc_token");
    window.dispatchEvent(new Event("auth-expired"));
    throw new Error("Authentication session expired.");
  }

  if (!response.ok) {
    let errMsg = `Request failed: ${response.status} ${response.statusText}`;
    try {
      const errData = await response.json();
      errMsg = errData.detail || errMsg;
    } catch (_) {}
    throw new Error(errMsg);
  }

  return response.json();
}

export const api = {
  auth: {
    login: (username: string, password: string) =>
      request<{ access_token: string; username: string }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password })
      }),
    me: () => request<{ username: string; role: string }>("/api/auth/me")
  },
  accounts: {
    list: () => request<Account[]>("/api/accounts"),
    get: (id: string) => request<Account>(`/api/accounts/${id}`),
    create: (name: string, restore_key: string) =>
      request<Account>("/api/accounts", {
        method: "POST",
        body: JSON.stringify({ name, restore_key })
      }),
    update: (id: string, data: Partial<Account>) =>
      request<Account>(`/api/accounts/${id}`, {
        method: "PUT",
        body: JSON.stringify(data)
      }),
    delete: (id: string) =>
      request<{ message: string }>(`/api/accounts/${id}`, {
        method: "DELETE"
      }),
    sync: (id: string) =>
      request<Account>(`/api/accounts/${id}/sync`, {
        method: "POST"
      })
  },
  battles: {
    get: (accountId: string) =>
      request<BattleSummary>(`/api/accounts/${accountId}/battles`),
    start: (accountId: string, config?: any) =>
      request<WorkerInfo>(`/api/accounts/${accountId}/workers/battle/start`, {
        method: "POST",
        body: JSON.stringify(config || {})
      }),
    stop: (accountId: string) =>
      request<WorkerInfo>(`/api/accounts/${accountId}/workers/battle/stop`, {
        method: "POST"
      }),
    pause: (accountId: string) =>
      request<WorkerInfo>(`/api/accounts/${accountId}/workers/battle/pause`, {
        method: "POST"
      }),
    resume: (accountId: string) =>
      request<WorkerInfo>(`/api/accounts/${accountId}/workers/battle/resume`, {
        method: "POST"
      })
  },
  mine: {
    get: (accountId: string) =>
      request<MineInfo>(`/api/accounts/${accountId}/mine`),
    collect: (accountId: string) =>
      request<{ status: string; gold_collected: number }>(`/api/accounts/${accountId}/mine/collect`, {
        method: "POST"
      }),
    start: (accountId: string, config?: any) =>
      request<WorkerInfo>(`/api/accounts/${accountId}/workers/mine/start`, {
        method: "POST",
        body: JSON.stringify(config || {})
      }),
    stop: (accountId: string) =>
      request<WorkerInfo>(`/api/accounts/${accountId}/workers/mine/stop`, {
        method: "POST"
      }),
    pause: (accountId: string) =>
      request<WorkerInfo>(`/api/accounts/${accountId}/workers/mine/pause`, {
        method: "POST"
      }),
    resume: (accountId: string) =>
      request<WorkerInfo>(`/api/accounts/${accountId}/workers/mine/resume`, {
        method: "POST"
      })
  },
  quests: {
    get: (accountId: string) =>
      request<QuestInfo>(`/api/accounts/${accountId}/quests`),
    execute: (accountId: string) =>
      request<{ result: string; gold_earned: number; xp_earned: number }>(`/api/accounts/${accountId}/quests/execute`, {
        method: "POST"
      }),
    start: (accountId: string, config?: any) =>
      request<WorkerInfo>(`/api/accounts/${accountId}/workers/quest/start`, {
        method: "POST",
        body: JSON.stringify(config || {})
      }),
    stop: (accountId: string) =>
      request<WorkerInfo>(`/api/accounts/${accountId}/workers/quest/stop`, {
        method: "POST"
      }),
    pause: (accountId: string) =>
      request<WorkerInfo>(`/api/accounts/${accountId}/workers/quest/pause`, {
        method: "POST"
      }),
    resume: (accountId: string) =>
      request<WorkerInfo>(`/api/accounts/${accountId}/workers/quest/resume`, {
        method: "POST"
      })
  },
  cards: {
    get: (accountId: string) =>
      request<CardItem[]>(`/api/accounts/${accountId}/cards`),
    evolve: (accountId: string, sacrifice_card_ids: number[], confirmed: boolean) =>
      request<any>(`/api/accounts/${accountId}/cards/evolve`, {
        method: "POST",
        body: JSON.stringify({ sacrifice_card_ids, confirmed })
      }),
    cooloff: (accountId: string, card_id: number, confirmed: boolean) =>
      request<any>(`/api/accounts/${accountId}/cards/cooloff`, {
        method: "POST",
        body: JSON.stringify({ card_id, confirmed })
      }),
    potionize: (accountId: string, hero_id: number, amount: number, confirmed: boolean) =>
      request<any>(`/api/accounts/${accountId}/cards/potionize`, {
        method: "POST",
        body: JSON.stringify({ hero_id, amount, confirmed })
      })
  },
  workers: {
    getAll: () => request<WorkerInfo[]>("/api/workers"),
    getForAccount: (accountId: string) => request<WorkerInfo[]>(`/api/accounts/${accountId}/workers`),
    control: (accountId: string, workerType: string, action: string, config?: any) =>
      request<WorkerInfo>(`/api/accounts/${accountId}/workers/${workerType}/control`, {
        method: "POST",
        body: JSON.stringify({ action, config })
      })
  },
  events: {
    list: (accountId?: string, limit = 50) =>
      request<ActivityEvent[]>(`/api/events?limit=${limit}${accountId ? `&account_id=${accountId}` : ""}`)
  },
  notifications: {
    list: (priority?: string, limit = 50) =>
      request<NotificationItem[]>(`/api/notifications?limit=${limit}${priority ? `&priority=${priority}` : ""}`)
  },
  settings: {
    get: () => request<SystemSettings>("/api/settings"),
    update: (data: Partial<SystemSettings>) =>
      request<{ message: string; settings: SystemSettings }>("/api/settings", {
        method: "POST",
        body: JSON.stringify(data)
      })
  },
  health: {
    get: () => request<HealthStatus>("/api/health")
  }
};
