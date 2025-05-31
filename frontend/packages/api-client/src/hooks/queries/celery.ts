import { useQuery, UseQueryOptions } from "@tanstack/react-query";
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
} from "@vbkg/types";
import { QueryKeys } from "../../config/queryKeys";
import { CeleryService } from "../../services/celery";

// Fetch complete dashboard data
export const useCeleryDashboard = (
  input: IGetCeleryDashboardRequest = {},
  options?: UseQueryOptions<IGetCeleryDashboardResponse, Error>,
) => {
  return useQuery<IGetCeleryDashboardResponse, Error>({
    queryKey: QueryKeys.celery.dashboard(),
    queryFn: () => CeleryService.getCeleryDashboard(input),
    refetchInterval: 30000, // Auto refresh every 30 seconds
    ...options,
  });
};

// Fetch all workers
export const useCeleryWorkers = (
  input: IGetCeleryWorkersRequest = {},
  options?: UseQueryOptions<IGetCeleryWorkersResponse, Error>,
) => {
  return useQuery<IGetCeleryWorkersResponse, Error>({
    queryKey: QueryKeys.celery.workers.list(input),
    queryFn: () => CeleryService.getCeleryWorkers(input),
    refetchInterval: 15000, // Auto refresh every 15 seconds
    ...options,
  });
};

// Fetch worker statistics
export const useCeleryWorkerStats = (
  options?: UseQueryOptions<IGetCeleryWorkerStatsResponse, Error>,
) => {
  return useQuery<IGetCeleryWorkerStatsResponse, Error>({
    queryKey: QueryKeys.celery.workers.stats(),
    queryFn: () => CeleryService.getCeleryWorkerStats(),
    refetchInterval: 15000,
    ...options,
  });
};

// Fetch tasks
export const useCeleryTasks = (
  input: IGetCeleryTasksRequest = { limit: 50 },
  options?: UseQueryOptions<IGetCeleryTasksResponse, Error>,
) => {
  return useQuery<IGetCeleryTasksResponse, Error>({
    queryKey: QueryKeys.celery.tasks.list(input),
    queryFn: () => CeleryService.getCeleryTasks(input),
    refetchInterval: 10000, // Auto refresh every 10 seconds
    ...options,
  });
};

// Fetch celery statistics
export const useCeleryStats = (
  options?: UseQueryOptions<IGetCeleryStatsResponse, Error>,
) => {
  return useQuery<IGetCeleryStatsResponse, Error>({
    queryKey: QueryKeys.celery.stats(),
    queryFn: () => CeleryService.getCeleryStats(),
    refetchInterval: 15000,
    ...options,
  });
};

// Fetch health status
export const useCeleryHealth = (
  options?: UseQueryOptions<IGetCeleryHealthResponse, Error>,
) => {
  return useQuery<IGetCeleryHealthResponse, Error>({
    queryKey: QueryKeys.celery.health(),
    queryFn: () => CeleryService.getCeleryHealth(),
    refetchInterval: 30000,
    retry: 1, // Don't retry too much for health checks
    ...options,
  });
};

// Fetch specific worker detail
export const useCeleryWorkerDetail = (
  input: IGetCeleryWorkerDetailRequest,
  options?: UseQueryOptions<IGetCeleryWorkerDetailResponse, Error>,
) => {
  return useQuery<IGetCeleryWorkerDetailResponse, Error>({
    queryKey: QueryKeys.celery.workers.detail(input.worker_name),
    queryFn: () => CeleryService.getCeleryWorkerDetail(input),
    refetchInterval: 10000,
    enabled: !!input.worker_name,
    ...options,
  });
};

// Fetch specific task detail
export const useCeleryTaskDetail = (
  input: IGetCeleryTaskDetailRequest,
  options?: UseQueryOptions<IGetCeleryTaskDetailResponse, Error>,
) => {
  return useQuery<IGetCeleryTaskDetailResponse, Error>({
    queryKey: QueryKeys.celery.tasks.detail(input.task_id),
    queryFn: () => CeleryService.getCeleryTaskDetail(input),
    enabled: !!input.task_id,
    ...options,
  });
};
