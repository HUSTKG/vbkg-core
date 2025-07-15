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
) => {
  return await api()
    .get<IGetQualityDashboardResponse>(API_ENDPOINTS.QUALITY_DASHBOARD, {
      params: input,
    })
};

const generateQualityReport = async (
  input: IGenerateQualityReportRequest,
) => {
  return await api()
    .get<IGenerateQualityReportResponse>(API_ENDPOINTS.QUALITY_REPORT, {
      params: input,
    })
};

const runQualityMonitoring = async (
  input: IRunQualityMonitoringRequest,
) => {
  return await api()
    .post<IRunQualityMonitoringResponse>(
      API_ENDPOINTS.QUALITY_MONITORING_RUN,
      input,
    )
};

// Conflicts Management
const getConflicts = async (
  input: IGetConflictsRequest,
) => {
  return await api()
    .get<IGetConflictsResponse>(API_ENDPOINTS.GET_CONFLICTS, {
      params: input,
    })
};

const detectConflicts = async (
  input?: IDetectConflictsRequest,
) => {
  return await api()
    .post<IDetectConflictsResponse>(API_ENDPOINTS.DETECT_CONFLICTS, input)
};

const resolveConflict = async (
  input: IResolveConflictRequest,
) => {
  const { conflict_id, ...resolution } = input;
  return await api()
    .post<IResolveConflictResponse>(
      API_ENDPOINTS.RESOLVE_CONFLICT(conflict_id),
      { ...resolution },
    )
};

const autoResolveConflict = async (
  input: IAutoResolveConflictRequest,
) => {
  const { conflict_id, ...params } = input;
  return await api()
    .post<IAutoResolveConflictResponse>(
      API_ENDPOINTS.AUTO_RESOLVE_CONFLICT(conflict_id),
      params,
    )
};

// KG Editing
const applyKGEdit = async (
  input: IApplyKGEditRequest,
) => {
  return await api()
    .post<IApplyKGEditResponse>(API_ENDPOINTS.APPLY_KG_EDIT, input)
};

const rollbackKGChanges = async (
  input: IRollbackKGChangesRequest,
) => {
  return await api()
    .post<IRollbackKGChangesResponse>(API_ENDPOINTS.ROLLBACK_KG_CHANGES, input)
};

const addQualityStepsToPipeline = async (
  input: IAddQualityStepsToPipelineRequest,
) => {
  const { pipeline_id, ...data } = input;
  return await api()
    .post<IAddQualityStepsToPipelineResponse>(
      API_ENDPOINTS.ADD_QUALITY_STEPS_TO_PIPELINE(pipeline_id),
      data,
    )
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
