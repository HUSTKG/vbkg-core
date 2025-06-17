-- Drop existing entity_mappings table 
DROP TABLE IF EXISTS "public"."entity_mappings" CASCADE;

-- Create new entity_mappings table with ontology structure
CREATE TABLE "public"."entity_mappings" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "entity_type" "text",  -- Legacy field for backward compatibility
    "entity_type_id" integer,  -- FK to entity_types table
    "ontology_class_id" integer NOT NULL,  -- FK to ontology_classes
    "confidence" double precision DEFAULT 0.8,
    "is_verified" boolean DEFAULT false,
    "mapping_status" "text" DEFAULT 'pending'::text NOT NULL,
    "mapping_notes" "text",
    "auto_mapped" boolean DEFAULT false,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "reviewed_by" "uuid",
    "reviewed_at" timestamp with time zone,
    CONSTRAINT "entity_mappings_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "entity_mappings_confidence_check" CHECK ((("confidence" >= (0.0)::double precision) AND ("confidence" <= (1.0)::double precision))),
    CONSTRAINT "entity_mappings_mapping_status_check" CHECK (("mapping_status" = ANY (ARRAY['pending'::text, 'mapped'::text, 'rejected'::text, 'needs_review'::text]))),
    CONSTRAINT "entity_mappings_ontology_class_id_fkey" FOREIGN KEY ("ontology_class_id") REFERENCES "public"."ontology_classes"("id"),
    CONSTRAINT "entity_mappings_entity_type_id_fkey" FOREIGN KEY ("entity_type_id") REFERENCES "public"."entity_types"("id"),
    CONSTRAINT "entity_mappings_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id"),
    CONSTRAINT "entity_mappings_reviewed_by_fkey" FOREIGN KEY ("reviewed_by") REFERENCES "auth"."users"("id")
);

-- ============================================
-- 2. UPDATE EXISTING RELATIONSHIP_MAPPINGS TABLE
-- ============================================

-- Backup existing data if any
CREATE TABLE IF NOT EXISTS "public"."relationship_mappings_backup" AS 
SELECT * FROM "public"."relationship_mappings";

-- Drop existing relationship_mappings table
DROP TABLE IF EXISTS "public"."relationship_mappings" CASCADE;

-- Create new relationship_mappings table with ontology structure
CREATE TABLE "public"."relationship_mappings" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "relationship_type" "text",  -- Legacy field for backward compatibility  
    "relationship_type_id" integer,  -- FK to relationship_types table
    "ontology_property_id" integer NOT NULL,  -- FK to ontology_properties
    "confidence" double precision DEFAULT 0.8,
    "is_verified" boolean DEFAULT false,
    "mapping_status" "text" DEFAULT 'pending'::text NOT NULL,
    "mapping_notes" "text",
    "auto_mapped" boolean DEFAULT false,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "reviewed_by" "uuid",
    "reviewed_at" timestamp with time zone,
    CONSTRAINT "relationship_mappings_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "relationship_mappings_confidence_check" CHECK ((("confidence" >= (0.0)::double precision) AND ("confidence" <= (1.0)::double precision))),
    CONSTRAINT "relationship_mappings_mapping_status_check" CHECK (("mapping_status" = ANY (ARRAY['pending'::text, 'mapped'::text, 'rejected'::text, 'needs_review'::text]))),
    CONSTRAINT "relationship_mappings_ontology_property_id_fkey" FOREIGN KEY ("ontology_property_id") REFERENCES "public"."ontology_properties"("id"),
    CONSTRAINT "relationship_mappings_relationship_type_id_fkey" FOREIGN KEY ("relationship_type_id") REFERENCES "public"."relationship_types"("id"),
    CONSTRAINT "relationship_mappings_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id"),
    CONSTRAINT "relationship_mappings_reviewed_by_fkey" FOREIGN KEY ("reviewed_by") REFERENCES "auth"."users"("id")
);

-- ============================================
-- 3. ADD MISSING COLUMNS TO EXISTING TABLES
-- ============================================

-- Add missing columns to domains table
ALTER TABLE "public"."domains" 
ADD COLUMN IF NOT EXISTS "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"());

-- Add missing columns to entity_types table  
ALTER TABLE "public"."entity_types"
ADD COLUMN IF NOT EXISTS "is_mapped" boolean DEFAULT false;

-- Add missing columns to relationship_types table
ALTER TABLE "public"."relationship_types"
ADD COLUMN IF NOT EXISTS "color" "text",
ADD COLUMN IF NOT EXISTS "is_bidirectional" boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS "is_mapped" boolean DEFAULT false;

-- Add missing relationship_type_id column to kg_relationships if not exists
ALTER TABLE "public"."kg_relationships" 
ADD COLUMN IF NOT EXISTS "relationship_type_id" integer;

-- Add foreign key constraint for kg_relationships.relationship_type_id
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'kg_relationships_relationship_type_id_fkey') THEN
        ALTER TABLE ONLY "public"."kg_relationships" ADD CONSTRAINT "kg_relationships_relationship_type_id_fkey" 
        FOREIGN KEY ("relationship_type_id") REFERENCES "public"."relationship_types"("id");
    END IF;
END $$;

-- ============================================
-- 4. CREATE ONTOLOGY MAPPING SUGGESTIONS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS "public"."ontology_mapping_suggestions" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "domain" "text",
    "user_id" "uuid",
    "entity_suggestions" "jsonb" DEFAULT '[]'::jsonb,
    "relationship_suggestions" "jsonb" DEFAULT '[]'::jsonb,
    "saved_entity_mappings" integer DEFAULT 0,
    "saved_relationship_mappings" integer DEFAULT 0,
    "auto_applied" boolean DEFAULT false,
    "confidence_threshold" double precision DEFAULT 0.8,
    "status" "text" DEFAULT 'pending'::text,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "processed_at" timestamp with time zone,
    "error_message" "text",
    CONSTRAINT "ontology_mapping_suggestions_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "ontology_mapping_suggestions_status_check" CHECK (("status" = ANY (ARRAY['pending'::text, 'processed'::text, 'failed'::text]))),
    CONSTRAINT "ontology_mapping_suggestions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id")
);

-- ============================================
-- 5. CREATE ONTOLOGY ENRICHMENT LOGS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS "public"."ontology_enrichment_logs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "domain" "text",
    "enrichment_type" "text" NOT NULL, -- 'entity_mapping', 'relationship_mapping', 'ontology_extension', 'full_enrichment'
    "input_data" "jsonb",
    "output_data" "jsonb", 
    "statistics" "jsonb",
    "auto_applied" boolean DEFAULT false,
    "confidence_threshold" double precision,
    "execution_time_ms" integer,
    "status" "text" DEFAULT 'running'::text,
    "error_message" "text",
    "started_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "completed_at" timestamp with time zone,
    CONSTRAINT "ontology_enrichment_logs_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "ontology_enrichment_logs_enrichment_type_check" CHECK (("enrichment_type" = ANY (ARRAY['entity_mapping'::text, 'relationship_mapping'::text, 'ontology_extension'::text, 'full_enrichment'::text]))),
    CONSTRAINT "ontology_enrichment_logs_status_check" CHECK (("status" = ANY (ARRAY['running'::text, 'completed'::text, 'failed'::text]))),
    CONSTRAINT "ontology_enrichment_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id")
);

-- Entity mappings indexes
CREATE INDEX IF NOT EXISTS "idx_entity_mappings_entity_type" ON "public"."entity_mappings" USING "btree" ("entity_type");
CREATE INDEX IF NOT EXISTS "idx_entity_mappings_entity_type_id" ON "public"."entity_mappings" USING "btree" ("entity_type_id");
CREATE INDEX IF NOT EXISTS "idx_entity_mappings_ontology_class_id" ON "public"."entity_mappings" USING "btree" ("ontology_class_id");
CREATE INDEX IF NOT EXISTS "idx_entity_mappings_mapping_status" ON "public"."entity_mappings" USING "btree" ("mapping_status");
CREATE INDEX IF NOT EXISTS "idx_entity_mappings_is_verified" ON "public"."entity_mappings" USING "btree" ("is_verified");
CREATE INDEX IF NOT EXISTS "idx_entity_mappings_auto_mapped" ON "public"."entity_mappings" USING "btree" ("auto_mapped");
CREATE INDEX IF NOT EXISTS "idx_entity_mappings_created_by" ON "public"."entity_mappings" USING "btree" ("created_by");

-- Relationship mappings indexes
CREATE INDEX IF NOT EXISTS "idx_relationship_mappings_relationship_type" ON "public"."relationship_mappings" USING "btree" ("relationship_type");
CREATE INDEX IF NOT EXISTS "idx_relationship_mappings_relationship_type_id" ON "public"."relationship_mappings" USING "btree" ("relationship_type_id");
CREATE INDEX IF NOT EXISTS "idx_relationship_mappings_ontology_property_id" ON "public"."relationship_mappings" USING "btree" ("ontology_property_id");
CREATE INDEX IF NOT EXISTS "idx_relationship_mappings_mapping_status" ON "public"."relationship_mappings" USING "btree" ("mapping_status");
CREATE INDEX IF NOT EXISTS "idx_relationship_mappings_is_verified" ON "public"."relationship_mappings" USING "btree" ("is_verified");
CREATE INDEX IF NOT EXISTS "idx_relationship_mappings_auto_mapped" ON "public"."relationship_mappings" USING "btree" ("auto_mapped");
CREATE INDEX IF NOT EXISTS "idx_relationship_mappings_created_by" ON "public"."relationship_mappings" USING "btree" ("created_by");

-- Ontology mapping suggestions indexes
CREATE INDEX IF NOT EXISTS "idx_ontology_mapping_suggestions_domain" ON "public"."ontology_mapping_suggestions" USING "btree" ("domain");
CREATE INDEX IF NOT EXISTS "idx_ontology_mapping_suggestions_user_id" ON "public"."ontology_mapping_suggestions" USING "btree" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_ontology_mapping_suggestions_status" ON "public"."ontology_mapping_suggestions" USING "btree" ("status");
CREATE INDEX IF NOT EXISTS "idx_ontology_mapping_suggestions_created_at" ON "public"."ontology_mapping_suggestions" USING "btree" ("created_at");

-- Ontology enrichment logs indexes
CREATE INDEX IF NOT EXISTS "idx_ontology_enrichment_logs_user_id" ON "public"."ontology_enrichment_logs" USING "btree" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_ontology_enrichment_logs_domain" ON "public"."ontology_enrichment_logs" USING "btree" ("domain");
CREATE INDEX IF NOT EXISTS "idx_ontology_enrichment_logs_enrichment_type" ON "public"."ontology_enrichment_logs" USING "btree" ("enrichment_type");
CREATE INDEX IF NOT EXISTS "idx_ontology_enrichment_logs_status" ON "public"."ontology_enrichment_logs" USING "btree" ("status");
CREATE INDEX IF NOT EXISTS "idx_ontology_enrichment_logs_started_at" ON "public"."ontology_enrichment_logs" USING "btree" ("started_at");

-- Additional indexes for existing tables
CREATE INDEX IF NOT EXISTS "idx_entity_types_is_mapped" ON "public"."entity_types" USING "btree" ("is_mapped");
CREATE INDEX IF NOT EXISTS "idx_relationship_types_is_mapped" ON "public"."relationship_types" USING "btree" ("is_mapped");
CREATE INDEX IF NOT EXISTS "idx_kg_relationships_relationship_type_id" ON "public"."kg_relationships" USING "btree" ("relationship_type_id");

-- ============================================
-- 8. ADD UPDATE TIMESTAMP TRIGGERS
-- ============================================

-- Add triggers for new mapping tables
CREATE OR REPLACE TRIGGER "update_timestamp_entity_mappings" BEFORE UPDATE ON "public"."entity_mappings" 
FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();

CREATE OR REPLACE TRIGGER "update_timestamp_relationship_mappings" BEFORE UPDATE ON "public"."relationship_mappings" 
FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();

-- Grant permissions on tables
GRANT ALL ON TABLE "public"."domains" TO "anon";
GRANT ALL ON TABLE "public"."domains" TO "authenticated";
GRANT ALL ON TABLE "public"."domains" TO "service_role";

GRANT ALL ON TABLE "public"."entity_types" TO "anon";
GRANT ALL ON TABLE "public"."entity_types" TO "authenticated";
GRANT ALL ON TABLE "public"."entity_types" TO "service_role";

GRANT ALL ON TABLE "public"."relationship_types" TO "anon";
GRANT ALL ON TABLE "public"."relationship_types" TO "authenticated";
GRANT ALL ON TABLE "public"."relationship_types" TO "service_role";

GRANT ALL ON TABLE "public"."entity_type_domains" TO "anon";
GRANT ALL ON TABLE "public"."entity_type_domains" TO "authenticated";
GRANT ALL ON TABLE "public"."entity_type_domains" TO "service_role";

GRANT ALL ON TABLE "public"."relationship_type_domains" TO "anon";
GRANT ALL ON TABLE "public"."relationship_type_domains" TO "authenticated";
GRANT ALL ON TABLE "public"."relationship_type_domains" TO "service_role";

GRANT ALL ON TABLE "public"."entity_mappings" TO "anon";
GRANT ALL ON TABLE "public"."entity_mappings" TO "authenticated"; 
GRANT ALL ON TABLE "public"."entity_mappings" TO "service_role";

GRANT ALL ON TABLE "public"."relationship_mappings" TO "anon";
GRANT ALL ON TABLE "public"."relationship_mappings" TO "authenticated";
GRANT ALL ON TABLE "public"."relationship_mappings" TO "service_role";

GRANT ALL ON TABLE "public"."ontology_mapping_suggestions" TO "anon";
GRANT ALL ON TABLE "public"."ontology_mapping_suggestions" TO "authenticated";
GRANT ALL ON TABLE "public"."ontology_mapping_suggestions" TO "service_role";

GRANT ALL ON TABLE "public"."ontology_enrichment_logs" TO "anon";
GRANT ALL ON TABLE "public"."ontology_enrichment_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."ontology_enrichment_logs" TO "service_role";

-- Grant permissions on sequences
GRANT ALL ON SEQUENCE "public"."domains_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."domains_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."domains_id_seq" TO "service_role";

GRANT ALL ON SEQUENCE "public"."entity_types_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."entity_types_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."entity_types_id_seq" TO "service_role";

GRANT ALL ON SEQUENCE "public"."relationship_types_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."relationship_types_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."relationship_types_id_seq" TO "service_role";

GRANT ALL ON SEQUENCE "public"."entity_type_domains_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."entity_type_domains_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."entity_type_domains_id_seq" TO "service_role";

GRANT ALL ON SEQUENCE "public"."relationship_type_domains_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."relationship_type_domains_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."relationship_type_domains_id_seq" TO "service_role";

-- ============================================
-- 14. ENABLE RLS AND CREATE POLICIES
-- ============================================

-- Enable RLS policies
ALTER TABLE "public"."entity_mappings" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."relationship_mappings" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."ontology_mapping_suggestions" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."ontology_enrichment_logs" ENABLE ROW LEVEL SECURITY;

-- Create RLS policies only if they don't exist
DO $$ 
BEGIN
    -- Entity mappings policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'entity_mappings' AND policyname = 'Users can manage entity mappings') THEN
        CREATE POLICY "Users can manage entity mappings" ON "public"."entity_mappings" 
        USING ("public"."check_user_permission"("auth"."uid"(), 'ontology:write'::"text"));
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'entity_mappings' AND policyname = 'Users can view entity mappings') THEN
        CREATE POLICY "Users can view entity mappings" ON "public"."entity_mappings" FOR SELECT
        USING ("public"."check_user_permission"("auth"."uid"(), 'ontology:read'::"text"));
    END IF;

    -- Relationship mappings policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'relationship_mappings' AND policyname = 'Users can manage relationship mappings') THEN
        CREATE POLICY "Users can manage relationship mappings" ON "public"."relationship_mappings"
        USING ("public"."check_user_permission"("auth"."uid"(), 'ontology:write'::"text"));
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'relationship_mappings' AND policyname = 'Users can view relationship mappings') THEN
        CREATE POLICY "Users can view relationship mappings" ON "public"."relationship_mappings" FOR SELECT
        USING ("public"."check_user_permission"("auth"."uid"(), 'ontology:read'::"text"));
    END IF;

    -- Mapping suggestions policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'ontology_mapping_suggestions' AND policyname = 'Users can view their mapping suggestions') THEN
        CREATE POLICY "Users can view their mapping suggestions" ON "public"."ontology_mapping_suggestions" FOR SELECT
        USING (("auth"."uid"() = "user_id") OR "public"."check_user_permission"("auth"."uid"(), 'ontology:read'::"text"));
    END IF;

    -- Enrichment logs policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'ontology_enrichment_logs' AND policyname = 'Users can view their enrichment logs') THEN
        CREATE POLICY "Users can view their enrichment logs" ON "public"."ontology_enrichment_logs" FOR SELECT  
        USING (("auth"."uid"() = "user_id") OR "public"."check_user_permission"("auth"."uid"(), 'system:monitoring'::"text"));
    END IF;
END $$;

-- ============================================
-- 15. CREATE HELPER FUNCTIONS
-- ============================================

-- Function to get domain ID by name
CREATE OR REPLACE FUNCTION "public"."get_domain_id"("domain_name" "text") RETURNS integer
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    domain_id INTEGER;
BEGIN
    SELECT id INTO domain_id FROM public.domains WHERE name = domain_name AND is_active = TRUE;
    RETURN domain_id;
END;
$$;

-- Function to sync entity type mappings
CREATE OR REPLACE FUNCTION "public"."sync_entity_type_mapping"("p_entity_type" "text", "p_ontology_class_id" integer) RETURNS void
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
    -- Update kg_entities to mark as mapped
    UPDATE public.kg_entities 
    SET ontology_class_id = p_ontology_class_id 
    WHERE entity_type = p_entity_type;
    
    -- Update entity_types to mark as mapped
    UPDATE public.entity_types 
    SET is_mapped = TRUE 
    WHERE name = p_entity_type;
END;
$$;

-- Function to sync relationship type mappings
CREATE OR REPLACE FUNCTION "public"."sync_relationship_type_mapping"("p_relationship_type" "text", "p_ontology_property_id" integer) RETURNS void
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
    -- Update kg_relationships to mark as mapped
    UPDATE public.kg_relationships 
    SET ontology_property_id = p_ontology_property_id 
    WHERE relationship_type = p_relationship_type;
    
    -- Update relationship_types to mark as mapped
    UPDATE public.relationship_types 
    SET is_mapped = TRUE 
    WHERE name = p_relationship_type;
END;
$$;

-- Grant function permissions
GRANT ALL ON FUNCTION "public"."get_domain_id"("domain_name" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."get_domain_id"("domain_name" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_domain_id"("domain_name" "text") TO "service_role";

GRANT ALL ON FUNCTION "public"."sync_entity_type_mapping"("p_entity_type" "text", "p_ontology_class_id" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."sync_entity_type_mapping"("p_entity_type" "text", "p_ontology_class_id" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."sync_entity_type_mapping"("p_entity_type" "text", "p_ontology_class_id" integer) TO "service_role";

GRANT ALL ON FUNCTION "public"."sync_relationship_type_mapping"("p_relationship_type" "text", "p_ontology_property_id" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."sync_relationship_type_mapping"("p_relationship_type" "text", "p_ontology_property_id" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."sync_relationship_type_mapping"("p_relationship_type" "text", "p_ontology_property_id" integer) TO "service_role";

-- Migration completed successfully
SELECT 'Ontology mappings migration completed successfully!' as result;
