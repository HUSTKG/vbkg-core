import {
  IGetCeleryDashboardRequest,
  IGetCeleryDashboardResponse,
  IGetCeleryWorkersRequest,
  IGetCeleryWorkersResponse,
  IGetCeleryWorkerStatsResponse,
  IGetCeleryTasksRequest,
  IGetCeleryTasksResponse,
  IGetCeleryStatsResponse,
  IGetCeleryHealthResponse,
  IGetCeleryWorkerDetailRequest,
  IGetCeleryWorkerDetailResponse,
  IGetCeleryTaskDetailRequest,
  IGetCeleryTaskDetailResponse,
  IRevokeTaskRequest,
  IRevokeTaskResponse,
  IShutdownWorkerRequest,
  IShutdownWorkerResponse,
} from "@vbkg/types";

import { API_ENDPOINTS } from "@vbkg/utils";
import { api } from "../config/axios";

const getCeleryDashboard = async (
  input: IGetCeleryDashboardRequest,
): Promise<IGetCeleryDashboardResponse> => {
  return await api()
    .get<IGetCeleryDashboardResponse>(API_ENDPOINTS.CELERY_DASHBOARD)
    .then((res) => res.data);
};

const getCeleryWorkers = async (
  input: IGetCeleryWorkersRequest,
): Promise<IGetCeleryWorkersResponse> => {
  return await api()
    .get<IGetCeleryWorkersResponse>(API_ENDPOINTS.CELERY_WORKERS, {
      params: {
        ...input,
      },
    })
    .then((res) => res.data);
};

const getCeleryWorkerStats =
  async (): Promise<IGetCeleryWorkerStatsResponse> => {
    return await api()
      .get<IGetCeleryWorkerStatsResponse>(API_ENDPOINTS.CELERY_WORKER_STATS)
      .then((res) => res.data);
  };

const getCeleryTasks = async (
  input: IGetCeleryTasksRequest,
): Promise<IGetCeleryTasksResponse> => {
  return await api()
    .get<IGetCeleryTasksResponse>(API_ENDPOINTS.CELERY_TASKS, {
      params: {
        ...input,
      },
    })
    .then((res) => res.data);
};

const getCeleryStats = async (): Promise<IGetCeleryStatsResponse> => {
  return await api()
    .get<IGetCeleryStatsResponse>(API_ENDPOINTS.CELERY_STATS)
    .then((res) => res.data);
};

const getCeleryHealth = async (): Promise<IGetCeleryHealthResponse> => {
  return await api()
    .get<IGetCeleryHealthResponse>(API_ENDPOINTS.CELERY_HEALTH)
    .then((res) => res.data);
};

const getCeleryWorkerDetail = async (
  input: IGetCeleryWorkerDetailRequest,
): Promise<IGetCeleryWorkerDetailResponse> => {
  return await api()
    .get<IGetCeleryWorkerDetailResponse>(
      API_ENDPOINTS.CELERY_WORKER_DETAIL(input.worker_name),
    )
    .then((res) => res.data);
};

const getCeleryTaskDetail = async (
  input: IGetCeleryTaskDetailRequest,
): Promise<IGetCeleryTaskDetailResponse> => {
  return await api()
    .get<IGetCeleryTaskDetailResponse>(
      API_ENDPOINTS.CELERY_TASK_DETAIL(input.task_id),
    )
    .then((res) => res.data);
};

const revokeTask = async (
  input: IRevokeTaskRequest,
): Promise<IRevokeTaskResponse> => {
  return await api()
    .post<IRevokeTaskResponse>(
      API_ENDPOINTS.CELERY_TASK_REVOKE(input.task_id),
      {
        terminate: input.terminate || false,
      },
    )
    .then((res) => res.data);
};

const shutdownWorker = async (
  input: IShutdownWorkerRequest,
): Promise<IShutdownWorkerResponse> => {
  return await api()
    .post<IShutdownWorkerResponse>(
      API_ENDPOINTS.CELERY_WORKER_SHUTDOWN(input.worker_name),
    )
    .then((res) => res.data);
};

export const CeleryService = {
  getCeleryDashboard,
  getCeleryWorkers,
  getCeleryWorkerStats,
  getCeleryTasks,
  getCeleryStats,
  getCeleryHealth,
  getCeleryWorkerDetail,
  getCeleryTaskDetail,
  revokeTask,
  shutdownWorker,
};
