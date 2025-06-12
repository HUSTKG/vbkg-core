-- Missing Tables Migration Script
-- These tables are referenced in functions but not defined in the schema

-- 1. Entity History Table (referenced in track_entity_change function)
CREATE TABLE IF NOT EXISTS "public"."entity_history" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "entity_id" "uuid" NOT NULL,
    "version_number" integer NOT NULL,
    "change_type" "text" NOT NULL,
    "old_values" "jsonb",
    "new_values" "jsonb" NOT NULL,
    "changed_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "entity_history_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "entity_history_change_type_check" CHECK (("change_type" = ANY (ARRAY['create'::"text", 'update'::"text", 'delete'::"text"])))
);

-- 2. Similarity Cache Table (referenced in compute_entity_similarity function)
CREATE TABLE IF NOT EXISTS "public"."similarity_cache" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "entity_id_1" "uuid" NOT NULL,
    "entity_id_2" "uuid" NOT NULL,
    "similarity_type" "text" NOT NULL DEFAULT 'cosine',
    "similarity_score" double precision NOT NULL,
    "expires_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "similarity_cache_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "similarity_cache_score_check" CHECK ((("similarity_score" >= (0)::double precision) AND ("similarity_score" <= (1)::double precision))),
    CONSTRAINT "similarity_cache_unique" UNIQUE ("entity_id_1", "entity_id_2", "similarity_type")
);

-- 3. Step Execution Cache Table (referenced in cleanup_expired_cache function)
CREATE TABLE IF NOT EXISTS "public"."step_execution_cache" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "step_id" "uuid" NOT NULL,
    "cache_key" "text" NOT NULL,
    "cached_data" "jsonb" NOT NULL,
    "expires_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "step_execution_cache_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "step_execution_cache_unique" UNIQUE ("step_id", "cache_key")
);

-- 4. Dependency Graph Table (referenced in build_dependency_graph function)
CREATE TABLE IF NOT EXISTS "public"."dependency_graph" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "source_entity_id" "uuid" NOT NULL,
    "dependent_entity_id" "uuid" NOT NULL,
    "dependent_entity_type" "text" NOT NULL,
    "dependency_type" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "dependency_graph_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "dependency_graph_unique" UNIQUE ("source_entity_id", "dependent_entity_id", "dependency_type")
);

-- 5. Domains Table (referenced in domain-related functions)
CREATE TABLE IF NOT EXISTS "public"."domains" (
    "id" integer NOT NULL,
    "name" "text" NOT NULL,
    "display_name" "text" NOT NULL,
    "description" "text",
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "domains_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "domains_name_unique" UNIQUE ("name")
);

CREATE SEQUENCE IF NOT EXISTS "public"."domains_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE "public"."domains_id_seq" OWNED BY "public"."domains"."id";
ALTER TABLE ONLY "public"."domains" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."domains_id_seq"'::"regclass");

-- 6. Entity Types Table (referenced in type-related functions)
CREATE TABLE IF NOT EXISTS "public"."entity_types" (
    "id" integer NOT NULL,
    "name" "text" NOT NULL,
    "display_name" "text" NOT NULL,
    "description" "text",
    "color" "text",
    "icon" "text",
    "extraction_pattern" "text",
    "validation_rules" "jsonb",
    "examples" "jsonb",
    "is_active" boolean DEFAULT true,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "entity_types_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "entity_types_name_unique" UNIQUE ("name")
);

CREATE SEQUENCE IF NOT EXISTS "public"."entity_types_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE "public"."entity_types_id_seq" OWNED BY "public"."entity_types"."id";
ALTER TABLE ONLY "public"."entity_types" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."entity_types_id_seq"'::"regclass");

-- 7. Entity Type Domains Junction Table
CREATE TABLE IF NOT EXISTS "public"."entity_type_domains" (
    "id" integer NOT NULL,
    "entity_type_id" integer NOT NULL,
    "domain_id" integer NOT NULL,
    "is_primary" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "entity_type_domains_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "entity_type_domains_unique" UNIQUE ("entity_type_id", "domain_id")
);

CREATE SEQUENCE IF NOT EXISTS "public"."entity_type_domains_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE "public"."entity_type_domains_id_seq" OWNED BY "public"."entity_type_domains"."id";
ALTER TABLE ONLY "public"."entity_type_domains" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."entity_type_domains_id_seq"'::"regclass");

-- 8. Relationship Types Table
CREATE TABLE IF NOT EXISTS "public"."relationship_types" (
    "id" integer NOT NULL,
    "name" "text" NOT NULL,
    "display_name" "text" NOT NULL,
    "description" "text",
    "source_entity_types" integer[],
    "target_entity_types" integer[],
    "is_active" boolean DEFAULT true,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "relationship_types_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "relationship_types_name_unique" UNIQUE ("name")
);

CREATE SEQUENCE IF NOT EXISTS "public"."relationship_types_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE "public"."relationship_types_id_seq" OWNED BY "public"."relationship_types"."id";
ALTER TABLE ONLY "public"."relationship_types" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."relationship_types_id_seq"'::"regclass");

-- 9. Relationship Type Domains Junction Table
CREATE TABLE IF NOT EXISTS "public"."relationship_type_domains" (
    "id" integer NOT NULL,
    "relationship_type_id" integer NOT NULL,
    "domain_id" integer NOT NULL,
    "is_primary" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "relationship_type_domains_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "relationship_type_domains_unique" UNIQUE ("relationship_type_id", "domain_id")
);

CREATE SEQUENCE IF NOT EXISTS "public"."relationship_type_domains_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE "public"."relationship_type_domains_id_seq" OWNED BY "public"."relationship_type_domains"."id";
ALTER TABLE ONLY "public"."relationship_type_domains" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."relationship_type_domains_id_seq"'::"regclass");

-- 10. Validation Rules Table (referenced in validation functions)
CREATE TABLE IF NOT EXISTS "public"."validation_rules" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" "text" NOT NULL,
    "description" "text",
    "rule_type" "text" NOT NULL,
    "rule_config" "jsonb" NOT NULL,
    "severity" "text" NOT NULL DEFAULT 'medium',
    "is_active" boolean DEFAULT true,
    "execution_count" integer DEFAULT 0,
    "violation_count" integer DEFAULT 0,
    "success_rate" double precision DEFAULT 1.0,
    "last_executed_at" timestamp with time zone,
    "average_execution_time" double precision,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "validation_rules_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "validation_rules_severity_check" CHECK (("severity" = ANY (ARRAY['low'::"text", 'medium'::"text", 'high'::"text", 'critical'::"text"]))),
    CONSTRAINT "validation_rules_rule_type_check" CHECK (("rule_type" = ANY (ARRAY['schema'::"text", 'business'::"text", 'consistency'::"text", 'completeness'::"text"])))
);

-- 11. Validation Rule Executions Table
CREATE TABLE IF NOT EXISTS "public"."validation_rule_executions" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "rule_id" "uuid" NOT NULL,
    "status" "text" NOT NULL,
    "start_time" timestamp with time zone NOT NULL,
    "end_time" timestamp with time zone,
    "execution_time" double precision,
    "entities_checked" integer DEFAULT 0,
    "relationships_checked" integer DEFAULT 0,
    "violations_found" integer DEFAULT 0,
    "error_message" "text",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "validation_rule_executions_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "validation_rule_executions_status_check" CHECK (("status" = ANY (ARRAY['running'::"text", 'completed'::"text", 'failed'::"text"])))
);

-- 12. Validation Violations Table
CREATE TABLE IF NOT EXISTS "public"."validation_violations" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "rule_id" "uuid" NOT NULL,
    "execution_id" "uuid",
    "entity_id" "uuid",
    "relationship_id" "uuid",
    "violation_type" "text" NOT NULL,
    "severity" "text" NOT NULL,
    "message" "text" NOT NULL,
    "details" "jsonb",
    "status" "text" DEFAULT 'open',
    "resolved_by" "uuid",
    "resolved_at" timestamp with time zone,
    "resolution_notes" "text",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "validation_violations_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "validation_violations_severity_check" CHECK (("severity" = ANY (ARRAY['low'::"text", 'medium'::"text", 'high'::"text", 'critical'::"text"]))),
    CONSTRAINT "validation_violations_status_check" CHECK (("status" = ANY (ARRAY['open'::"text", 'acknowledged'::"text", 'resolved'::"text", 'ignored'::"text"])))
);

-- 13. Entity Mappings Table (referenced in migration functions)
CREATE TABLE IF NOT EXISTS "public"."entity_mappings" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "entity_type" "text",
    "entity_type_id" integer,
    "source_id" "text",
    "target_entity_id" "uuid",
    "mapping_config" "jsonb",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "entity_mappings_pkey" PRIMARY KEY ("id")
);

-- 14. Relationship Mappings Table (referenced in migration functions)
CREATE TABLE IF NOT EXISTS "public"."relationship_mappings" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "relationship_type" "text",
    "relationship_type_id" integer,
    "source_id" "text",
    "target_relationship_id" "uuid",
    "mapping_config" "jsonb",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "relationship_mappings_pkey" PRIMARY KEY ("id")
);

-- Add Foreign Key Constraints
ALTER TABLE ONLY "public"."entity_history"
    ADD CONSTRAINT "entity_history_entity_id_fkey" FOREIGN KEY ("entity_id") REFERENCES "public"."kg_entities"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."entity_history"
    ADD CONSTRAINT "entity_history_changed_by_fkey" FOREIGN KEY ("changed_by") REFERENCES "auth"."users"("id");

ALTER TABLE ONLY "public"."similarity_cache"
    ADD CONSTRAINT "similarity_cache_entity_id_1_fkey" FOREIGN KEY ("entity_id_1") REFERENCES "public"."kg_entities"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."similarity_cache"
    ADD CONSTRAINT "similarity_cache_entity_id_2_fkey" FOREIGN KEY ("entity_id_2") REFERENCES "public"."kg_entities"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."step_execution_cache"
    ADD CONSTRAINT "step_execution_cache_step_id_fkey" FOREIGN KEY ("step_id") REFERENCES "public"."pipeline_steps"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."dependency_graph"
    ADD CONSTRAINT "dependency_graph_source_entity_id_fkey" FOREIGN KEY ("source_entity_id") REFERENCES "public"."kg_entities"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."dependency_graph"
    ADD CONSTRAINT "dependency_graph_dependent_entity_id_fkey" FOREIGN KEY ("dependent_entity_id") REFERENCES "public"."kg_entities"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."entity_types"
    ADD CONSTRAINT "entity_types_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");

ALTER TABLE ONLY "public"."entity_type_domains"
    ADD CONSTRAINT "entity_type_domains_entity_type_id_fkey" FOREIGN KEY ("entity_type_id") REFERENCES "public"."entity_types"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."entity_type_domains"
    ADD CONSTRAINT "entity_type_domains_domain_id_fkey" FOREIGN KEY ("domain_id") REFERENCES "public"."domains"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."relationship_types"
    ADD CONSTRAINT "relationship_types_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");

ALTER TABLE ONLY "public"."relationship_type_domains"
    ADD CONSTRAINT "relationship_type_domains_relationship_type_id_fkey" FOREIGN KEY ("relationship_type_id") REFERENCES "public"."relationship_types"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."relationship_type_domains"
    ADD CONSTRAINT "relationship_type_domains_domain_id_fkey" FOREIGN KEY ("domain_id") REFERENCES "public"."domains"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."validation_rules"
    ADD CONSTRAINT "validation_rules_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");

ALTER TABLE ONLY "public"."validation_rule_executions"
    ADD CONSTRAINT "validation_rule_executions_rule_id_fkey" FOREIGN KEY ("rule_id") REFERENCES "public"."validation_rules"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."validation_violations"
    ADD CONSTRAINT "validation_violations_rule_id_fkey" FOREIGN KEY ("rule_id") REFERENCES "public"."validation_rules"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."validation_violations"
    ADD CONSTRAINT "validation_violations_execution_id_fkey" FOREIGN KEY ("execution_id") REFERENCES "public"."validation_rule_executions"("id") ON DELETE SET NULL;

ALTER TABLE ONLY "public"."validation_violations"
    ADD CONSTRAINT "validation_violations_entity_id_fkey" FOREIGN KEY ("entity_id") REFERENCES "public"."kg_entities"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."validation_violations"
    ADD CONSTRAINT "validation_violations_relationship_id_fkey" FOREIGN KEY ("relationship_id") REFERENCES "public"."kg_relationships"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."validation_violations"
    ADD CONSTRAINT "validation_violations_resolved_by_fkey" FOREIGN KEY ("resolved_by") REFERENCES "auth"."users"("id");

ALTER TABLE ONLY "public"."entity_mappings"
    ADD CONSTRAINT "entity_mappings_entity_type_id_fkey" FOREIGN KEY ("entity_type_id") REFERENCES "public"."entity_types"("id");

ALTER TABLE ONLY "public"."entity_mappings"
    ADD CONSTRAINT "entity_mappings_target_entity_id_fkey" FOREIGN KEY ("target_entity_id") REFERENCES "public"."kg_entities"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."relationship_mappings"
    ADD CONSTRAINT "relationship_mappings_relationship_type_id_fkey" FOREIGN KEY ("relationship_type_id") REFERENCES "public"."relationship_types"("id");

ALTER TABLE ONLY "public"."relationship_mappings"
    ADD CONSTRAINT "relationship_mappings_target_relationship_id_fkey" FOREIGN KEY ("target_relationship_id") REFERENCES "public"."kg_relationships"("id") ON DELETE CASCADE;

-- Add missing columns to existing tables
ALTER TABLE "public"."kg_entities" 
ADD COLUMN IF NOT EXISTS "entity_type" "text",
ADD COLUMN IF NOT EXISTS "entity_type_id" integer;

ALTER TABLE "public"."kg_relationships" 
ADD COLUMN IF NOT EXISTS "relationship_type" "text";

-- Add foreign key constraints for the new columns
ALTER TABLE ONLY "public"."kg_entities"
    ADD CONSTRAINT "kg_entities_entity_type_id_fkey" FOREIGN KEY ("entity_type_id") REFERENCES "public"."entity_types"("id");

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS "idx_entity_history_entity_id" ON "public"."entity_history" USING "btree" ("entity_id");
CREATE INDEX IF NOT EXISTS "idx_entity_history_version_number" ON "public"."entity_history" USING "btree" ("version_number");
CREATE INDEX IF NOT EXISTS "idx_similarity_cache_entities" ON "public"."similarity_cache" USING "btree" ("entity_id_1", "entity_id_2");
CREATE INDEX IF NOT EXISTS "idx_similarity_cache_expires_at" ON "public"."similarity_cache" USING "btree" ("expires_at");
CREATE INDEX IF NOT EXISTS "idx_step_execution_cache_expires_at" ON "public"."step_execution_cache" USING "btree" ("expires_at");
CREATE INDEX IF NOT EXISTS "idx_dependency_graph_source" ON "public"."dependency_graph" USING "btree" ("source_entity_id");
CREATE INDEX IF NOT EXISTS "idx_dependency_graph_dependent" ON "public"."dependency_graph" USING "btree" ("dependent_entity_id");
CREATE INDEX IF NOT EXISTS "idx_validation_rules_is_active" ON "public"."validation_rules" USING "btree" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_validation_rule_executions_rule_id" ON "public"."validation_rule_executions" USING "btree" ("rule_id");
CREATE INDEX IF NOT EXISTS "idx_validation_violations_rule_id" ON "public"."validation_violations" USING "btree" ("rule_id");
CREATE INDEX IF NOT EXISTS "idx_validation_violations_status" ON "public"."validation_violations" USING "btree" ("status");
CREATE INDEX IF NOT EXISTS "idx_validation_violations_severity" ON "public"."validation_violations" USING "btree" ("severity");
CREATE INDEX IF NOT EXISTS "idx_kg_entities_entity_type_id" ON "public"."kg_entities" USING "btree" ("entity_type_id");

-- Add triggers for update timestamps
CREATE OR REPLACE TRIGGER "update_timestamp" BEFORE UPDATE ON "public"."domains" FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();
CREATE OR REPLACE TRIGGER "update_timestamp" BEFORE UPDATE ON "public"."entity_types" FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();
CREATE OR REPLACE TRIGGER "update_timestamp" BEFORE UPDATE ON "public"."relationship_types" FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();
CREATE OR REPLACE TRIGGER "update_timestamp" BEFORE UPDATE ON "public"."validation_rules" FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();

-- Add trigger for updating rule statistics
CREATE OR REPLACE TRIGGER "update_validation_rule_statistics" AFTER INSERT ON "public"."validation_rule_executions" FOR EACH ROW EXECUTE FUNCTION "public"."update_rule_statistics"();

-- Insert default domain
INSERT INTO "public"."domains" ("name", "display_name", "description") 
VALUES ('general', 'General', 'General domain for entities and relationships')
ON CONFLICT ("name") DO NOTHING;

-- Grant permissions
GRANT ALL ON TABLE "public"."entity_history" TO "anon";
GRANT ALL ON TABLE "public"."entity_history" TO "authenticated";
GRANT ALL ON TABLE "public"."entity_history" TO "service_role";

GRANT ALL ON TABLE "public"."similarity_cache" TO "anon";
GRANT ALL ON TABLE "public"."similarity_cache" TO "authenticated";
GRANT ALL ON TABLE "public"."similarity_cache" TO "service_role";

GRANT ALL ON TABLE "public"."step_execution_cache" TO "anon";
GRANT ALL ON TABLE "public"."step_execution_cache" TO "authenticated";
GRANT ALL ON TABLE "public"."step_execution_cache" TO "service_role";

GRANT ALL ON TABLE "public"."dependency_graph" TO "anon";
GRANT ALL ON TABLE "public"."dependency_graph" TO "authenticated";
GRANT ALL ON TABLE "public"."dependency_graph" TO "service_role";

GRANT ALL ON TABLE "public"."domains" TO "anon";
GRANT ALL ON TABLE "public"."domains" TO "authenticated";
GRANT ALL ON TABLE "public"."domains" TO "service_role";

GRANT ALL ON TABLE "public"."entity_types" TO "anon";
GRANT ALL ON TABLE "public"."entity_types" TO "authenticated";
GRANT ALL ON TABLE "public"."entity_types" TO "service_role";

GRANT ALL ON TABLE "public"."entity_type_domains" TO "anon";
GRANT ALL ON TABLE "public"."entity_type_domains" TO "authenticated";
GRANT ALL ON TABLE "public"."entity_type_domains" TO "service_role";

GRANT ALL ON TABLE "public"."relationship_types" TO "anon";
GRANT ALL ON TABLE "public"."relationship_types" TO "authenticated";
GRANT ALL ON TABLE "public"."relationship_types" TO "service_role";

GRANT ALL ON TABLE "public"."relationship_type_domains" TO "anon";
GRANT ALL ON TABLE "public"."relationship_type_domains" TO "authenticated";
GRANT ALL ON TABLE "public"."relationship_type_domains" TO "service_role";

GRANT ALL ON TABLE "public"."validation_rules" TO "anon";
GRANT ALL ON TABLE "public"."validation_rules" TO "authenticated";
GRANT ALL ON TABLE "public"."validation_rules" TO "service_role";

GRANT ALL ON TABLE "public"."validation_rule_executions" TO "anon";
GRANT ALL ON TABLE "public"."validation_rule_executions" TO "authenticated";
GRANT ALL ON TABLE "public"."validation_rule_executions" TO "service_role";

GRANT ALL ON TABLE "public"."validation_violations" TO "anon";
GRANT ALL ON TABLE "public"."validation_violations" TO "authenticated";
GRANT ALL ON TABLE "public"."validation_violations" TO "service_role";

GRANT ALL ON TABLE "public"."entity_mappings" TO "anon";
GRANT ALL ON TABLE "public"."entity_mappings" TO "authenticated";
GRANT ALL ON TABLE "public"."entity_mappings" TO "service_role";

GRANT ALL ON TABLE "public"."relationship_mappings" TO "anon";
GRANT ALL ON TABLE "public"."relationship_mappings" TO "authenticated";
GRANT ALL ON TABLE "public"."relationship_mappings" TO "service_role";

-- Grant sequence permissions
GRANT ALL ON SEQUENCE "public"."domains_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."domains_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."domains_id_seq" TO "service_role";

GRANT ALL ON SEQUENCE "public"."entity_types_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."entity_types_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."entity_types_id_seq" TO "service_role";

GRANT ALL ON SEQUENCE "public"."entity_type_domains_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."entity_type_domains_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."entity_type_domains_id_seq" TO "service_role";

GRANT ALL ON SEQUENCE "public"."relationship_types_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."relationship_types_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."relationship_types_id_seq" TO "service_role";

GRANT ALL ON SEQUENCE "public"."relationship_type_domains_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."relationship_type_domains_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."relationship_type_domains_id_seq" TO "service_role";
