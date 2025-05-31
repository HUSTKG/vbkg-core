import {
  ApiResponse,
  Conflict,
  ConflictResolution,
  ConflictStatus,
  ConflictType,
  KGEdit,
  KGEditResult,
  PaginatedResponse,
  QualityReport,
} from "../models";

export interface IGetQualityDashboardRequest {}
export interface IGetQualityDashboardResponse
  extends ApiResponse<{
    quality_report: QualityReport;
    conflict_statistics: {
      by_status: Record<string, number>;
      by_type: Record<string, number>;
      total_pending: number;
    };
    recent_activity: Array<{
      type: string;
      timestamp: string;
      description: string;
      user: string;
      status: string;
    }>;
    trending_metrics: {
      trend: string;
      recent_scores: number[];
      current_score: number;
    };
  }> {}

export interface IGenerateQualityReportRequest {
  days_back?: number;
}
export interface IGenerateQualityReportResponse
  extends ApiResponse<QualityReport> {}

export interface IRunQualityMonitoringRequest {}
export interface IRunQualityMonitoringResponse
  extends ApiResponse<{
    status: string;
    message: string;
  }> {}

export interface IGetConflictsRequest {
  status?: ConflictStatus;
  conflict_type?: ConflictType;
  assigned_to_me?: boolean;
  limit?: number;
  skip?: number;
}
export interface IGetConflictsResponse extends PaginatedResponse<Conflict> {}

export interface IDetectConflictsRequest {
  entity_ids?: string[];
}
export interface IDetectConflictsResponse
  extends ApiResponse<{
    status: string;
    conflicts_detected?: number;
  }> {}

export interface IResolveConflictRequest {
  conflict_id: string;
  resolution: ConflictResolution;
}
export interface IResolveConflictResponse
  extends ApiResponse<{
    success: boolean;
    message: string;
  }> {}

export interface IAutoResolveConflictRequest {
  conflict_id: string;
  use_ai?: boolean;
  confidence_threshold?: number;
}
export interface IAutoResolveConflictResponse
  extends ApiResponse<{
    success: boolean;
    message: string;
    applied_resolution?: ConflictResolution;
  }> {}

export interface IApplyKGEditRequest {
  edit: KGEdit;
}
export interface IApplyKGEditResponse extends ApiResponse<KGEditResult> {}

export interface IRollbackKGChangesRequest {
  rollback_info: Record<string, any>;
}
export interface IRollbackKGChangesResponse
  extends ApiResponse<{
    success: boolean;
    message: string;
  }> {}

export interface IAddQualityStepsToPipelineRequest {
  pipeline_id: string;
  include_validation?: boolean;
  include_conflict_detection?: boolean;
  include_auto_resolution?: boolean;
}
export interface IAddQualityStepsToPipelineResponse
  extends ApiResponse<{
    added_steps: Array<Record<string, any>>;
  }> {}
