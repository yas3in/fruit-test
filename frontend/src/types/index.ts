export interface Account {
  id: string;
  name: string;
  masked_restore_key: string;
  is_active: boolean;
  player_id?: number;
  player_name?: string;
  level: number;
  xp: number;
  gold: number;
  nectar: number;
  potion: number;
  global_rank?: number;
  league_rank?: number;
  tribe_name?: string;
  attack_power: number;
  defense_power: number;
  current_state: string; // READY, RUNNING, WAITING, ERROR, CAPTCHA REQUIRED, STOPPED
  battle_worker_status: string;
  mine_worker_status: string;
  quest_worker_status: string;
  last_activity?: string;
  next_action?: string;
  last_error?: string;
  captcha_status: string;
  last_successful_request?: string;
  last_login?: string;
}

export interface WorkerInfo {
  worker: string;
  account_id: string;
  account: string;
  status: string;
  started_at?: string;
  last_action?: string;
  next_action?: string;
  last_error?: string;
  action_count: number;
}

export interface BattleHistoryItem {
  id: number;
  time: string;
  opponent: string;
  opponent_power: number;
  result: "WIN" | "LOSS";
  gold: number;
  xp: number;
  cards: number[];
  duration: string;
}

export interface BattleSummary {
  total_battles_today: number;
  wins_today: number;
  losses_today: number;
  win_rate_today: number;
  gold_earned_today: number;
  xp_earned_today: number;
  recent_battles: BattleHistoryItem[];
  worker_status?: string;
  worker_state?: string;
}

export interface MineInfo {
  account_id: string;
  account_name: string;
  current_gold: number;
  collection_status: string;
  next_collection_time: string;
  countdown: string;
  seconds_remaining: number;
  last_collection_time: string;
  gold_collected_today: number;
  number_of_collections: number;
  mine_power: number;
  mine_capacity: number;
  worker_state: string;
  worker_status?: string;
}

export interface QuestInfo {
  account_id: string;
  account_name: string;
  quests_completed_today: number;
  current_quest: string;
  last_quest_result: string;
  gold_earned: number;
  xp_earned: number;
  worker_status: string;
}

export interface CardItem {
  id: number;
  name: string;
  level: number;
  attack: number;
  defense: number;
  rarity: number;
  potion: number;
  cooldown: boolean;
  status: string;
}

export interface ActivityEvent {
  id?: number;
  timestamp: string;
  account_id?: string;
  account_name?: string;
  event_type: string;
  message: string;
  metadata?: Record<string, any>;
  priority?: string;
}

export interface NotificationItem {
  id: number;
  timestamp: string;
  account_id?: string;
  account_name: string;
  priority: "INFO" | "WARNING" | "ERROR" | "CRITICAL";
  title: string;
  message: string;
  occurrence_count: number;
  last_occurrence: string;
  is_read: boolean;
}

export interface SystemSettings {
  battle_delay_min: number;
  battle_delay_max: number;
  max_battles_per_run: number;
  min_gold_threshold: number;
  max_opponent_defense: number;
  auto_heal: boolean;
  auto_cooldown: boolean;
  mine_delay_minutes: number;
  quest_delay_min: number;
  quest_delay_max: number;
  max_quests_per_run: number;
  auto_restart_workers: boolean;
  stop_on_captcha: boolean;
  stop_on_error: boolean;
  telegram_enabled: boolean;
  telegram_chat_id?: string;
  has_telegram_token: boolean;
  proxy_enabled: boolean;
  proxy_port: number;
  proxy_url: string;
  timezone: string;
  daily_report_time: string;
  logging_level: string;
}

export interface HealthStatus {
  status: string;
  database: string;
  api: string;
  telegram: string;
  proxy_port: number;
  proxy_enabled: boolean;
  last_check?: string;
}
