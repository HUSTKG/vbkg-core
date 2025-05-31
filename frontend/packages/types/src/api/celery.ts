import {
  ApiResponse,
  CeleryStats,
  FlowerDashboardData,
  FlowerHealthStatus,
  TaskInfo,
  WorkerInfo,
  WorkerStats,
} from "../models";

// Request Types
export interface IGetCeleryDashboardRequest {
  // No parameters needed for dashboard
}

export interface IGetCeleryWorkersRequest {
  include_offline?: boolean;
}

export interface IGetCeleryTasksRequest {
  limit?: number;
  state?: string;
  worker?: string;
}

export interface IGetCeleryWorkerDetailRequest {
  worker_name: string;
}

export interface IGetCeleryTaskDetailRequest {
  task_id: string;
}

export interface IRevokeTaskRequest {
  task_id: string;
  terminate?: boolean;
}

export interface IShutdownWorkerRequest {
  worker_name: string;
}

// Response Types
export interface IGetCeleryDashboardResponse
  extends ApiResponse<FlowerDashboardData> {}

export interface IGetCeleryWorkersResponse extends ApiResponse<WorkerInfo[]> {}

export interface IGetCeleryWorkerStatsResponse
  extends ApiResponse<WorkerStats> {}

export interface IGetCeleryTasksResponse extends ApiResponse<TaskInfo[]> {}

export interface IGetCeleryStatsResponse extends ApiResponse<CeleryStats> {}

export interface IGetCeleryHealthResponse
  extends ApiResponse<FlowerHealthStatus> {}

export interface IGetCeleryWorkerDetailResponse
  extends ApiResponse<WorkerInfo> {}

export interface IGetCeleryTaskDetailResponse extends ApiResponse<TaskInfo> {}

export interface IRevokeTaskResponse
  extends ApiResponse<{ message: string; success: boolean }> {}

export interface IShutdownWorkerResponse
  extends ApiResponse<{ message: string; success: boolean }> {}
