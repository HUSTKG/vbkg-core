export enum ValidationCategory {
  COMPLETENESS = "completeness",
  ACCURACY = "accuracy",
  CONSISTENCY = "consistency",
  VALIDITY = "validity",
  UNIQUENESS = "uniqueness",
  TIMELINESS = "timeliness",
  RELEVANCE = "relevance",
}

export enum RuleType {
  FIELD_VALIDATION = "field_validation",
  FORMAT_VALIDATION = "format_validation",
  BUSINESS_LOGIC = "business_logic",
  UNIQUENESS_CHECK = "uniqueness_check",
  RELATIONSHIP_VALIDATION = "relationship_validation",
  CUSTOM_VALIDATION = "custom_validation",
}

export enum ValidationSeverity {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical",
}

export enum ExecutionMode {
  ON_DEMAND = "on_demand",
  REAL_TIME = "real_time",
  BATCH = "batch",
  SCHEDULED = "scheduled",
}

export enum ExecutionStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

export enum ViolationStatus {
  OPEN = "open",
  RESOLVED = "resolved",
  IGNORED = "ignored",
  FALSE_POSITIVE = "false_positive",
}

// Base Models
export interface ValidationCondition {
  field: string;
  operator: string;
  value?: any;
  scope?: string;
}

export interface ValidationRuleBase {
  name: string;
  description?: string;
  category: ValidationCategory;
  rule_type: RuleType;
  is_active: boolean;
  severity: ValidationSeverity;
  target_entity_types: string[];
  target_relationship_types?: string[];
  conditions: ValidationCondition | Record<string, any>;
  error_message: string;
  execution_mode: ExecutionMode;
  batch_size?: number;
  timeout_seconds?: number;
  tags?: string[];
  documentation?: string;
  examples?: Record<string, any>;
}

export interface ValidationRule extends ValidationRuleBase {
  id: string;
  execution_count: number;
  violation_count: number;
  success_rate: number;
  last_executed_at?: string;
  average_execution_time?: number;
  created_by?: string;
  updated_by?: string;
  created_at: string;
  updated_at: string;
}

export interface ValidationRuleExecution {
  id: string;
  rule_id: string;
  pipeline_run_id?: string;
  status: ExecutionStatus;
  start_time: string;
  end_time?: string;
  execution_time?: number;
  entities_checked: number;
  relationships_checked: number;
  violations_found: number;
  violations_details?: Record<string, any>;
  error_message?: string;
  stack_trace?: string;
  triggered_by: string;
  execution_context?: Record<string, any>;
  created_at: string;
}

export interface ValidationViolation {
  id: string;
  rule_execution_id: string;
  rule_id: string;
  entity_id?: string;
  relationship_id?: string;
  violation_type: string;
  severity: ValidationSeverity;
  message: string;
  field_name?: string;
  expected_value?: string;
  actual_value?: string;
  status: ViolationStatus;
  resolution_action?: string;
  resolved_by?: string;
  resolved_at?: string;
  resolution_notes?: string;
  context_data?: Record<string, any>;
  suggestions?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ValidationRuleTemplate {
  id: string;
  name: string;
  description?: string;
  category: ValidationCategory;
  rule_type: RuleType;
  conditions_template: Record<string, any>;
  default_severity: ValidationSeverity;
  default_error_message: string;
  usage_count: number;
  is_builtin: boolean;
  tags?: string[];
  documentation?: string;
  examples?: Record<string, any>;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface RulePerformanceMetrics {
  rule_id: string;
  rule_name: string;
  total_executions: number;
  avg_execution_time?: number;
  total_violations: number;
  success_rate: number;
  last_executed?: string;
}

export interface ValidationSummary {
  total_rules: number;
  active_rules: number;
  recent_violations: number;
  avg_success_rate: number;
  critical_violations: number;
}

export interface ValidationDashboardData {
  summary: ValidationSummary;
  recent_executions: ValidationRuleExecution[];
  top_violating_rules: RulePerformanceMetrics[];
  violation_trends: Record<string, any>;
  rule_performance: RulePerformanceMetrics[];
}
