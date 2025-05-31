export enum ConflictType {
  DUPLICATE_ENTITY = "duplicate_entity",
  CONTRADICTORY_RELATIONSHIP = "contradictory_relationship",
  MISSING_RELATIONSHIP = "missing_relationship",
  ATTRIBUTE_MISMATCH = "attribute_mismatch",
  TEMPORAL_CONFLICT = "temporal_conflict",
  SOURCE_CONFLICT = "source_conflict",
  SCHEMA_MISMATCH = "schema_mismatch",
}

export enum ConflictSeverity {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical",
}

export enum ConflictStatus {
  DETECTED = "detected",
  UNDER_REVIEW = "under_review",
  RESOLVED_MANUAL = "resolved_manual",
  RESOLVED_AUTO = "resolved_auto",
  REJECTED = "rejected",
  ESCALATED = "escalated",
}

export enum ResolutionMethod {
  MERGE_ENTITIES = "merge_entities",
  KEEP_BOTH = "keep_both",
  KEEP_SOURCE = "keep_source",
  KEEP_TARGET = "keep_target",
  CREATE_NEW = "create_new",
  DELETE_CONFLICTING = "delete_conflicting",
  MANUAL_EDIT = "manual_edit",
  AI_RESOLUTION = "ai_resolution",
}

export enum QualityDimension {
  COMPLETENESS = "completeness",
  ACCURACY = "accuracy",
  CONSISTENCY = "consistency",
  VALIDITY = "validity",
  UNIQUENESS = "uniqueness",
  TIMELINESS = "timeliness",
  RELEVANCE = "relevance",
}

export enum KGEditAction {
  CREATE_ENTITY = "create_entity",
  UPDATE_ENTITY = "update_entity",
  DELETE_ENTITY = "delete_entity",
  MERGE_ENTITIES = "merge_entities",
  CREATE_RELATIONSHIP = "create_relationship",
  UPDATE_RELATIONSHIP = "update_relationship",
  DELETE_RELATIONSHIP = "delete_relationship",
  BULK_UPDATE = "bulk_update",
}

// Base Models
export interface ConflictResolution {
  resolution_method: ResolutionMethod;
  resolution_data: Record<string, any>;
  reasoning: string;
  confidence_score?: number;
  resolved_by: string;
  resolution_timestamp: string;
  validation_required: boolean;
}

export interface Conflict {
  id: string;
  conflict_type: ConflictType;
  severity: ConflictSeverity;
  status: ConflictStatus;
  description: string;
  confidence_score: number;
  source_entity_id?: string;
  target_entity_id?: string;
  source_relationship_id?: string;
  target_relationship_id?: string;
  conflicting_attributes?: Record<string, any>;
  context_data?: Record<string, any>;
  detected_by: string;
  detected_at: string;
  assigned_to?: string;
  resolution?: ConflictResolution;
  review_notes?: string;
  escalation_reason?: string;
  auto_resolution_suggestions?: Array<Record<string, any>>;
  created_at: string;
  updated_at: string;
}

export interface QualityReport {
  report_date: string;
  overall_score: number;
  dimension_scores: Record<QualityDimension, number>;
  total_entities: number;
  total_relationships: number;
  issues_detected: number;
  conflicts_pending: number;
  improvement_recommendations: string[];
}

export interface KGEdit {
  action: KGEditAction;
  entity_data?: Record<string, any>;
  relationship_data?: Record<string, any>;
  bulk_data?: Array<Record<string, any>>;
  reason: string;
  validate_before_apply: boolean;
}

export interface KGEditResult {
  success: boolean;
  applied_changes: Array<Record<string, any>>;
  validation_errors?: string[];
  rollback_info?: Record<string, any>;
}
