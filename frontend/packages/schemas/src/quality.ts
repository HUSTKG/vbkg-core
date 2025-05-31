import { z } from "zod";

const ConflictTypeSchema = z.enum([
  "duplicate_entity",
  "contradictory_relationship",
  "missing_relationship",
  "attribute_mismatch",
  "temporal_conflict",
  "source_conflict",
  "schema_mismatch",
]);

export const ConflictSeveritySchema = z.enum([
  "low",
  "medium",
  "high",
  "critical",
]);
const ConflictStatusSchema = z.enum([
  "detected",
  "under_review",
  "resolved_manual",
  "resolved_auto",
  "rejected",
  "escalated",
]);

// Request Schemas - CHỈ CÁC API CÓ THẬT
export const GetQualityDashboardSchema = z.object({});

export const GenerateQualityReportSchema = z.object({
  days_back: z.number().min(1).max(365).default(30),
});

export const RunQualityMonitoringSchema = z.object({});

export const GetConflictsSchema = z.object({
  status: ConflictStatusSchema.optional(),
  conflict_type: ConflictTypeSchema.optional(),
  assigned_to_me: z.boolean().optional(),
  limit: z.number().min(1).max(100).default(50),
  skip: z.number().min(0).default(0),
});

export const DetectConflictsSchema = z.object({
  entity_ids: z.array(z.string().uuid()).optional(),
});

export const ResolveConflictSchema = z.object({
  conflict_id: z.string().uuid(),
  resolution: z.object({
    resolution_method: z.enum([
      "merge_entities",
      "keep_both",
      "keep_source",
      "keep_target",
      "create_new",
      "delete_conflicting",
      "manual_edit",
      "ai_resolution",
    ]),
    resolution_data: z.record(z.any()),
    reasoning: z.string().min(1),
    confidence_score: z.number().min(0).max(1).optional(),
    resolved_by: z.string().min(1),
    validation_required: z.boolean().default(false),
  }),
});

export const AutoResolveConflictSchema = z.object({
  conflict_id: z.string().uuid(),
  use_ai: z.boolean().default(true),
  confidence_threshold: z.number().min(0).max(1).default(0.8),
});

export const ApplyKGEditSchema = z.object({
  edit: z.object({
    action: z.enum([
      "create_entity",
      "update_entity",
      "delete_entity",
      "merge_entities",
      "create_relationship",
      "update_relationship",
      "delete_relationship",
      "bulk_update",
    ]),
    entity_data: z.record(z.any()).optional(),
    relationship_data: z.record(z.any()).optional(),
    bulk_data: z.array(z.record(z.any())).optional(),
    reason: z.string().min(1),
    validate_before_apply: z.boolean().default(true),
  }),
});

export const RollbackKGChangesSchema = z.object({
  rollback_info: z.record(z.any()),
});

export const AddQualityStepsToPipelineSchema = z.object({
  pipeline_id: z.string().uuid(),
  include_validation: z.boolean().default(true),
  include_conflict_detection: z.boolean().default(true),
  include_auto_resolution: z.boolean().default(false),
});
