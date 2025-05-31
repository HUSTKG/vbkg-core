// Base Types
export interface SystemInfo {
  cpu_usage: number;
  memory_usage: number;
  memory_total: number;
  disk_usage: number;
  uptime: string;
}

export interface WorkerInfo {
  name: string;
  status: "online" | "offline";
  active_tasks: number;
  processed_tasks: number;
  load_avg: number[];
  system_info: SystemInfo;
  heartbeat: string | null;
  last_heartbeat_delta: number;
}

export interface WorkerStats {
  total: number;
  online: number;
  offline: number;
}

export interface TaskInfo {
  id: string;
  name: string;
  state: string;
  runtime: number;
  timestamp: string;
  worker?: string;
  args: any[];
  kwargs: Record<string, any>;
  result?: any;
  traceback?: string;
  exception?: string;
}

export interface CeleryStats {
  success: number;
  running: number;
  failed: number;
  total: number;
}

export interface FlowerDashboardData {
  workers: WorkerInfo[];
  worker_stats: WorkerStats;
  celery_stats: CeleryStats;
  tasks: TaskInfo[];
}

export interface FlowerHealthStatus {
  status: "healthy" | "unhealthy";
  flower_url: string;
  error?: string;
}
