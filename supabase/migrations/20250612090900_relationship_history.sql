-- 1. Create Relationship History Table
CREATE TABLE IF NOT EXISTS "public"."relationship_history" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "relationship_id" "uuid" NOT NULL,
    "version_number" integer NOT NULL,
    "change_type" "text" NOT NULL,
    "old_values" "jsonb",
    "new_values" "jsonb" NOT NULL,
    "changed_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "relationship_history_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "relationship_history_change_type_check" CHECK (("change_type" = ANY (ARRAY['create'::"text", 'update'::"text", 'delete'::"text"])))
);

-- 2. Create Track Relationship Change Function
CREATE OR REPLACE FUNCTION "public"."track_relationship_change"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
  version_num INTEGER;
BEGIN
  -- Get next version number
  SELECT COALESCE(MAX(version_number), 0) + 1 INTO version_num
  FROM public.relationship_history
  WHERE relationship_id = NEW.id;
  
  -- Insert history record
  INSERT INTO public.relationship_history (
    relationship_id, version_number, change_type,
    old_values, new_values, changed_by
  ) VALUES (
    NEW.id, version_num,
    CASE WHEN TG_OP = 'INSERT' THEN 'create' ELSE 'update' END,
    CASE WHEN TG_OP = 'UPDATE' THEN row_to_json(OLD) ELSE NULL END,
    row_to_json(NEW),
    auth.uid()
  );
  
  RETURN NEW;
END;
$$;

-- 3. Create Track Relationship Delete Function
CREATE OR REPLACE FUNCTION "public"."track_relationship_delete"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
  version_num INTEGER;
BEGIN
  -- Get next version number
  SELECT COALESCE(MAX(version_number), 0) + 1 INTO version_num
  FROM public.relationship_history
  WHERE relationship_id = OLD.id;
  
  -- Insert delete history record
  INSERT INTO public.relationship_history (
    relationship_id, version_number, change_type,
    old_values, new_values, changed_by
  ) VALUES (
    OLD.id, version_num, 'delete',
    row_to_json(OLD),
    NULL,
    auth.uid()
  );
  
  RETURN OLD;
END;
$$;

-- 4. Add Foreign Key Constraints
ALTER TABLE ONLY "public"."relationship_history"
    ADD CONSTRAINT "relationship_history_relationship_id_fkey" 
    FOREIGN KEY ("relationship_id") REFERENCES "public"."kg_relationships"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."relationship_history"
    ADD CONSTRAINT "relationship_history_changed_by_fkey" 
    FOREIGN KEY ("changed_by") REFERENCES "auth"."users"("id");

-- 5. Add Indexes for Performance
CREATE INDEX IF NOT EXISTS "idx_relationship_history_relationship_id" 
    ON "public"."relationship_history" USING "btree" ("relationship_id");

CREATE INDEX IF NOT EXISTS "idx_relationship_history_version_number" 
    ON "public"."relationship_history" USING "btree" ("version_number");

CREATE INDEX IF NOT EXISTS "idx_relationship_history_change_type" 
    ON "public"."relationship_history" USING "btree" ("change_type");

CREATE INDEX IF NOT EXISTS "idx_relationship_history_created_at" 
    ON "public"."relationship_history" USING "btree" ("created_at");

-- 6. Drop Existing Relationship Change Trigger
DROP TRIGGER IF EXISTS "track_kg_relationship_changes" ON "public"."kg_relationships";

-- 7. Create New Relationship Change Triggers
CREATE OR REPLACE TRIGGER "track_kg_relationship_changes" 
    AFTER INSERT OR UPDATE ON "public"."kg_relationships" 
    FOR EACH ROW EXECUTE FUNCTION "public"."track_relationship_change"();

CREATE OR REPLACE TRIGGER "track_kg_relationship_deletes" 
    BEFORE DELETE ON "public"."kg_relationships" 
    FOR EACH ROW EXECUTE FUNCTION "public"."track_relationship_delete"();

-- 8. Grant Function Permissions
ALTER FUNCTION "public"."track_relationship_change"() OWNER TO "postgres";
ALTER FUNCTION "public"."track_relationship_delete"() OWNER TO "postgres";

GRANT ALL ON FUNCTION "public"."track_relationship_change"() TO "anon";
GRANT ALL ON FUNCTION "public"."track_relationship_change"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."track_relationship_change"() TO "service_role";

GRANT ALL ON FUNCTION "public"."track_relationship_delete"() TO "anon";
GRANT ALL ON FUNCTION "public"."track_relationship_delete"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."track_relationship_delete"() TO "service_role";

-- 9. Grant Table Permissions
GRANT ALL ON TABLE "public"."relationship_history" TO "anon";
GRANT ALL ON TABLE "public"."relationship_history" TO "authenticated";
GRANT ALL ON TABLE "public"."relationship_history" TO "service_role";

