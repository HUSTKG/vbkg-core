-- Additional tables to support enhanced pipeline functionality

-- Quality Assessments Table
CREATE TABLE IF NOT EXISTS "public"."pipeline_quality_assessments" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "pipeline_run_id" "uuid" REFERENCES "public"."pipeline_runs"("id") ON DELETE CASCADE,
    "step_id" "uuid" REFERENCES "public"."pipeline_steps"("id") ON DELETE CASCADE,
    "metric_name" "text" NOT NULL,
    "dimension" "text" NOT NULL CHECK ("dimension" IN ('accuracy', 'consistency', 'completeness', 'timeliness', 'trustworthiness', 'availability')),
    "score" decimal(5,4) NOT NULL CHECK ("score" >= 0 AND "score" <= 1),
    "level" "text" NOT NULL CHECK ("level" IN ('excellent', 'good', 'fair', 'poor', 'critical')),
    "details" "jsonb",
    "timestamp" timestamp with time zone NOT NULL,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    PRIMARY KEY ("id")
);

-- Pipeline Quality Reports Table
CREATE TABLE IF NOT EXISTS "public"."pipeline_quality_reports" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "pipeline_run_id" "uuid" REFERENCES "public"."pipeline_runs"("id") ON DELETE CASCADE,
    "overall_score" decimal(5,4) NOT NULL CHECK ("overall_score" >= 0 AND "overall_score" <= 1),
    "overall_level" "text" NOT NULL CHECK ("overall_level" IN ('excellent', 'good', 'fair', 'poor', 'critical')),
    "dimension_scores" "jsonb" NOT NULL,
    "recommendations" "jsonb",
    "step_count" integer NOT NULL DEFAULT 0,
    "assessment_count" integer NOT NULL DEFAULT 0,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    PRIMARY KEY ("id")
);

-- Incremental Checkpoints Table
CREATE TABLE IF NOT EXISTS "public"."incremental_checkpoints" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "step_id" "uuid" REFERENCES "public"."pipeline_steps"("id") ON DELETE CASCADE,
    "pipeline_id" "uuid" REFERENCES "public"."pipelines"("id") ON DELETE CASCADE,
    "strategy" "text" NOT NULL CHECK ("strategy" IN ('timestamp', 'sequence', 'hash', 'custom', 'file_modification', 'event_log')),
    "checkpoint_field" "text" NOT NULL,
    "checkpoint_value" "text",
    "last_processed" timestamp with time zone NOT NULL,
    "record_count" integer DEFAULT 0,
    "hash_value" "text",
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    PRIMARY KEY ("id"),
    UNIQUE ("step_id", "pipeline_id")
);

-- Change Records Table
CREATE TABLE IF NOT EXISTS "public"."change_records" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "change_id" "uuid" NOT NULL,
    "change_type" "text" NOT NULL CHECK ("change_type" IN ('insert', 'update', 'delete', 'move', 'modify')),
    "entity_id" "text",
    "field_name" "text",
    "old_value" "jsonb",
    "new_value" "jsonb",
    "timestamp" timestamp with time zone NOT NULL,
    "source" "text" NOT NULL,
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    PRIMARY KEY ("id")
);

-- Provenance Records Table
CREATE TABLE IF NOT EXISTS "public"."provenance_records" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "entity_id" "text" NOT NULL,
    "step_id" "uuid" REFERENCES "public"."pipeline_steps"("id") ON DELETE CASCADE,
    "pipeline_run_id" "uuid" REFERENCES "public"."pipeline_runs"("id") ON DELETE CASCADE,
    "source_system" "text" NOT NULL,
    "source_record_id" "text",
    "transformation_applied" "jsonb" NOT NULL,
    "quality_score" decimal(5,4) NOT NULL DEFAULT 0.8 CHECK ("quality_score" >= 0 AND "quality_score" <= 1),
    "confidence_score" decimal(5,4) NOT NULL DEFAULT 0.8 CHECK ("confidence_score" >= 0 AND "confidence_score" <= 1),
    "timestamp" timestamp with time zone NOT NULL,
    "lineage" "jsonb",
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    PRIMARY KEY ("id")
);

-- Pipeline Templates Table (for storing custom templates)
CREATE TABLE IF NOT EXISTS "public"."pipeline_templates" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" "text" NOT NULL,
    "description" "text",
    "source_type" "text" NOT NULL,
    "template_config" "jsonb" NOT NULL,
    "steps" "jsonb" NOT NULL,
    "complexity" "text" CHECK ("complexity" IN ('low', 'medium', 'high')),
    "quality_level" "text" CHECK ("quality_level" IN ('low', 'medium', 'high')),
    "estimated_duration" "text",
    "use_case" "text",
    "supports_incremental" boolean DEFAULT false,
    "created_by" "uuid",
    "is_public" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    PRIMARY KEY ("id")
);

-- Step Execution Logs Table (for detailed debugging)
CREATE TABLE IF NOT EXISTS "public"."step_execution_logs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "step_run_id" "uuid" REFERENCES "public"."pipeline_step_runs"("id") ON DELETE CASCADE,
    "log_level" "text" NOT NULL CHECK ("log_level" IN ('DEBUG', 'INFO', 'WARN', 'ERROR')),
    "message" "text" NOT NULL,
    "details" "jsonb",
    "timestamp" timestamp with time zone NOT NULL,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    PRIMARY KEY ("id")
);

-- Entity Clusters Table (for entity resolution results)
CREATE TABLE IF NOT EXISTS "public"."entity_clusters" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "cluster_id" "uuid" NOT NULL,
    "entity_ids" "jsonb" NOT NULL,
    "merged_entity" "jsonb" NOT NULL,
    "resolution_method" "text" NOT NULL,
    "confidence_score" decimal(5,4) DEFAULT 0.8 CHECK ("confidence_score" >= 0 AND "confidence_score" <= 1),
    "step_run_id" "uuid" REFERENCES "public"."pipeline_step_runs"("id"),
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    PRIMARY KEY ("id")
);

-- Pipeline Notifications Table (for alerts and notifications)
CREATE TABLE IF NOT EXISTS "public"."pipeline_notifications" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "pipeline_id" "uuid" REFERENCES "public"."pipelines"("id") ON DELETE CASCADE,
    "pipeline_run_id" "uuid" REFERENCES "public"."pipeline_runs"("id") ON DELETE CASCADE,
    "notification_type" "text" NOT NULL CHECK ("notification_type" IN ('success', 'failure', 'warning', 'quality_issue')),
    "title" "text" NOT NULL,
    "message" "text" NOT NULL,
    "details" "jsonb",
    "is_read" boolean DEFAULT false,
    "recipient_user_id" "uuid",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    PRIMARY KEY ("id")
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS "idx_quality_assessments_pipeline_run" ON "public"."pipeline_quality_assessments" ("pipeline_run_id");
CREATE INDEX IF NOT EXISTS "idx_quality_assessments_step" ON "public"."pipeline_quality_assessments" ("step_id");
CREATE INDEX IF NOT EXISTS "idx_quality_assessments_dimension" ON "public"."pipeline_quality_assessments" ("dimension");
CREATE INDEX IF NOT EXISTS "idx_quality_assessments_level" ON "public"."pipeline_quality_assessments" ("level");

CREATE INDEX IF NOT EXISTS "idx_pipeline_quality_reports_run" ON "public"."pipeline_quality_reports" ("pipeline_run_id");
CREATE INDEX IF NOT EXISTS "idx_pipeline_quality_reports_score" ON "public"."pipeline_quality_reports" ("overall_score");

CREATE INDEX IF NOT EXISTS "idx_incremental_checkpoints_step" ON "public"."incremental_checkpoints" ("step_id");
CREATE INDEX IF NOT EXISTS "idx_incremental_checkpoints_pipeline" ON "public"."incremental_checkpoints" ("pipeline_id");
CREATE INDEX IF NOT EXISTS "idx_incremental_checkpoints_strategy" ON "public"."incremental_checkpoints" ("strategy");

CREATE INDEX IF NOT EXISTS "idx_change_records_entity" ON "public"."change_records" ("entity_id");
CREATE INDEX IF NOT EXISTS "idx_change_records_timestamp" ON "public"."change_records" ("timestamp");
CREATE INDEX IF NOT EXISTS "idx_change_records_change_type" ON "public"."change_records" ("change_type");
CREATE INDEX IF NOT EXISTS "idx_change_records_source" ON "public"."change_records" ("source");

CREATE INDEX IF NOT EXISTS "idx_provenance_records_entity" ON "public"."provenance_records" ("entity_id");
CREATE INDEX IF NOT EXISTS "idx_provenance_records_step" ON "public"."provenance_records" ("step_id");
CREATE INDEX IF NOT EXISTS "idx_provenance_records_pipeline_run" ON "public"."provenance_records" ("pipeline_run_id");
CREATE INDEX IF NOT EXISTS "idx_provenance_records_source_system" ON "public"."provenance_records" ("source_system");

CREATE INDEX IF NOT EXISTS "idx_pipeline_templates_source_type" ON "public"."pipeline_templates" ("source_type");
CREATE INDEX IF NOT EXISTS "idx_pipeline_templates_complexity" ON "public"."pipeline_templates" ("complexity");
CREATE INDEX IF NOT EXISTS "idx_pipeline_templates_public" ON "public"."pipeline_templates" ("is_public");

CREATE INDEX IF NOT EXISTS "idx_step_execution_logs_step_run" ON "public"."step_execution_logs" ("step_run_id");
CREATE INDEX IF NOT EXISTS "idx_step_execution_logs_level" ON "public"."step_execution_logs" ("log_level");
CREATE INDEX IF NOT EXISTS "idx_step_execution_logs_timestamp" ON "public"."step_execution_logs" ("timestamp");



CREATE INDEX IF NOT EXISTS "idx_entity_clusters_cluster_id" ON "public"."entity_clusters" ("cluster_id");
CREATE INDEX IF NOT EXISTS "idx_entity_clusters_step_run" ON "public"."entity_clusters" ("step_run_id");
CREATE INDEX IF NOT EXISTS "idx_entity_clusters_method" ON "public"."entity_clusters" ("resolution_method");

CREATE INDEX IF NOT EXISTS "idx_pipeline_notifications_pipeline" ON "public"."pipeline_notifications" ("pipeline_id");
CREATE INDEX IF NOT EXISTS "idx_pipeline_notifications_run" ON "public"."pipeline_notifications" ("pipeline_run_id");
CREATE INDEX IF NOT EXISTS "idx_pipeline_notifications_type" ON "public"."pipeline_notifications" ("notification_type");
CREATE INDEX IF NOT EXISTS "idx_pipeline_notifications_recipient" ON "public"."pipeline_notifications" ("recipient_user_id");
CREATE INDEX IF NOT EXISTS "idx_pipeline_notifications_read" ON "public"."pipeline_notifications" ("is_read");

-- Create triggers for updating updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_incremental_checkpoints_updated_at 
    BEFORE UPDATE ON "public"."incremental_checkpoints"
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_pipeline_templates_updated_at 
    BEFORE UPDATE ON "public"."pipeline_templates"
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Add RLS (Row Level Security) policies if needed
-- ALTER TABLE "public"."quality_assessments" ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE "public"."pipeline_quality_reports" ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE "public"."incremental_checkpoints" ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE "public"."change_records" ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE "public"."provenance_records" ENABLE ROW LEVEL SECURITY;

-- Grant permissions to postgres user
ALTER TABLE "public"."pipeline_quality_assessments" OWNER TO "postgres";
ALTER TABLE "public"."pipeline_quality_reports" OWNER TO "postgres";
ALTER TABLE "public"."incremental_checkpoints" OWNER TO "postgres";
ALTER TABLE "public"."change_records" OWNER TO "postgres";
ALTER TABLE "public"."provenance_records" OWNER TO "postgres";
ALTER TABLE "public"."pipeline_templates" OWNER TO "postgres";
ALTER TABLE "public"."step_execution_logs" OWNER TO "postgres";
ALTER TABLE "public"."entity_clusters" OWNER TO "postgres";
ALTER TABLE "public"."pipeline_notifications" OWNER TO "postgres";

-- Add comments for documentation
COMMENT ON TABLE "public"."pipeline_quality_assessments" IS 'Quality assessment results for individual pipeline steps';
COMMENT ON TABLE "public"."pipeline_quality_reports" IS 'Overall quality reports for complete pipeline runs';
COMMENT ON TABLE "public"."incremental_checkpoints" IS 'Checkpoints for incremental data processing';
COMMENT ON TABLE "public"."change_records" IS 'Record of data changes for change tracking';
COMMENT ON TABLE "public"."provenance_records" IS 'Data provenance and lineage information';
COMMENT ON TABLE "public"."pipeline_templates" IS 'Reusable pipeline templates';
COMMENT ON TABLE "public"."step_execution_logs" IS 'Detailed execution logs for pipeline steps';
COMMENT ON TABLE "public"."entity_clusters" IS 'Entity resolution clusters';
COMMENT ON TABLE "public"."pipeline_notifications" IS 'Pipeline execution notifications and alerts';
