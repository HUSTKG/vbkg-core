import {
  ApiResponse,
  ExecutionMode,
  ExecutionStatus,
  PaginatedResponse,
  RulePerformanceMetrics,
  RuleType,
  ValidationCategory,
  ValidationCondition,
  ValidationDashboardData,
  ValidationRule,
  ValidationRuleExecution,
  ValidationRuleTemplate,
  ValidationSeverity,
  ValidationSummary,
  ValidationViolation,
  ViolationStatus,
} from "../models";

export interface ICreateValidationRuleRequest {
  name: string;
  description?: string;
  category: ValidationCategory;
  rule_type: RuleType;
  is_active?: boolean;
  severity: ValidationSeverity;
  target_entity_types: string[];
  target_relationship_types?: string[];
  conditions: ValidationCondition | Record<string, any>;
  error_message: string;
  execution_mode?: ExecutionMode;
  batch_size?: number;
  timeout_seconds?: number;
  tags?: string[];
  documentation?: string;
  examples?: Record<string, any>;
}

export interface ICreateValidationRuleResponse
  extends ApiResponse<ValidationRule> {}

export interface IGetValidationRulesRequest {
  category?: ValidationCategory;
  is_active?: boolean;
  severity?: ValidationSeverity;
  entity_type?: string;
  limit?: number;
  offset?: number;
}

export interface IGetValidationRulesResponse
  extends PaginatedResponse<ValidationRule> {}

export interface IGetValidationRuleRequest {
  rule_id: string;
}

export interface IGetValidationRuleResponse
  extends ApiResponse<ValidationRule> {}

export interface IUpdateValidationRuleRequest {
  rule_id: string;
  name?: string;
  description?: string;
  category?: ValidationCategory;
  rule_type?: RuleType;
  is_active?: boolean;
  severity?: ValidationSeverity;
  target_entity_types?: string[];
  target_relationship_types?: string[];
  conditions?: ValidationCondition | Record<string, any>;
  error_message?: string;
  execution_mode?: ExecutionMode;
  batch_size?: number;
  timeout_seconds?: number;
  tags?: string[];
  documentation?: string;
  examples?: Record<string, any>;
}

export interface IUpdateValidationRuleResponse
  extends ApiResponse<ValidationRule> {}

export interface IDeleteValidationRuleRequest {
  rule_id: string;
}

export interface IDeleteValidationRuleResponse
  extends ApiResponse<{ message: string }> {}

export interface IToggleValidationRuleRequest {
  rule_id: string;
}

export interface IToggleValidationRuleResponse
  extends ApiResponse<ValidationRule> {}

// Rule Execution
export interface IExecuteValidationRuleRequest {
  rule_id: string;
  pipeline_run_id?: string;
  triggered_by?: string;
  execution_context?: Record<string, any>;
}

export interface IExecuteValidationRuleResponse
  extends ApiResponse<ValidationRuleExecution> {}

export interface IExecuteBatchValidationRulesRequest {
  rule_ids?: string[];
  category?: ValidationCategory;
  entity_type?: string;
}

export interface IExecuteBatchValidationRulesResponse
  extends ApiResponse<{ message: string }> {}

export interface IGetValidationExecutionsRequest {
  rule_id?: string;
  status?: ExecutionStatus;
  limit?: number;
}

export interface IGetValidationExecutionsResponse
  extends PaginatedResponse<ValidationRuleExecution> {}

export interface IGetValidationExecutionRequest {
  execution_id: string;
}

export interface IGetValidationExecutionResponse
  extends ApiResponse<ValidationRuleExecution> {}

// Violations
export interface IGetValidationViolationsRequest {
  rule_id?: string;
  status?: ViolationStatus;
  severity?: ValidationSeverity;
  limit?: number;
}

export interface IGetValidationViolationsResponse
  extends PaginatedResponse<ValidationViolation> {}

export interface IUpdateValidationViolationRequest {
  violation_id: string;
  status?: ViolationStatus;
  resolution_action?: string;
  resolution_notes?: string;
}

export interface IUpdateValidationViolationResponse
  extends ApiResponse<string> {}

export interface IBulkUpdateValidationViolationsRequest {
  violation_ids: string[];
  status?: ViolationStatus;
  resolution_action?: string;
  resolution_notes?: string;
}

export interface IBulkUpdateValidationViolationsResponse
  extends ApiResponse<{ updated_count: number }> {}

// Dashboard & Statistics
export interface IGetValidationDashboardRequest {}

export interface IGetValidationDashboardResponse
  extends ApiResponse<ValidationDashboardData> {}

export interface IGetValidationPerformanceRequest {
  rule_ids?: string[];
}

export interface IGetValidationPerformanceResponse
  extends ApiResponse<RulePerformanceMetrics[]> {}

export interface IGetValidationSummaryRequest {}

export interface IGetValidationSummaryResponse
  extends ApiResponse<ValidationSummary> {}

// Templates
export interface IGetValidationTemplatesRequest {}

export interface IGetValidationTemplatesResponse
  extends ApiResponse<ValidationRuleTemplate[]> {}

export interface ICreateRuleFromTemplateRequest {
  template_id: string;
  name?: string;
  description?: string;
  severity?: ValidationSeverity;
  conditions?: Record<string, any>;
  error_message?: string;
  target_entity_types?: string[];
  tags?: string[];
}

export interface ICreateRuleFromTemplateResponse
  extends ApiResponse<ValidationRule> {}

// Pipeline Integration
export interface IAddValidationToPipelineRequest {
  pipeline_id: string;
  rule_ids?: string[];
  category?: ValidationCategory;
  entity_type?: string;
}

export interface IAddValidationToPipelineResponse
  extends ApiResponse<{ step: any }> {}
