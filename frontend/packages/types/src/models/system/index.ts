export interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  storageUsage: number;
  activeUsers: number;
  requestsPerMinute: number;
  averageResponseTime: number;
  errors: {
    count: number;
    types: Record<string, number>;
  };
  timestamp: Date;
}
