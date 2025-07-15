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

const getCeleryDashboard = async (_input: IGetCeleryDashboardRequest) => {
	return await api().get<IGetCeleryDashboardResponse>(
		API_ENDPOINTS.CELERY_DASHBOARD,
	);
};

const getCeleryWorkers = async (input: IGetCeleryWorkersRequest) => {
	return await api().get<IGetCeleryWorkersResponse>(
		API_ENDPOINTS.CELERY_WORKERS,
		{
			params: {
				...input,
			},
		},
	);
};

const getCeleryWorkerStats = async () => {
	return await api().get<IGetCeleryWorkerStatsResponse>(
		API_ENDPOINTS.CELERY_WORKER_STATS,
	);
};

const getCeleryTasks = async (input: IGetCeleryTasksRequest) => {
	return await api().get<IGetCeleryTasksResponse>(API_ENDPOINTS.CELERY_TASKS, {
		params: {
			...input,
		},
	});
};

const getCeleryStats = async () => {
	return await api().get<IGetCeleryStatsResponse>(API_ENDPOINTS.CELERY_STATS);
};

const getCeleryHealth = async () => {
	return await api().get<IGetCeleryHealthResponse>(API_ENDPOINTS.CELERY_HEALTH);
};

const getCeleryWorkerDetail = async (input: IGetCeleryWorkerDetailRequest) => {
	return await api().get<IGetCeleryWorkerDetailResponse>(
		API_ENDPOINTS.CELERY_WORKER_DETAIL(input.worker_name),
	);
};

const getCeleryTaskDetail = async (input: IGetCeleryTaskDetailRequest) => {
	return await api().get<IGetCeleryTaskDetailResponse>(
		API_ENDPOINTS.CELERY_TASK_DETAIL(input.task_id),
	);
};

const revokeTask = async (input: IRevokeTaskRequest) => {
	return await api().post<IRevokeTaskResponse>(
		API_ENDPOINTS.CELERY_TASK_REVOKE(input.task_id),
		{
			terminate: input.terminate || false,
		},
	);
};

const shutdownWorker = async (input: IShutdownWorkerRequest) => {
	return await api().post<IShutdownWorkerResponse>(
		API_ENDPOINTS.CELERY_WORKER_SHUTDOWN(input.worker_name),
	);
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
