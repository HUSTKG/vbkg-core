import { api } from "../config/axios";
import { API_ENDPOINTS } from "@vbkg/utils";
import {
  IGetQualityDashboardRequest,
  IGetQualityDashboardResponse,
  IGenerateQualityReportRequest,
  IGenerateQualityReportResponse,
  IRunQualityMonitoringRequest,
  IRunQualityMonitoringResponse,
  IGetConflictsRequest,
  IGetConflictsResponse,
  IDetectConflictsRequest,
  IDetectConflictsResponse,
  IResolveConflictRequest,
  IResolveConflictResponse,
  IAutoResolveConflictRequest,
  IAutoResolveConflictResponse,
  IApplyKGEditRequest,
  IApplyKGEditResponse,
  IRollbackKGChangesRequest,
  IRollbackKGChangesResponse,
  IAddQualityStepsToPipelineRequest,
  IAddQualityStepsToPipelineResponse,
} from "@vbkg/types";

// Quality Dashboard
const getQualityDashboard = async (
  input: IGetQualityDashboardRequest,
): Promise<IGetQualityDashboardResponse> => {
  return await api()
    .get<IGetQualityDashboardResponse>(API_ENDPOINTS.QUALITY_DASHBOARD, {
      params: input,
    })
    .then((res) => res.data);
};

const generateQualityReport = async (
  input: IGenerateQualityReportRequest,
): Promise<IGenerateQualityReportResponse> => {
  return await api()
    .get<IGenerateQualityReportResponse>(API_ENDPOINTS.QUALITY_REPORT, {
      params: input,
    })
    .then((res) => res.data);
};

const runQualityMonitoring = async (
  input: IRunQualityMonitoringRequest,
): Promise<IRunQualityMonitoringResponse> => {
  return await api()
    .post<IRunQualityMonitoringResponse>(
      API_ENDPOINTS.QUALITY_MONITORING_RUN,
      input,
    )
    .then((res) => res.data);
};

// Conflicts Management
const getConflicts = async (
  input: IGetConflictsRequest,
): Promise<IGetConflictsResponse> => {
  return await api()
    .get<IGetConflictsResponse>(API_ENDPOINTS.GET_CONFLICTS, {
      params: input,
    })
    .then((res) => res.data);
};

const detectConflicts = async (
  input?: IDetectConflictsRequest,
): Promise<IDetectConflictsResponse> => {
  return await api()
    .post<IDetectConflictsResponse>(API_ENDPOINTS.DETECT_CONFLICTS, input)
    .then((res) => res.data);
};

const resolveConflict = async (
  input: IResolveConflictRequest,
): Promise<IResolveConflictResponse> => {
  const { conflict_id, resolution } = input;
  return await api()
    .post<IResolveConflictResponse>(
      API_ENDPOINTS.RESOLVE_CONFLICT(conflict_id),
      { resolution },
    )
    .then((res) => res.data);
};

const autoResolveConflict = async (
  input: IAutoResolveConflictRequest,
): Promise<IAutoResolveConflictResponse> => {
  const { conflict_id, ...params } = input;
  return await api()
    .post<IAutoResolveConflictResponse>(
      API_ENDPOINTS.AUTO_RESOLVE_CONFLICT(conflict_id),
      params,
    )
    .then((res) => res.data);
};

// KG Editing
const applyKGEdit = async (
  input: IApplyKGEditRequest,
): Promise<IApplyKGEditResponse> => {
  return await api()
    .post<IApplyKGEditResponse>(API_ENDPOINTS.APPLY_KG_EDIT, input)
    .then((res) => res.data);
};

const rollbackKGChanges = async (
  input: IRollbackKGChangesRequest,
): Promise<IRollbackKGChangesResponse> => {
  return await api()
    .post<IRollbackKGChangesResponse>(API_ENDPOINTS.ROLLBACK_KG_CHANGES, input)
    .then((res) => res.data);
};

const addQualityStepsToPipeline = async (
  input: IAddQualityStepsToPipelineRequest,
): Promise<IAddQualityStepsToPipelineResponse> => {
  const { pipeline_id, ...data } = input;
  return await api()
    .post<IAddQualityStepsToPipelineResponse>(
      API_ENDPOINTS.ADD_QUALITY_STEPS_TO_PIPELINE(pipeline_id),
      data,
    )
    .then((res) => res.data);
};

export const QualityService = {
  // Dashboard
  getQualityDashboard,
  generateQualityReport,
  runQualityMonitoring,

  // Conflicts
  getConflicts,
  detectConflicts,
  resolveConflict,
  autoResolveConflict,

  // KG Editing
  applyKGEdit,
  rollbackKGChanges,
  addQualityStepsToPipeline,
};
