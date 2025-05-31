import { z } from "zod";
import {
  ValidationCategory,
  RuleType,
  ValidationSeverity,
  ExecutionMode,
  ExecutionStatus,
  ViolationStatus,
} from "@vbkg/types";

// Enum Schemas
const ValidationCategorySchema = z.nativeEnum(ValidationCategory);
const RuleTypeSchema = z.nativeEnum(RuleType);
const ValidationSeveritySchema = z.nativeEnum(ValidationSeverity);
const ExecutionModeSchema = z.nativeEnum(ExecutionMode);
const ExecutionStatusSchema = z.nativeEnum(ExecutionStatus);
const ViolationStatusSchema = z.nativeEnum(ViolationStatus);

// Base Validation Condition Schema
const ValidationConditionSchema = z.object({
  field: z.string().min(1, "Field name is required"),
  operator: z.string().min(1, "Operator is required"),
  value: z.any().optional(),
  scope: z.string().optional(),
});

// Create Validation Rule Schema
export const CreateValidationRuleSchema = z.object({
  name: z
    .string()
    .min(1, "Rule name is required")
    .max(255, "Rule name too long"),
  description: z.string().max(1000, "Description too long").optional(),
  category: ValidationCategorySchema,
  rule_type: RuleTypeSchema,
  is_active: z.boolean().default(true),
  severity: ValidationSeveritySchema.default(ValidationSeverity.MEDIUM),
  target_entity_types: z
    .array(z.string())
    .min(1, "At least one target entity type required")
    .default(["*"]),
  target_relationship_types: z.array(z.string()).optional(),
  conditions: z.union([ValidationConditionSchema, z.record(z.any())]),
  error_message: z
    .string()
    .min(1, "Error message is required")
    .max(500, "Error message too long"),
  execution_mode: ExecutionModeSchema.default(ExecutionMode.ON_DEMAND),
  batch_size: z.number().int().min(1).max(10000).default(100),
  timeout_seconds: z.number().int().min(1).max(3600).default(300),
  tags: z.array(z.string()).optional(),
  documentation: z.string().max(2000, "Documentation too long").optional(),
  examples: z.record(z.any()).optional(),
});

// Update Validation Rule Schema
export const UpdateValidationRuleSchema = z.object({
  name: z
    .string()
    .min(1, "Rule name is required")
    .max(255, "Rule name too long")
    .optional(),
  description: z.string().max(1000, "Description too long").optional(),
  category: ValidationCategorySchema.optional(),
  rule_type: RuleTypeSchema.optional(),
  is_active: z.boolean().optional(),
  severity: ValidationSeveritySchema.optional(),
  target_entity_types: z
    .array(z.string())
    .min(1, "At least one target entity type required")
    .optional(),
  target_relationship_types: z.array(z.string()).optional(),
  conditions: z
    .union([ValidationConditionSchema, z.record(z.any())])
    .optional(),
  error_message: z
    .string()
    .min(1, "Error message is required")
    .max(500, "Error message too long")
    .optional(),
  execution_mode: ExecutionModeSchema.optional(),
  batch_size: z.number().int().min(1).max(10000).optional(),
  timeout_seconds: z.number().int().min(1).max(3600).optional(),
  tags: z.array(z.string()).optional(),
  documentation: z.string().max(2000, "Documentation too long").optional(),
  examples: z.record(z.any()).optional(),
});

// Get Validation Rules Schema
export const GetValidationRulesSchema = z.object({
  category: ValidationCategorySchema.optional(),
  is_active: z.boolean().optional(),
  severity: ValidationSeveritySchema.optional(),
  entity_type: z.string().optional(),
  limit: z.number().int().min(1).max(1000).default(50),
  offset: z.number().int().min(0).default(0),
});

// Get Validation Rule by ID Schema
export const GetValidationRuleByIdSchema = z.object({
  rule_id: z.string().uuid("Invalid rule ID"),
});

// Execute Validation Rule Schema
export const ExecuteValidationRuleSchema = z.object({
  rule_id: z.string().uuid("Invalid rule ID"),
  pipeline_run_id: z.string().uuid("Invalid pipeline run ID").optional(),
  triggered_by: z.string().default("manual"),
  execution_context: z.record(z.any()).optional(),
});

// Execute Batch Validation Rules Schema
export const ExecuteBatchValidationRulesSchema = z.object({
  rule_ids: z.array(z.string().uuid("Invalid rule ID")).optional(),
  category: ValidationCategorySchema.optional(),
  entity_type: z.string().optional(),
});

// Get Validation Executions Schema
export const GetValidationExecutionsSchema = z.object({
  rule_id: z.string().uuid("Invalid rule ID").optional(),
  status: ExecutionStatusSchema.optional(),
  limit: z.number().int().min(1).max(500).default(50),
});

// Get Validation Execution by ID Schema
export const GetValidationExecutionByIdSchema = z.object({
  execution_id: z.string().uuid("Invalid execution ID"),
});

// Get Validation Violations Schema
export const GetValidationViolationsSchema = z.object({
  rule_id: z.string().uuid("Invalid rule ID").optional(),
  status: ViolationStatusSchema.optional(),
  severity: ValidationSeveritySchema.optional(),
  limit: z.number().int().min(1).max(1000).default(100),
});

// Update Validation Violation Schema
export const UpdateValidationViolationSchema = z.object({
  violation_id: z.string().uuid("Invalid violation ID"),
  status: ViolationStatusSchema.optional(),
  resolution_action: z
    .string()
    .max(500, "Resolution action too long")
    .optional(),
  resolution_notes: z
    .string()
    .max(1000, "Resolution notes too long")
    .optional(),
});

// Bulk Update Validation Violations Schema
export const BulkUpdateValidationViolationsSchema = z.object({
  violation_ids: z
    .array(z.string().uuid("Invalid violation ID"))
    .min(1, "At least one violation ID required"),
  status: ViolationStatusSchema.optional(),
  resolution_action: z
    .string()
    .max(500, "Resolution action too long")
    .optional(),
  resolution_notes: z
    .string()
    .max(1000, "Resolution notes too long")
    .optional(),
});

// Get Validation Performance Schema
export const GetValidationPerformanceSchema = z.object({
  rule_ids: z.array(z.string().uuid("Invalid rule ID")).optional(),
});

// Create Rule from Template Schema
export const CreateRuleFromTemplateSchema = z.object({
  template_id: z.string().uuid("Invalid template ID"),
  name: z
    .string()
    .min(1, "Rule name is required")
    .max(255, "Rule name too long")
    .optional(),
  description: z.string().max(1000, "Description too long").optional(),
  severity: ValidationSeveritySchema.optional(),
  conditions: z.record(z.any()).optional(),
  error_message: z
    .string()
    .min(1, "Error message is required")
    .max(500, "Error message too long")
    .optional(),
  target_entity_types: z
    .array(z.string())
    .min(1, "At least one target entity type required")
    .optional(),
  tags: z.array(z.string()).optional(),
});

// Add Validation to Pipeline Schema
export const AddValidationToPipelineSchema = z.object({
  pipeline_id: z.string().uuid("Invalid pipeline ID"),
  rule_ids: z.array(z.string().uuid("Invalid rule ID")).optional(),
  category: ValidationCategorySchema.optional(),
  entity_type: z.string().optional(),
});

// Toggle Validation Rule Schema
export const ToggleValidationRuleSchema = z.object({
  rule_id: z.string().uuid("Invalid rule ID"),
});

// Delete Validation Rule Schema
export const DeleteValidationRuleSchema = z.object({
  rule_id: z.string().uuid("Invalid rule ID"),
});

// Validation Rule Template Schemas
export const CreateValidationRuleTemplateSchema = z.object({
  name: z
    .string()
    .min(1, "Template name is required")
    .max(255, "Template name too long"),
  description: z.string().max(1000, "Description too long").optional(),
  category: ValidationCategorySchema,
  rule_type: RuleTypeSchema,
  conditions_template: z.record(z.any()),
  default_severity: ValidationSeveritySchema.default(ValidationSeverity.MEDIUM),
  default_error_message: z
    .string()
    .min(1, "Default error message is required")
    .max(500, "Error message too long"),
  tags: z.array(z.string()).optional(),
  documentation: z.string().max(2000, "Documentation too long").optional(),
  examples: z.record(z.any()).optional(),
});

// Validation for rule conditions based on rule type
export const validateRuleConditions = (
  ruleType: RuleType,
  conditions: any,
): boolean => {
  switch (ruleType) {
    case RuleType.FIELD_VALIDATION:
      return !!(conditions.field && conditions.operator);

    case RuleType.FORMAT_VALIDATION:
      return !!(
        conditions.field &&
        conditions.operator === "matches_pattern" &&
        conditions.value
      );

    case RuleType.BUSINESS_LOGIC:
      return !!(
        conditions.field ||
        (conditions.start_field && conditions.end_field)
      );

    case RuleType.UNIQUENESS_CHECK:
      return !!(conditions.field && conditions.operator === "unique");

    case RuleType.RELATIONSHIP_VALIDATION:
      return !!(conditions.relationship_type || conditions.validation_rules);

    case RuleType.CUSTOM_VALIDATION:
      return true; // Custom validation can have any structure

    default:
      return false;
  }
};

// Enhanced validation with custom rule logic
export const EnhancedCreateValidationRuleSchema =
  CreateValidationRuleSchema.refine(
    (data) => validateRuleConditions(data.rule_type, data.conditions),
    {
      message: "Invalid conditions for the selected rule type",
      path: ["conditions"],
    },
  );

export const EnhancedUpdateValidationRuleSchema =
  UpdateValidationRuleSchema.refine(
    (data) => {
      if (data.rule_type && data.conditions) {
        return validateRuleConditions(data.rule_type, data.conditions);
      }
      return true;
    },
    {
      message: "Invalid conditions for the selected rule type",
      path: ["conditions"],
    },
  );
