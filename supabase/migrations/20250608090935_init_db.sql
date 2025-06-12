

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE EXTENSION IF NOT EXISTS "pg_net" WITH SCHEMA "extensions";






COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pg_trgm" WITH SCHEMA "public";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgjwt" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "vector" WITH SCHEMA "public";






CREATE OR REPLACE FUNCTION "public"."build_dependency_graph"("entity_id" "uuid", "max_depth" integer DEFAULT 3) RETURNS TABLE("level" integer, "dependent_id" "uuid", "dependent_type" "text", "dependency_type" "text")
    LANGUAGE "sql"
    AS $$
WITH RECURSIVE deps AS (
  -- Base case
  SELECT 
    0 as level,
    source_entity_id,
    dependent_entity_id,
    dependent_entity_type,
    dependency_type
  FROM public.dependency_graph
  WHERE source_entity_id = entity_id
  
  UNION ALL
  
  -- Recursive case
  SELECT 
    d.level + 1,
    dg.source_entity_id,
    dg.dependent_entity_id,
    dg.dependent_entity_type,
    dg.dependency_type
  FROM public.dependency_graph dg
  JOIN deps d ON dg.source_entity_id = d.dependent_entity_id
  WHERE d.level < max_depth - 1
)
SELECT DISTINCT
  level,
  dependent_entity_id as dependent_id,
  dependent_entity_type as dependent_type,
  dependency_type
FROM deps
ORDER BY level, dependent_id;
$$;


ALTER FUNCTION "public"."build_dependency_graph"("entity_id" "uuid", "max_depth" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."check_user_permission"("user_id" "uuid", "permission_name" "text") RETURNS boolean
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
  has_permission BOOLEAN;
BEGIN
  SELECT EXISTS (
    SELECT 1 FROM public.user_roles ur
    JOIN public.role_permissions rp ON ur.role_id = rp.role_id
    JOIN public.permissions p ON rp.permission_id = p.id
    WHERE ur.user_id = check_user_permission.user_id AND p.name = permission_name
  ) INTO has_permission;
  
  RETURN has_permission;
END;
$$;


ALTER FUNCTION "public"."check_user_permission"("user_id" "uuid", "permission_name" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."cleanup_expired_cache"() RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
  -- Clean similarity cache
  DELETE FROM public.similarity_cache 
  WHERE expires_at < NOW();
  
  -- Clean step execution cache
  DELETE FROM public.step_execution_cache
  WHERE expires_at < NOW();
  
  -- Log cleanup
  RAISE NOTICE 'Cache cleanup completed at %', NOW();
END;
$$;


ALTER FUNCTION "public"."cleanup_expired_cache"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."cleanup_old_logs"("days_to_keep" integer DEFAULT 90) RETURNS integer
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Cleanup user activity log
    DELETE FROM public.user_activity_log 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Cleanup API usage log
    DELETE FROM public.api_usage_log 
    WHERE timestamp < NOW() - INTERVAL '1 day' * days_to_keep;
    
    RETURN deleted_count;
END;
$$;


ALTER FUNCTION "public"."cleanup_old_logs"("days_to_keep" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."compute_entity_similarity"("entity1_id" "uuid", "entity2_id" "uuid", "similarity_type" "text" DEFAULT 'cosine'::"text") RETURNS double precision
    LANGUAGE "plpgsql"
    AS $$
DECLARE
  cached_score FLOAT;
  computed_score FLOAT;
BEGIN
  -- Check cache first
  SELECT similarity_score INTO cached_score
  FROM public.similarity_cache
  WHERE (entity_id_1 = entity1_id AND entity_id_2 = entity2_id)
     OR (entity_id_1 = entity2_id AND entity_id_2 = entity1_id)
    AND similarity_type = compute_entity_similarity.similarity_type
    AND (expires_at IS NULL OR expires_at > NOW());
  
  IF cached_score IS NOT NULL THEN
    RETURN cached_score;
  END IF;
  
  -- Compute similarity (simplified - implement actual logic)
  computed_score := 0.5; -- Placeholder
  
  -- Cache result
  INSERT INTO public.similarity_cache (
    entity_id_1, entity_id_2, similarity_type, similarity_score,
    expires_at
  ) VALUES (
    entity1_id, entity2_id, similarity_type, computed_score,
    NOW() + INTERVAL '7 days'
  ) ON CONFLICT DO NOTHING;
  
  RETURN computed_score;
END;
$$;


ALTER FUNCTION "public"."compute_entity_similarity"("entity1_id" "uuid", "entity2_id" "uuid", "similarity_type" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."decrypt_data_source_credentials"("p_id" "uuid", "p_encryption_key" "text") RETURNS "jsonb"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$DECLARE
  v_result JSONB;
  v_encrypted_data BYTEA;
BEGIN
  -- Chỉ cho phép lấy dữ liệu của user hiện tại
  SELECT encrypted_credentials INTO v_encrypted_data
  FROM data_sources as ds
  WHERE ds.id = p_id;
  
  IF v_encrypted_data IS NULL THEN
    RAISE EXCEPTION 'Data source not found or permission denied';
  END IF;
  
  -- Giải mã và trả về JSONB
  v_result := pgp_sym_decrypt(v_encrypted_data, p_encryption_key)::JSONB;
  RETURN v_result;
EXCEPTION
  WHEN OTHERS THEN
    RAISE EXCEPTION 'Decryption failed: %', SQLERRM;
END;$$;


ALTER FUNCTION "public"."decrypt_data_source_credentials"("p_id" "uuid", "p_encryption_key" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."encrypt_data_source_credentials"("p_credentials" "jsonb", "p_encryption_key" "text") RETURNS "bytea"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
  RETURN pgp_sym_encrypt(p_credentials::TEXT, p_encryption_key);
END;
$$;


ALTER FUNCTION "public"."encrypt_data_source_credentials"("p_credentials" "jsonb", "p_encryption_key" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."exec_sql"("sql_query" "text", "query_params" "json" DEFAULT '[]'::"json") RETURNS "json"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
  result_json JSON;
  execution_start TIMESTAMP;
  execution_end TIMESTAMP;
  execution_time NUMERIC;
  affected_rows INTEGER DEFAULT 0;
  result_data JSON DEFAULT '[]'::json;
  error_message TEXT;
  query_type TEXT;
BEGIN
  -- Record start time
  execution_start := clock_timestamp();
  
  -- Log the query for debugging (remove in production)
  RAISE NOTICE 'Executing SQL: %', sql_query;
  RAISE NOTICE 'With params: %', query_params;
  
  -- Determine query type
  query_type := UPPER(SPLIT_PART(TRIM(sql_query), ' ', 1));
  
  BEGIN
    -- Handle different query types
    IF query_type IN ('SELECT', 'WITH') THEN
      -- For SELECT queries, return data
      EXECUTE format('
        SELECT COALESCE(json_agg(row_to_json(t)), ''[]''::json)
        FROM (%s) t
      ', sql_query) 
      INTO result_data;
      
      -- Count rows
      GET DIAGNOSTICS affected_rows = ROW_COUNT;
      
    ELSIF query_type IN ('INSERT', 'UPDATE', 'DELETE') THEN
      -- For DML queries, execute and get affected rows
      EXECUTE sql_query;
      GET DIAGNOSTICS affected_rows = ROW_COUNT;
      result_data := '[]'::json;
      
    ELSIF query_type IN ('CREATE', 'DROP', 'ALTER', 'TRUNCATE') THEN
      -- For DDL queries
      EXECUTE sql_query;
      affected_rows := 0;
      result_data := '[]'::json;
      
    ELSE
      -- For other queries
      EXECUTE sql_query;
      GET DIAGNOSTICS affected_rows = ROW_COUNT;
      result_data := '[]'::json;
    END IF;
    
    -- Calculate execution time
    execution_end := clock_timestamp();
    execution_time := EXTRACT(MILLISECONDS FROM execution_end - execution_start);
    
    -- Build success response
    result_json := json_build_object(
      'success', true,
      'data', result_data,
      'affected_rows', affected_rows,
      'execution_time_ms', execution_time,
      'query_type', query_type,
      'timestamp', execution_end
    );
    
  EXCEPTION WHEN OTHERS THEN
    -- Calculate execution time even on error
    execution_end := clock_timestamp();
    execution_time := EXTRACT(MILLISECONDS FROM execution_end - execution_start);
    
    -- Get error details
    GET STACKED DIAGNOSTICS error_message = MESSAGE_TEXT;
    
    -- Build error response
    result_json := json_build_object(
      'success', false,
      'error', error_message,
      'affected_rows', 0,
      'execution_time_ms', execution_time,
      'query_type', query_type,
      'timestamp', execution_end
    );
    
    -- Log error for debugging
    RAISE NOTICE 'SQL Error: %', error_message;
  END;
  
  RETURN result_json;
END;
$$;


ALTER FUNCTION "public"."exec_sql"("sql_query" "text", "query_params" "json") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_domain_entity_types"("domain_name" "text") RETURNS TABLE("id" integer, "name" "text", "display_name" "text", "description" "text", "color" "text", "icon" "text", "extraction_pattern" "text", "validation_rules" "jsonb", "examples" "jsonb", "is_active" boolean, "created_by" "uuid", "created_at" timestamp with time zone, "updated_at" timestamp with time zone, "is_primary" boolean)
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
  RETURN QUERY
  SELECT et.*, etd.is_primary
  FROM public.entity_types et
  JOIN public.entity_type_domains etd ON et.id = etd.entity_type_id
  JOIN public.domains d ON etd.domain_id = d.id
  WHERE d.name = domain_name AND et.is_active = TRUE;
END;
$$;


ALTER FUNCTION "public"."get_domain_entity_types"("domain_name" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_domain_relationship_types"("domain_name" "text") RETURNS TABLE("id" integer, "name" "text", "display_name" "text", "is_primary" boolean)
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
  RETURN QUERY
  SELECT rt.id, rt.name, rt.display_name, rtd.is_primary
  FROM public.relationship_types rt
  JOIN public.relationship_type_domains rtd ON rt.id = rtd.relationship_type_id  
  JOIN public.domains d ON rtd.domain_id = d.id
  WHERE d.name = domain_name AND rt.is_active = TRUE;
END;
$$;


ALTER FUNCTION "public"."get_domain_relationship_types"("domain_name" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_entity_type_id"("type_name" "text", "domain_name" "text" DEFAULT NULL::"text") RETURNS integer
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
  type_id INTEGER;
BEGIN
  IF domain_name IS NULL THEN
    SELECT id INTO type_id FROM public.entity_types WHERE name = type_name AND is_active = TRUE;
  ELSE
    SELECT et.id INTO type_id 
    FROM public.entity_types et
    JOIN public.entity_type_domains etd ON et.id = etd.entity_type_id
    JOIN public.domains d ON etd.domain_id = d.id
    WHERE et.name = type_name AND et.is_active = TRUE AND d.name = domain_name;
  END IF;
  RETURN type_id;
END;
$$;


ALTER FUNCTION "public"."get_entity_type_id"("type_name" "text", "domain_name" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_relationship_type_id"("type_name" "text", "domain_name" "text" DEFAULT NULL::"text") RETURNS integer
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
  type_id INTEGER;
BEGIN
  IF domain_name IS NULL THEN
    SELECT id INTO type_id FROM public.relationship_types WHERE name = type_name AND is_active = TRUE;
  ELSE
    SELECT rt.id INTO type_id
    FROM public.relationship_types rt
    JOIN public.relationship_type_domains rtd ON rt.id = rtd.relationship_type_id
    JOIN public.domains d ON rtd.domain_id = d.id
    WHERE rt.name = type_name AND rt.is_active = TRUE AND d.name = domain_name;
  END IF;
  RETURN type_id;
END;
$$;


ALTER FUNCTION "public"."get_relationship_type_id"("type_name" "text", "domain_name" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_rule_performance_metrics"("rule_ids" "uuid"[] DEFAULT NULL::"uuid"[]) RETURNS TABLE("rule_id" "uuid", "rule_name" "text", "total_executions" bigint, "avg_execution_time" double precision, "total_violations" bigint, "success_rate" double precision, "last_executed" timestamp with time zone)
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.name,
        COUNT(e.id)::BIGINT as total_executions,
        AVG(e.execution_time)::FLOAT as avg_execution_time,
        COALESCE(SUM(e.violations_found), 0)::BIGINT as total_violations,
        CASE 
            WHEN SUM(e.entities_checked + e.relationships_checked) > 0 THEN
                1.0 - (COALESCE(SUM(e.violations_found), 0)::FLOAT / SUM(e.entities_checked + e.relationships_checked)::FLOAT)
            ELSE 1.0
        END as success_rate,
        MAX(e.end_time) as last_executed
    FROM public.validation_rules r
    LEFT JOIN public.validation_rule_executions e ON r.id = e.rule_id AND e.status = 'completed'
    WHERE (rule_ids IS NULL OR r.id = ANY(rule_ids))
    GROUP BY r.id, r.name
    ORDER BY r.name;
END;
$$;


ALTER FUNCTION "public"."get_rule_performance_metrics"("rule_ids" "uuid"[]) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_step_dependencies"("step_id" "uuid") RETURNS TABLE("dependency_step_id" "uuid", "dependency_step_name" "text")
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    inputs_text TEXT;
    input_array TEXT[];
    input_id TEXT;
BEGIN
    -- Get the inputs string for the step
    SELECT inputs INTO inputs_text FROM public.pipeline_steps WHERE id = step_id;
    
    -- If no inputs, return empty
    IF inputs_text IS NULL OR inputs_text = '' THEN
        RETURN;
    END IF;
    
    -- Split the inputs string into array
    input_array := string_to_array(inputs_text, ',');
    
    -- For each input, find the corresponding step
    FOREACH input_id IN ARRAY input_array
    LOOP
        IF trim(input_id) != '' THEN
            RETURN QUERY
            SELECT ps.id, ps.name
            FROM public.pipeline_steps ps
            WHERE ps.id = trim(input_id)::UUID;
        END IF;
    END LOOP;
    
    RETURN;
END;
$$;


ALTER FUNCTION "public"."get_step_dependencies"("step_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_user_permissions"("user_id" "uuid") RETURNS TABLE("permission_name" "text", "resource_type" "text")
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
    RETURN QUERY
    SELECT p.name, SPLIT_PART(p.name, ':', 1) as resource_type
    FROM public.user_roles ur
    JOIN public.role_permissions rp ON ur.role_id = rp.role_id
    JOIN public.permissions p ON rp.permission_id = p.id
    WHERE ur.user_id = get_user_permissions.user_id;
END;
$$;


ALTER FUNCTION "public"."get_user_permissions"("user_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_validation_summary"() RETURNS TABLE("total_rules" integer, "active_rules" integer, "recent_violations" bigint, "avg_success_rate" double precision, "critical_violations" bigint)
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_rules,
        COUNT(CASE WHEN is_active THEN 1 END)::INTEGER as active_rules,
        COALESCE((
            SELECT COUNT(*) 
            FROM public.validation_violations v
            WHERE v.created_at >= NOW() - INTERVAL '24 hours' 
            AND v.status = 'open'
        ), 0)::BIGINT as recent_violations,
        COALESCE(AVG(success_rate), 1.0)::FLOAT as avg_success_rate,
        COALESCE((
            SELECT COUNT(*)
            FROM public.validation_violations v
            WHERE v.severity = 'critical' 
            AND v.status = 'open'
        ), 0)::BIGINT as critical_violations
    FROM public.validation_rules;
END;
$$;


ALTER FUNCTION "public"."get_validation_summary"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_new_user"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$BEGIN
  INSERT INTO public.profiles (id, full_name, email)
  VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email), NEW.email);
  RETURN NEW;
END;$$;


ALTER FUNCTION "public"."handle_new_user"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."log_user_activity"("p_user_id" "uuid", "p_action" "text", "p_resource_type" "text" DEFAULT NULL::"text", "p_resource_id" "uuid" DEFAULT NULL::"uuid", "p_ip_address" "inet" DEFAULT NULL::"inet", "p_user_agent" "text" DEFAULT NULL::"text", "p_details" "jsonb" DEFAULT NULL::"jsonb") RETURNS "uuid"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    activity_id UUID;
BEGIN
    INSERT INTO public.user_activity_log (
        user_id, action, resource_type, resource_id, 
        ip_address, user_agent, details
    ) VALUES (
        p_user_id, p_action, p_resource_type, p_resource_id,
        p_ip_address, p_user_agent, p_details
    ) RETURNING id INTO activity_id;
    
    RETURN activity_id;
END;
$$;


ALTER FUNCTION "public"."log_user_activity"("p_user_id" "uuid", "p_action" "text", "p_resource_type" "text", "p_resource_id" "uuid", "p_ip_address" "inet", "p_user_agent" "text", "p_details" "jsonb") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."migrate_entity_types"() RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
  existing_type TEXT;
  type_id INTEGER;
  general_domain_id INTEGER;
BEGIN
  -- Get general domain id
  SELECT id INTO general_domain_id FROM public.domains WHERE name = 'general';
  
  -- Insert distinct entity types from existing data
  FOR existing_type IN 
    SELECT DISTINCT entity_type FROM public.kg_entities WHERE entity_type IS NOT NULL
  LOOP
    INSERT INTO public.entity_types (name, display_name)
    VALUES (existing_type, initcap(replace(existing_type, '_', ' ')))
    ON CONFLICT (name) DO NOTHING
    RETURNING id INTO type_id;
    
    -- If type was inserted, link it to general domain
    IF type_id IS NOT NULL THEN
      INSERT INTO public.entity_type_domains (entity_type_id, domain_id, is_primary)
      VALUES (type_id, general_domain_id, TRUE)
      ON CONFLICT DO NOTHING;
    ELSE
      -- Get existing type id
      SELECT id INTO type_id FROM public.entity_types WHERE name = existing_type;
      
      -- Link to general domain if not already linked
      INSERT INTO public.entity_type_domains (entity_type_id, domain_id, is_primary)
      VALUES (type_id, general_domain_id, TRUE)
      ON CONFLICT DO NOTHING;
    END IF;
  END LOOP;
  
  -- Update kg_entities with entity_type_id
  UPDATE public.kg_entities 
  SET entity_type_id = et.id
  FROM public.entity_types et
  WHERE public.kg_entities.entity_type = et.name;
  
  -- Update entity_mappings with entity_type_id
  UPDATE public.entity_mappings
  SET entity_type_id = et.id
  FROM public.entity_types et  
  WHERE public.entity_mappings.entity_type = et.name;
END;
$$;


ALTER FUNCTION "public"."migrate_entity_types"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."migrate_relationship_types"() RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
  existing_type TEXT;
  type_id INTEGER;
  general_domain_id INTEGER;
BEGIN
  -- Get general domain id
  SELECT id INTO general_domain_id FROM public.domains WHERE name = 'general';
  
  -- Insert distinct relationship types from existing data
  FOR existing_type IN
    SELECT DISTINCT relationship_type FROM public.kg_relationships WHERE relationship_type IS NOT NULL
  LOOP
    INSERT INTO public.relationship_types (name, display_name)
    VALUES (existing_type, initcap(replace(existing_type, '_', ' ')))
    ON CONFLICT (name) DO NOTHING
    RETURNING id INTO type_id;
    
    -- If type was inserted, link it to general domain
    IF type_id IS NOT NULL THEN
      INSERT INTO public.relationship_type_domains (relationship_type_id, domain_id, is_primary)
      VALUES (type_id, general_domain_id, TRUE)
      ON CONFLICT DO NOTHING;
    ELSE
      -- Get existing type id
      SELECT id INTO type_id FROM public.relationship_types WHERE name = existing_type;
      
      -- Link to general domain if not already linked
      INSERT INTO public.relationship_type_domains (relationship_type_id, domain_id, is_primary)
      VALUES (type_id, general_domain_id, TRUE)
      ON CONFLICT DO NOTHING;
    END IF;
  END LOOP;
  
  -- Update kg_relationships with relationship_type_id
  UPDATE public.kg_relationships
  SET relationship_type_id = rt.id
  FROM public.relationship_types rt
  WHERE public.kg_relationships.relationship_type = rt.name;
  
  -- Update relationship_mappings with relationship_type_id
  UPDATE public.relationship_mappings
  SET relationship_type_id = rt.id  
  FROM public.relationship_types rt
  WHERE public.relationship_mappings.relationship_type = rt.name;
END;
$$;


ALTER FUNCTION "public"."migrate_relationship_types"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."track_entity_change"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
  version_num INTEGER;
BEGIN
  -- Get next version number
  SELECT COALESCE(MAX(version_number), 0) + 1 INTO version_num
  FROM public.entity_history
  WHERE entity_id = NEW.id;
  
  -- Insert history record
  INSERT INTO public.entity_history (
    entity_id, version_number, change_type,
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


ALTER FUNCTION "public"."track_entity_change"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_rule_statistics"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    -- Update rule execution count and statistics
    IF TG_OP = 'INSERT' AND NEW.status = 'completed' THEN
        UPDATE public.validation_rules 
        SET 
            execution_count = execution_count + 1,
            last_executed_at = NEW.end_time,
            average_execution_time = COALESCE(
                (average_execution_time * (execution_count - 1) + NEW.execution_time) / execution_count,
                NEW.execution_time
            )
        WHERE id = NEW.rule_id;
        
        -- Update violation count
        UPDATE public.validation_rules 
        SET 
            violation_count = violation_count + NEW.violations_found,
            success_rate = CASE 
                WHEN execution_count > 0 THEN 
                    1.0 - (CAST(violation_count + NEW.violations_found AS FLOAT) / CAST((SELECT SUM(entities_checked + relationships_checked) FROM public.validation_rule_executions WHERE rule_id = NEW.rule_id) AS FLOAT))
                ELSE 1.0 
            END
        WHERE id = NEW.rule_id;
    END IF;
    
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_rule_statistics"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_timestamp"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_timestamp"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."user_has_role"("user_id" "uuid", "role_name" "text") RETURNS boolean
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    has_role BOOLEAN := FALSE;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM public.user_roles ur
        JOIN public.roles r ON ur.role_id = r.id
        WHERE ur.user_id = user_has_role.user_id
        AND r.name = role_name
    ) INTO has_role;
    
    RETURN has_role;
END;
$$;


ALTER FUNCTION "public"."user_has_role"("user_id" "uuid", "role_name" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."validate_relationship_types"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
  source_type_id INTEGER;
  target_type_id INTEGER;
  rel_type RECORD;
BEGIN
  -- Get entity type IDs
  SELECT entity_type_id INTO source_type_id FROM public.kg_entities WHERE id = NEW.source_entity_id;
  SELECT entity_type_id INTO target_type_id FROM public.kg_entities WHERE id = NEW.target_entity_id;
  
  -- Get relationship type constraints
  SELECT * INTO rel_type FROM public.relationship_types WHERE id = NEW.relationship_type_id;
  
  -- Validate source entity type
  IF rel_type.source_entity_types IS NOT NULL AND NOT (source_type_id = ANY(rel_type.source_entity_types)) THEN
    RAISE EXCEPTION 'Source entity type % is not allowed for relationship type %', source_type_id, rel_type.name;
  END IF;
  
  -- Validate target entity type  
  IF rel_type.target_entity_types IS NOT NULL AND NOT (target_type_id = ANY(rel_type.target_entity_types)) THEN
    RAISE EXCEPTION 'Target entity type % is not allowed for relationship type %', target_type_id, rel_type.name;
  END IF;
  
  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."validate_relationship_types"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."api_keys" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" "text" NOT NULL,
    "description" "text",
    "key_hash" "text" NOT NULL,
    "key_prefix" "text" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "is_active" boolean DEFAULT true,
    "expires_at" timestamp with time zone,
    "rate_limit" integer DEFAULT 1000,
    "allowed_ips" "text"[],
    "last_used" timestamp with time zone,
    "usage_count" integer DEFAULT 0,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL
);


ALTER TABLE "public"."api_keys" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."api_usage_log" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "api_key_id" "uuid",
    "method" "text",
    "path" "text",
    "status_code" integer,
    "response_time" double precision,
    "ip_address" "inet",
    "user_agent" "text",
    "timestamp" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL
);


ALTER TABLE "public"."api_usage_log" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."conflicts" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "conflict_type" "text" NOT NULL,
    "severity" "text" NOT NULL,
    "status" "text" DEFAULT 'detected'::"text" NOT NULL,
    "description" "text" NOT NULL,
    "confidence_score" double precision NOT NULL,
    "source_entity_id" "uuid",
    "target_entity_id" "uuid",
    "source_relationship_id" "uuid",
    "target_relationship_id" "uuid",
    "conflicting_attributes" "jsonb",
    "context_data" "jsonb",
    "resolution_method" "text",
    "resolution_data" "jsonb",
    "resolution_reasoning" "text",
    "detected_by" "text" NOT NULL,
    "detected_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "assigned_to" "uuid",
    "resolved_by" "text",
    "resolved_at" timestamp with time zone,
    "auto_resolution_attempted" boolean DEFAULT false,
    "auto_resolution_suggestions" "jsonb",
    "review_notes" "text",
    "escalation_reason" "text",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "conflicts_confidence_score_check" CHECK ((("confidence_score" >= (0)::double precision) AND ("confidence_score" <= (1)::double precision))),
    CONSTRAINT "conflicts_conflict_type_check" CHECK (("conflict_type" = ANY (ARRAY['duplicate_entity'::"text", 'contradictory_relationship'::"text", 'missing_relationship'::"text", 'attribute_mismatch'::"text", 'temporal_conflict'::"text", 'source_conflict'::"text", 'schema_mismatch'::"text"]))),
    CONSTRAINT "conflicts_severity_check" CHECK (("severity" = ANY (ARRAY['low'::"text", 'medium'::"text", 'high'::"text", 'critical'::"text"]))),
    CONSTRAINT "conflicts_status_check" CHECK (("status" = ANY (ARRAY['detected'::"text", 'under_review'::"text", 'resolved_manual'::"text", 'resolved_auto'::"text", 'rejected'::"text", 'escalated'::"text"])))
);


ALTER TABLE "public"."conflicts" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."data_sources" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" "text" NOT NULL,
    "description" "text",
    "source_type" "text" NOT NULL,
    "connection_details" "jsonb" NOT NULL,
    "is_active" boolean DEFAULT true,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "encrypted_credentials" "bytea",
    "trust_score" double precision DEFAULT 0.5,
    "trust_score_updated_at" timestamp with time zone,
    "trust_score_reason" "text",
    CONSTRAINT "data_sources_source_type_check" CHECK (("source_type" = ANY (ARRAY['file'::"text", 'api'::"text", 'database'::"text", 'url'::"text"]))),
    CONSTRAINT "data_sources_trust_score_check" CHECK ((("trust_score" >= (0.0)::double precision) AND ("trust_score" <= (1.0)::double precision)))
);


ALTER TABLE "public"."data_sources" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."extraction_results" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "pipeline_run_id" "uuid",
    "source_id" "uuid",
    "entity_count" integer DEFAULT 0,
    "relationship_count" integer DEFAULT 0,
    "processed_text_length" integer,
    "extracted_entities" "jsonb",
    "extracted_relationships" "jsonb",
    "status" "text" NOT NULL,
    "error_message" "text",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "step_run_id" "uuid",
    "synced_to_graph" boolean DEFAULT false,
    "synced_at" timestamp with time zone,
    "chunks" "jsonb",
    CONSTRAINT "extraction_results_status_check" CHECK (("status" = ANY (ARRAY['pending'::"text", 'completed'::"text", 'failed'::"text", 'partially_completed'::"text"])))
);


ALTER TABLE "public"."extraction_results" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."file_uploads" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "data_source_id" "uuid",
    "file_name" "text" NOT NULL,
    "file_type" "text" NOT NULL,
    "file_size" integer NOT NULL,
    "storage_path" "text" NOT NULL,
    "upload_status" "text" DEFAULT 'pending'::"text",
    "processed" boolean DEFAULT false,
    "metadata" "jsonb",
    "uploaded_by" "uuid",
    "uploaded_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "file_uploads_upload_status_check" CHECK (("upload_status" = ANY (ARRAY['pending'::"text", 'processing'::"text", 'completed'::"text", 'failed'::"text"])))
);


ALTER TABLE "public"."file_uploads" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."kg_edit_logs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "action" "text" NOT NULL,
    "resource_type" "text",
    "resource_id" "uuid",
    "changes" "jsonb",
    "reason" "text",
    "rollback_info" "jsonb",
    "timestamp" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL
);


ALTER TABLE "public"."kg_edit_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."kg_entities" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "neo4j_id" "text",
    "entity_text" "text" NOT NULL,
    "source_document_id" "uuid",
    "properties" "jsonb",
    "confidence" double precision,
    "is_verified" boolean DEFAULT false,
    "verification_notes" "text",
    "verified_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "embedding" "public"."vector"(1536),
    "is_active" boolean DEFAULT true,
    "merged_into" "uuid",
    "created_by" "uuid",
    "updated_by" "uuid",
    "extraction_confidence" double precision DEFAULT 0.0,
    "validation_status" "text" DEFAULT 'pending'::"text",
    "validation_errors" "jsonb",
    "deleted_at" timestamp with time zone,
    "deleted_by" "uuid",
    "deleted_reason" "text",
    "ontology_class_id" integer,
    CONSTRAINT "kg_entities_validation_status_check" CHECK (("validation_status" = ANY (ARRAY['pending'::"text", 'valid'::"text", 'invalid'::"text", 'needs_review'::"text"])))
);


ALTER TABLE "public"."kg_entities" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."kg_relationships" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "neo4j_id" "text",
    "source_entity_id" "uuid",
    "target_entity_id" "uuid",
    "source_document_id" "uuid",
    "properties" "jsonb",
    "confidence" double precision,
    "is_verified" boolean DEFAULT false,
    "verification_notes" "text",
    "verified_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "is_active" boolean DEFAULT true,
    "created_by" "uuid",
    "updated_by" "uuid",
    "relationship_type_id" integer,
    "extraction_confidence" double precision DEFAULT 0.0,
    "validation_status" "text" DEFAULT 'pending'::"text",
    "validation_errors" "jsonb",
    "ontology_property_id" integer,
    CONSTRAINT "kg_relationships_validation_status_check" CHECK (("validation_status" = ANY (ARRAY['pending'::"text", 'valid'::"text", 'invalid'::"text", 'needs_review'::"text"])))
);


ALTER TABLE "public"."kg_relationships" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."notifications" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "title" "text" NOT NULL,
    "message" "text" NOT NULL,
    "icon" "text",
    "link" "text",
    "is_read" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL
);


ALTER TABLE "public"."notifications" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."ontology_classes" (
    "id" integer NOT NULL,
    "uri" "text" NOT NULL,
    "label" "text",
    "description" "text",
    "parent_class_id" integer,
    "properties" "jsonb",
    "domain" "text",
    "is_custom" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL
);


ALTER TABLE "public"."ontology_classes" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."ontology_classes_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE "public"."ontology_classes_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."ontology_classes_id_seq" OWNED BY "public"."ontology_classes"."id";



CREATE TABLE IF NOT EXISTS "public"."ontology_properties" (
    "id" integer NOT NULL,
    "uri" "text" NOT NULL,
    "label" "text",
    "description" "text",
    "domain_class_id" integer,
    "range_class_id" integer,
    "property_type" "text",
    "is_custom" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "domain" "text",
    CONSTRAINT "fibo_properties_property_type_check" CHECK (("property_type" = ANY (ARRAY['object'::"text", 'datatype'::"text"])))
);


ALTER TABLE "public"."ontology_properties" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."ontology_properties_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE "public"."ontology_properties_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."ontology_properties_id_seq" OWNED BY "public"."ontology_properties"."id";



CREATE TABLE IF NOT EXISTS "public"."permissions" (
    "id" integer NOT NULL,
    "name" "text" NOT NULL,
    "description" "text",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL
);


ALTER TABLE "public"."permissions" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."permissions_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE "public"."permissions_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."permissions_id_seq" OWNED BY "public"."permissions"."id";



CREATE TABLE IF NOT EXISTS "public"."pipeline_runs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "pipeline_id" "uuid",
    "status" "text" NOT NULL,
    "start_time" timestamp with time zone NOT NULL,
    "end_time" timestamp with time zone,
    "duration" integer,
    "triggered_by" "uuid",
    "log" "text",
    "error_message" "text",
    "stats" "jsonb",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "input_parameters" "jsonb",
    "result" "jsonb",
    "celery_task_id" "text",
    CONSTRAINT "pipeline_runs_status_check" CHECK (("status" = ANY (ARRAY['pending'::"text", 'running'::"text", 'completed'::"text", 'failed'::"text"])))
);


ALTER TABLE "public"."pipeline_runs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."pipeline_step_runs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "pipeline_run_id" "uuid",
    "step_id" "uuid",
    "status" "text" NOT NULL,
    "start_time" timestamp with time zone,
    "end_time" timestamp with time zone,
    "run_order" integer NOT NULL,
    "input_data" "jsonb",
    "output_data" "jsonb",
    "error_message" "text",
    "retry_count" integer DEFAULT 0,
    "celery_task_id" "text",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "pipeline_step_runs_status_check" CHECK (("status" = ANY (ARRAY['pending'::"text", 'running'::"text", 'completed'::"text", 'failed'::"text", 'cancelled'::"text"])))
);


ALTER TABLE "public"."pipeline_step_runs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."pipeline_steps" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "pipeline_id" "uuid",
    "name" "text" NOT NULL,
    "step_type" "text" NOT NULL,
    "config" "jsonb" NOT NULL,
    "run_order" integer,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "depends_on" "uuid"[],
    "description" "text",
    "enabled" boolean DEFAULT false,
    "incremental_config" "jsonb",
    "inputs" "text",
    "is_incremental_capable" boolean DEFAULT false
);


ALTER TABLE "public"."pipeline_steps" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."pipelines" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" "text" NOT NULL,
    "description" "text",
    "pipeline_type" "text" NOT NULL,
    "schedule" "text",
    "is_active" boolean DEFAULT true,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "pipelines_pipeline_type_check" CHECK (("pipeline_type" = ANY (ARRAY['extraction'::"text", 'transformation'::"text", 'loading'::"text", 'complete'::"text"])))
);


ALTER TABLE "public"."pipelines" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."profiles" (
    "id" "uuid" NOT NULL,
    "full_name" "text",
    "avatar_url" "text",
    "department" "text",
    "position" "text",
    "bio" "text",
    "last_sign_in_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "email" "text",
    "is_active" boolean
);


ALTER TABLE "public"."profiles" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."quality_assessments" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "entity_id" "uuid",
    "relationship_id" "uuid",
    "dimension" "text" NOT NULL,
    "score" double precision NOT NULL,
    "assessment_method" "text" NOT NULL,
    "assessment_date" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "details" "jsonb",
    "improvement_suggestions" "text"[],
    "created_by" "uuid",
    CONSTRAINT "quality_assessments_dimension_check" CHECK (("dimension" = ANY (ARRAY['completeness'::"text", 'accuracy'::"text", 'consistency'::"text", 'validity'::"text", 'uniqueness'::"text", 'timeliness'::"text", 'relevance'::"text"]))),
    CONSTRAINT "quality_assessments_score_check" CHECK ((("score" >= (0)::double precision) AND ("score" <= (1)::double precision)))
);


ALTER TABLE "public"."quality_assessments" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."quality_monitoring_runs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "started_at" timestamp with time zone NOT NULL,
    "completed_at" timestamp with time zone,
    "overall_score" double precision,
    "dimension_scores" "jsonb",
    "issues_detected" integer DEFAULT 0,
    "conflicts_pending" integer DEFAULT 0,
    "steps" "jsonb",
    "status" "text",
    "error_message" "text",
    "quality_report" "jsonb",
    CONSTRAINT "quality_monitoring_runs_status_check" CHECK (("status" = ANY (ARRAY['running'::"text", 'completed'::"text", 'failed'::"text"])))
);


ALTER TABLE "public"."quality_monitoring_runs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."rate_limiter_logs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "identifier" "text" NOT NULL,
    "scope" "text" NOT NULL,
    "allowed" boolean NOT NULL,
    "limit_value" integer NOT NULL,
    "remaining" integer NOT NULL,
    "timestamp" timestamp with time zone DEFAULT "now"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."rate_limiter_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."role_permissions" (
    "id" integer NOT NULL,
    "role_id" integer,
    "permission_id" integer,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL
);


ALTER TABLE "public"."role_permissions" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."role_permissions_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE "public"."role_permissions_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."role_permissions_id_seq" OWNED BY "public"."role_permissions"."id";



CREATE TABLE IF NOT EXISTS "public"."roles" (
    "id" integer NOT NULL,
    "name" "text" NOT NULL,
    "description" "text",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL
);


ALTER TABLE "public"."roles" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."roles_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE "public"."roles_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."roles_id_seq" OWNED BY "public"."roles"."id";



CREATE TABLE IF NOT EXISTS "public"."saved_queries" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" "text" NOT NULL,
    "description" "text",
    "query_type" "text",
    "query_text" "text" NOT NULL,
    "parameters" "jsonb",
    "is_public" boolean DEFAULT false,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "saved_queries_query_type_check" CHECK (("query_type" = ANY (ARRAY['cypher'::"text", 'sparql'::"text", 'natural_language'::"text"])))
);


ALTER TABLE "public"."saved_queries" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_activity_log" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "action" "text" NOT NULL,
    "resource_type" "text",
    "resource_id" "uuid",
    "ip_address" "inet",
    "user_agent" "text",
    "details" "jsonb",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL
);


ALTER TABLE "public"."user_activity_log" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_roles" (
    "id" integer NOT NULL,
    "user_id" "uuid",
    "role_id" integer,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL
);


ALTER TABLE "public"."user_roles" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."user_roles_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE "public"."user_roles_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."user_roles_id_seq" OWNED BY "public"."user_roles"."id";



CREATE TABLE IF NOT EXISTS "public"."visualizations" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" "text" NOT NULL,
    "description" "text",
    "query_id" "uuid",
    "visualization_type" "text" NOT NULL,
    "config" "jsonb" NOT NULL,
    "is_public" boolean DEFAULT false,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    CONSTRAINT "visualizations_visualization_type_check" CHECK (("visualization_type" = ANY (ARRAY['graph'::"text", 'tree'::"text", 'table'::"text", 'chart'::"text"])))
);


ALTER TABLE "public"."visualizations" OWNER TO "postgres";


ALTER TABLE ONLY "public"."ontology_classes" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."ontology_classes_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."ontology_properties" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."ontology_properties_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."permissions" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."permissions_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."role_permissions" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."role_permissions_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."roles" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."roles_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."user_roles" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."user_roles_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."api_keys"
    ADD CONSTRAINT "api_keys_key_hash_key" UNIQUE ("key_hash");



ALTER TABLE ONLY "public"."api_keys"
    ADD CONSTRAINT "api_keys_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."api_usage_log"
    ADD CONSTRAINT "api_usage_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."conflicts"
    ADD CONSTRAINT "conflicts_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."data_sources"
    ADD CONSTRAINT "data_sources_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."extraction_results"
    ADD CONSTRAINT "extraction_results_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."ontology_classes"
    ADD CONSTRAINT "fibo_classes_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."ontology_classes"
    ADD CONSTRAINT "fibo_classes_uri_key" UNIQUE ("uri");



ALTER TABLE ONLY "public"."ontology_properties"
    ADD CONSTRAINT "fibo_properties_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."ontology_properties"
    ADD CONSTRAINT "fibo_properties_uri_key" UNIQUE ("uri");



ALTER TABLE ONLY "public"."file_uploads"
    ADD CONSTRAINT "file_uploads_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."kg_edit_logs"
    ADD CONSTRAINT "kg_edit_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."kg_entities"
    ADD CONSTRAINT "kg_entities_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."kg_relationships"
    ADD CONSTRAINT "kg_relationships_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."notifications"
    ADD CONSTRAINT "notifications_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."permissions"
    ADD CONSTRAINT "permissions_name_key" UNIQUE ("name");



ALTER TABLE ONLY "public"."permissions"
    ADD CONSTRAINT "permissions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."pipeline_runs"
    ADD CONSTRAINT "pipeline_runs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."pipeline_step_runs"
    ADD CONSTRAINT "pipeline_step_runs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."pipeline_steps"
    ADD CONSTRAINT "pipeline_steps_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."pipelines"
    ADD CONSTRAINT "pipelines_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."quality_assessments"
    ADD CONSTRAINT "quality_assessments_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."quality_monitoring_runs"
    ADD CONSTRAINT "quality_monitoring_runs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."rate_limiter_logs"
    ADD CONSTRAINT "rate_limiter_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."role_permissions"
    ADD CONSTRAINT "role_permissions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."role_permissions"
    ADD CONSTRAINT "role_permissions_role_id_permission_id_key" UNIQUE ("role_id", "permission_id");



ALTER TABLE ONLY "public"."roles"
    ADD CONSTRAINT "roles_name_key" UNIQUE ("name");



ALTER TABLE ONLY "public"."roles"
    ADD CONSTRAINT "roles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."saved_queries"
    ADD CONSTRAINT "saved_queries_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_activity_log"
    ADD CONSTRAINT "user_activity_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_roles"
    ADD CONSTRAINT "user_roles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_roles"
    ADD CONSTRAINT "user_roles_user_id_role_id_key" UNIQUE ("user_id", "role_id");



ALTER TABLE ONLY "public"."visualizations"
    ADD CONSTRAINT "visualizations_pkey" PRIMARY KEY ("id");



CREATE INDEX "fibo_classes_label_idx" ON "public"."ontology_classes" USING "gin" ("label" "public"."gin_trgm_ops");



CREATE INDEX "fibo_classes_uri_idx" ON "public"."ontology_classes" USING "gin" ("uri" "public"."gin_trgm_ops");



CREATE INDEX "fibo_properties_label_idx" ON "public"."ontology_properties" USING "gin" ("label" "public"."gin_trgm_ops");



CREATE INDEX "fibo_properties_uri_idx" ON "public"."ontology_properties" USING "gin" ("uri" "public"."gin_trgm_ops");



CREATE INDEX "idx_api_keys_is_active" ON "public"."api_keys" USING "btree" ("is_active");



CREATE INDEX "idx_api_keys_key_hash" ON "public"."api_keys" USING "btree" ("key_hash");



CREATE INDEX "idx_api_keys_user_id" ON "public"."api_keys" USING "btree" ("user_id");



CREATE INDEX "idx_api_usage_path" ON "public"."api_usage_log" USING "btree" ("path");



CREATE INDEX "idx_api_usage_timestamp" ON "public"."api_usage_log" USING "btree" ("timestamp");



CREATE INDEX "idx_api_usage_user_id" ON "public"."api_usage_log" USING "btree" ("user_id");



CREATE INDEX "idx_conflicts_assigned_to" ON "public"."conflicts" USING "btree" ("assigned_to");



CREATE INDEX "idx_conflicts_conflict_type" ON "public"."conflicts" USING "btree" ("conflict_type");



CREATE INDEX "idx_conflicts_severity" ON "public"."conflicts" USING "btree" ("severity");



CREATE INDEX "idx_conflicts_source_entity_id" ON "public"."conflicts" USING "btree" ("source_entity_id");



CREATE INDEX "idx_conflicts_status" ON "public"."conflicts" USING "btree" ("status");



CREATE INDEX "idx_conflicts_target_entity_id" ON "public"."conflicts" USING "btree" ("target_entity_id");



CREATE INDEX "idx_data_sources_active" ON "public"."data_sources" USING "btree" ("is_active");



CREATE INDEX "idx_data_sources_trust_score" ON "public"."data_sources" USING "btree" ("trust_score");



CREATE INDEX "idx_kg_entities_created_by" ON "public"."kg_entities" USING "btree" ("created_by");



CREATE INDEX "idx_kg_entities_is_active" ON "public"."kg_entities" USING "btree" ("is_active");



CREATE INDEX "idx_kg_relationships_is_active" ON "public"."kg_relationships" USING "btree" ("is_active");



CREATE INDEX "idx_pipeline_runs_pipeline_id" ON "public"."pipeline_runs" USING "btree" ("pipeline_id");



CREATE INDEX "idx_pipeline_runs_status" ON "public"."pipeline_runs" USING "btree" ("status");



CREATE INDEX "idx_pipeline_step_runs_pipeline_run_id" ON "public"."pipeline_step_runs" USING "btree" ("pipeline_run_id");



CREATE INDEX "idx_pipeline_step_runs_status" ON "public"."pipeline_step_runs" USING "btree" ("status");



CREATE INDEX "idx_pipeline_step_runs_step_id" ON "public"."pipeline_step_runs" USING "btree" ("step_id");



CREATE INDEX "idx_pipeline_steps_pipeline_id" ON "public"."pipeline_steps" USING "btree" ("pipeline_id");



CREATE INDEX "idx_pipeline_steps_run_order" ON "public"."pipeline_steps" USING "btree" ("run_order");



CREATE INDEX "idx_pipeline_steps_step_type" ON "public"."pipeline_steps" USING "btree" ("step_type");



CREATE INDEX "idx_quality_assessments_dimension" ON "public"."quality_assessments" USING "btree" ("dimension");



CREATE INDEX "idx_quality_assessments_entity_id" ON "public"."quality_assessments" USING "btree" ("entity_id");



CREATE INDEX "idx_quality_assessments_relationship_id" ON "public"."quality_assessments" USING "btree" ("relationship_id");



CREATE INDEX "idx_rate_limiter_identifier" ON "public"."rate_limiter_logs" USING "btree" ("identifier");



CREATE INDEX "idx_rate_limiter_identifier_scope" ON "public"."rate_limiter_logs" USING "btree" ("identifier", "scope");



CREATE INDEX "idx_rate_limiter_scope" ON "public"."rate_limiter_logs" USING "btree" ("scope");



CREATE INDEX "idx_rate_limiter_timestamp" ON "public"."rate_limiter_logs" USING "btree" ("timestamp");



CREATE INDEX "idx_user_activity_action" ON "public"."user_activity_log" USING "btree" ("action");



CREATE INDEX "idx_user_activity_created_at" ON "public"."user_activity_log" USING "btree" ("created_at");



CREATE INDEX "idx_user_activity_user_id" ON "public"."user_activity_log" USING "btree" ("user_id");



CREATE INDEX "kg_entities_text_idx" ON "public"."kg_entities" USING "gin" ("entity_text" "public"."gin_trgm_ops");



CREATE INDEX "kg_entities_validation_status_idx" ON "public"."kg_entities" USING "btree" ("validation_status");



CREATE INDEX "kg_relationships_source_idx" ON "public"."kg_relationships" USING "btree" ("source_entity_id");



CREATE INDEX "kg_relationships_target_idx" ON "public"."kg_relationships" USING "btree" ("target_entity_id");



CREATE INDEX "kg_relationships_type_id_idx" ON "public"."kg_relationships" USING "btree" ("relationship_type_id");



CREATE INDEX "kg_relationships_validation_status_idx" ON "public"."kg_relationships" USING "btree" ("validation_status");



CREATE OR REPLACE TRIGGER "track_kg_entity_changes" AFTER INSERT OR UPDATE ON "public"."kg_entities" FOR EACH ROW EXECUTE FUNCTION "public"."track_entity_change"();



CREATE OR REPLACE TRIGGER "track_kg_relationship_changes" AFTER INSERT OR UPDATE ON "public"."kg_relationships" FOR EACH ROW EXECUTE FUNCTION "public"."track_entity_change"();



CREATE OR REPLACE TRIGGER "update_timestamp" BEFORE UPDATE ON "public"."data_sources" FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();



CREATE OR REPLACE TRIGGER "update_timestamp" BEFORE UPDATE ON "public"."kg_entities" FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();



CREATE OR REPLACE TRIGGER "update_timestamp" BEFORE UPDATE ON "public"."kg_relationships" FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();



CREATE OR REPLACE TRIGGER "update_timestamp" BEFORE UPDATE ON "public"."ontology_classes" FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();



CREATE OR REPLACE TRIGGER "update_timestamp" BEFORE UPDATE ON "public"."ontology_properties" FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();



CREATE OR REPLACE TRIGGER "update_timestamp" BEFORE UPDATE ON "public"."pipelines" FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();



CREATE OR REPLACE TRIGGER "update_timestamp" BEFORE UPDATE ON "public"."profiles" FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();



CREATE OR REPLACE TRIGGER "update_timestamp" BEFORE UPDATE ON "public"."saved_queries" FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();



CREATE OR REPLACE TRIGGER "update_timestamp" BEFORE UPDATE ON "public"."visualizations" FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();



CREATE OR REPLACE TRIGGER "validate_kg_relationships" BEFORE INSERT OR UPDATE ON "public"."kg_relationships" FOR EACH ROW WHEN (("new"."relationship_type_id" IS NOT NULL)) EXECUTE FUNCTION "public"."validate_relationship_types"();



ALTER TABLE ONLY "public"."api_keys"
    ADD CONSTRAINT "api_keys_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."api_usage_log"
    ADD CONSTRAINT "api_usage_log_api_key_id_fkey" FOREIGN KEY ("api_key_id") REFERENCES "public"."api_keys"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."api_usage_log"
    ADD CONSTRAINT "api_usage_log_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."conflicts"
    ADD CONSTRAINT "conflicts_assigned_to_fkey" FOREIGN KEY ("assigned_to") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."conflicts"
    ADD CONSTRAINT "conflicts_source_entity_id_fkey" FOREIGN KEY ("source_entity_id") REFERENCES "public"."kg_entities"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."conflicts"
    ADD CONSTRAINT "conflicts_source_relationship_id_fkey" FOREIGN KEY ("source_relationship_id") REFERENCES "public"."kg_relationships"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."conflicts"
    ADD CONSTRAINT "conflicts_target_entity_id_fkey" FOREIGN KEY ("target_entity_id") REFERENCES "public"."kg_entities"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."conflicts"
    ADD CONSTRAINT "conflicts_target_relationship_id_fkey" FOREIGN KEY ("target_relationship_id") REFERENCES "public"."kg_relationships"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."data_sources"
    ADD CONSTRAINT "data_sources_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."extraction_results"
    ADD CONSTRAINT "extraction_results_pipeline_run_id_fkey" FOREIGN KEY ("pipeline_run_id") REFERENCES "public"."pipeline_runs"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."extraction_results"
    ADD CONSTRAINT "extraction_results_source_id_fkey" FOREIGN KEY ("source_id") REFERENCES "public"."file_uploads"("id");



ALTER TABLE ONLY "public"."extraction_results"
    ADD CONSTRAINT "extraction_results_step_run_id_fkey" FOREIGN KEY ("step_run_id") REFERENCES "public"."pipeline_step_runs"("id");



ALTER TABLE ONLY "public"."ontology_classes"
    ADD CONSTRAINT "fibo_classes_parent_class_id_fkey" FOREIGN KEY ("parent_class_id") REFERENCES "public"."ontology_classes"("id");



ALTER TABLE ONLY "public"."ontology_properties"
    ADD CONSTRAINT "fibo_properties_domain_class_id_fkey" FOREIGN KEY ("domain_class_id") REFERENCES "public"."ontology_classes"("id");



ALTER TABLE ONLY "public"."ontology_properties"
    ADD CONSTRAINT "fibo_properties_range_class_id_fkey" FOREIGN KEY ("range_class_id") REFERENCES "public"."ontology_classes"("id");



ALTER TABLE ONLY "public"."file_uploads"
    ADD CONSTRAINT "file_uploads_data_source_id_fkey" FOREIGN KEY ("data_source_id") REFERENCES "public"."data_sources"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."file_uploads"
    ADD CONSTRAINT "file_uploads_uploaded_by_fkey" FOREIGN KEY ("uploaded_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."kg_edit_logs"
    ADD CONSTRAINT "kg_edit_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."kg_entities"
    ADD CONSTRAINT "kg_entities_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."kg_entities"
    ADD CONSTRAINT "kg_entities_deleted_by_fkey" FOREIGN KEY ("deleted_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."kg_entities"
    ADD CONSTRAINT "kg_entities_fibo_class_id_fkey" FOREIGN KEY ("ontology_class_id") REFERENCES "public"."ontology_classes"("id");



ALTER TABLE ONLY "public"."kg_entities"
    ADD CONSTRAINT "kg_entities_merged_into_fkey" FOREIGN KEY ("merged_into") REFERENCES "public"."kg_entities"("id");



ALTER TABLE ONLY "public"."kg_entities"
    ADD CONSTRAINT "kg_entities_source_document_id_fkey" FOREIGN KEY ("source_document_id") REFERENCES "public"."file_uploads"("id");



ALTER TABLE ONLY "public"."kg_entities"
    ADD CONSTRAINT "kg_entities_updated_by_fkey" FOREIGN KEY ("updated_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."kg_entities"
    ADD CONSTRAINT "kg_entities_verified_by_fkey" FOREIGN KEY ("verified_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."kg_relationships"
    ADD CONSTRAINT "kg_relationships_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."kg_relationships"
    ADD CONSTRAINT "kg_relationships_fibo_property_id_fkey" FOREIGN KEY ("ontology_property_id") REFERENCES "public"."ontology_properties"("id");



ALTER TABLE ONLY "public"."kg_relationships"
    ADD CONSTRAINT "kg_relationships_source_document_id_fkey" FOREIGN KEY ("source_document_id") REFERENCES "public"."file_uploads"("id");



ALTER TABLE ONLY "public"."kg_relationships"
    ADD CONSTRAINT "kg_relationships_source_entity_id_fkey" FOREIGN KEY ("source_entity_id") REFERENCES "public"."kg_entities"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."kg_relationships"
    ADD CONSTRAINT "kg_relationships_target_entity_id_fkey" FOREIGN KEY ("target_entity_id") REFERENCES "public"."kg_entities"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."kg_relationships"
    ADD CONSTRAINT "kg_relationships_updated_by_fkey" FOREIGN KEY ("updated_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."kg_relationships"
    ADD CONSTRAINT "kg_relationships_verified_by_fkey" FOREIGN KEY ("verified_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."notifications"
    ADD CONSTRAINT "notifications_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."pipeline_runs"
    ADD CONSTRAINT "pipeline_runs_pipeline_id_fkey" FOREIGN KEY ("pipeline_id") REFERENCES "public"."pipelines"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."pipeline_runs"
    ADD CONSTRAINT "pipeline_runs_triggered_by_fkey" FOREIGN KEY ("triggered_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."pipeline_step_runs"
    ADD CONSTRAINT "pipeline_step_runs_pipeline_run_id_fkey" FOREIGN KEY ("pipeline_run_id") REFERENCES "public"."pipeline_runs"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."pipeline_step_runs"
    ADD CONSTRAINT "pipeline_step_runs_step_id_fkey" FOREIGN KEY ("step_id") REFERENCES "public"."pipeline_steps"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."pipeline_steps"
    ADD CONSTRAINT "pipeline_steps_pipeline_id_fkey" FOREIGN KEY ("pipeline_id") REFERENCES "public"."pipelines"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."pipelines"
    ADD CONSTRAINT "pipelines_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_id_fkey" FOREIGN KEY ("id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."quality_assessments"
    ADD CONSTRAINT "quality_assessments_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."quality_assessments"
    ADD CONSTRAINT "quality_assessments_entity_id_fkey" FOREIGN KEY ("entity_id") REFERENCES "public"."kg_entities"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."quality_assessments"
    ADD CONSTRAINT "quality_assessments_relationship_id_fkey" FOREIGN KEY ("relationship_id") REFERENCES "public"."kg_relationships"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."role_permissions"
    ADD CONSTRAINT "role_permissions_permission_id_fkey" FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."role_permissions"
    ADD CONSTRAINT "role_permissions_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."saved_queries"
    ADD CONSTRAINT "saved_queries_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."user_activity_log"
    ADD CONSTRAINT "user_activity_log_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."user_roles"
    ADD CONSTRAINT "user_roles_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."user_roles"
    ADD CONSTRAINT "user_roles_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."visualizations"
    ADD CONSTRAINT "visualizations_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."visualizations"
    ADD CONSTRAINT "visualizations_query_id_fkey" FOREIGN KEY ("query_id") REFERENCES "public"."saved_queries"("id");



CREATE POLICY "Admins can manage data sources" ON "public"."data_sources" USING ("public"."check_user_permission"("auth"."uid"(), 'datasource:write'::"text"));



CREATE POLICY "Admins can manage permissions" ON "public"."permissions" USING ("public"."check_user_permission"("auth"."uid"(), 'user:write'::"text"));



CREATE POLICY "Admins can manage pipelines" ON "public"."pipelines" USING ("public"."check_user_permission"("auth"."uid"(), 'pipeline:write'::"text"));



CREATE POLICY "Admins can manage roles" ON "public"."roles" USING ("public"."check_user_permission"("auth"."uid"(), 'user:write'::"text"));



CREATE POLICY "Admins can view all activity" ON "public"."user_activity_log" FOR SELECT USING ("public"."check_user_permission"("auth"."uid"(), 'system:monitoring'::"text"));



CREATE POLICY "Admins can view all profiles" ON "public"."profiles" FOR SELECT USING ("public"."check_user_permission"("auth"."uid"(), 'user:read'::"text"));



CREATE POLICY "Enable read access for all users" ON "public"."role_permissions" FOR SELECT TO "authenticator" USING (true);



CREATE POLICY "Enable read access for all users" ON "public"."roles" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "Enable users to view their own data only" ON "public"."file_uploads" TO "authenticated" USING ((( SELECT "auth"."uid"() AS "uid") = "uploaded_by"));



CREATE POLICY "Enable users to view their own data only" ON "public"."user_roles" FOR SELECT TO "authenticated" USING ((( SELECT "auth"."uid"() AS "uid") = "user_id"));



CREATE POLICY "Experts can manage conflicts" ON "public"."conflicts" USING ("public"."check_user_permission"("auth"."uid"(), 'quality:expert'::"text"));



CREATE POLICY "Experts can manage quality assessments" ON "public"."quality_assessments" USING ("public"."check_user_permission"("auth"."uid"(), 'quality:expert'::"text"));



CREATE POLICY "Experts can view conflicts" ON "public"."conflicts" FOR SELECT USING ("public"."check_user_permission"("auth"."uid"(), 'quality:expert'::"text"));



CREATE POLICY "Knowledge editors can manage entities" ON "public"."kg_entities" USING ("public"."check_user_permission"("auth"."uid"(), 'kg:edit'::"text"));



CREATE POLICY "Knowledge editors can manage relationships" ON "public"."kg_relationships" USING ("public"."check_user_permission"("auth"."uid"(), 'kg:edit'::"text"));



CREATE POLICY "Users can manage own API keys" ON "public"."api_keys" USING ((("user_id" = "auth"."uid"()) OR "public"."check_user_permission"("auth"."uid"(), 'user:management'::"text")));



CREATE POLICY "Users can manage pipeline steps" ON "public"."pipeline_steps" USING ("public"."check_user_permission"("auth"."uid"(), 'pipeline:write'::"text"));



CREATE POLICY "Users can save queries" ON "public"."saved_queries" FOR INSERT WITH CHECK ("public"."check_user_permission"("auth"."uid"(), 'knowledge:read'::"text"));



CREATE POLICY "Users can update their own notifications" ON "public"."notifications" FOR UPDATE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can update their own profile" ON "public"."profiles" FOR UPDATE USING (("auth"."uid"() = "id"));



CREATE POLICY "Users can update their own queries" ON "public"."saved_queries" FOR UPDATE USING (("auth"."uid"() = "created_by"));



CREATE POLICY "Users can upload files" ON "public"."file_uploads" FOR INSERT WITH CHECK ("public"."check_user_permission"("auth"."uid"(), 'file_upload:write'::"text"));



CREATE POLICY "Users can view data sources" ON "public"."data_sources" FOR SELECT USING ("public"."check_user_permission"("auth"."uid"(), 'datasource:read'::"text"));



CREATE POLICY "Users can view knowledge graph entities" ON "public"."kg_entities" FOR SELECT USING ("public"."check_user_permission"("auth"."uid"(), 'kg:read'::"text"));



CREATE POLICY "Users can view knowledge graph relationships" ON "public"."kg_relationships" FOR SELECT USING ("public"."check_user_permission"("auth"."uid"(), 'kg:read'::"text"));



CREATE POLICY "Users can view own activity" ON "public"."user_activity_log" FOR SELECT USING (("user_id" = "auth"."uid"()));



CREATE POLICY "Users can view pipeline steps" ON "public"."pipeline_steps" FOR SELECT USING ("public"."check_user_permission"("auth"."uid"(), 'pipeline:read'::"text"));



CREATE POLICY "Users can view pipelines" ON "public"."pipelines" FOR SELECT USING ("public"."check_user_permission"("auth"."uid"(), 'pipeline:read'::"text"));



CREATE POLICY "Users can view quality assessments" ON "public"."quality_assessments" FOR SELECT USING ("public"."check_user_permission"("auth"."uid"(), 'quality:read'::"text"));



CREATE POLICY "Users can view their own notifications" ON "public"."notifications" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view their own profile" ON "public"."profiles" FOR SELECT USING (("auth"."uid"() = "id"));



CREATE POLICY "Users can view their own queries" ON "public"."saved_queries" FOR SELECT USING ((("auth"."uid"() = "created_by") OR "is_public"));



CREATE POLICY "Users can view uploads" ON "public"."file_uploads" FOR SELECT USING ("public"."check_user_permission"("auth"."uid"(), 'file_upload:read'::"text"));



ALTER TABLE "public"."notifications" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."saved_queries" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."visualizations" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";





GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_in"("cstring") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_in"("cstring") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_in"("cstring") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_in"("cstring") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_out"("public"."gtrgm") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_out"("public"."gtrgm") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_out"("public"."gtrgm") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_out"("public"."gtrgm") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_in"("cstring", "oid", integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_in"("cstring", "oid", integer) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_in"("cstring", "oid", integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_in"("cstring", "oid", integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_out"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_out"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_out"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_out"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_recv"("internal", "oid", integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_recv"("internal", "oid", integer) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_recv"("internal", "oid", integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_recv"("internal", "oid", integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_send"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_send"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_send"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_send"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_typmod_in"("cstring"[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_typmod_in"("cstring"[]) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_typmod_in"("cstring"[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_typmod_in"("cstring"[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_in"("cstring", "oid", integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_in"("cstring", "oid", integer) TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_in"("cstring", "oid", integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_in"("cstring", "oid", integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_out"("public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_out"("public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_out"("public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_out"("public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_recv"("internal", "oid", integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_recv"("internal", "oid", integer) TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_recv"("internal", "oid", integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_recv"("internal", "oid", integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_send"("public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_send"("public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_send"("public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_send"("public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_typmod_in"("cstring"[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_typmod_in"("cstring"[]) TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_typmod_in"("cstring"[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_typmod_in"("cstring"[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_in"("cstring", "oid", integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_in"("cstring", "oid", integer) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_in"("cstring", "oid", integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_in"("cstring", "oid", integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_out"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_out"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_out"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_out"("public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_recv"("internal", "oid", integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_recv"("internal", "oid", integer) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_recv"("internal", "oid", integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_recv"("internal", "oid", integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_send"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_send"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_send"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_send"("public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_typmod_in"("cstring"[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_typmod_in"("cstring"[]) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_typmod_in"("cstring"[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_typmod_in"("cstring"[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_halfvec"(real[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(real[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(real[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(real[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(real[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(real[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(real[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(real[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_vector"(real[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_vector"(real[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_vector"(real[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_vector"(real[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_halfvec"(double precision[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(double precision[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(double precision[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(double precision[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(double precision[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(double precision[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(double precision[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(double precision[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_vector"(double precision[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_vector"(double precision[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_vector"(double precision[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_vector"(double precision[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_halfvec"(integer[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(integer[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(integer[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(integer[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(integer[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(integer[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(integer[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(integer[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_vector"(integer[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_vector"(integer[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_vector"(integer[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_vector"(integer[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_halfvec"(numeric[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(numeric[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(numeric[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(numeric[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(numeric[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(numeric[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(numeric[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(numeric[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_vector"(numeric[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_vector"(numeric[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_vector"(numeric[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_vector"(numeric[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_to_float4"("public"."halfvec", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_to_float4"("public"."halfvec", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_to_float4"("public"."halfvec", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_to_float4"("public"."halfvec", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec"("public"."halfvec", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec"("public"."halfvec", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec"("public"."halfvec", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec"("public"."halfvec", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_to_sparsevec"("public"."halfvec", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_to_sparsevec"("public"."halfvec", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_to_sparsevec"("public"."halfvec", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_to_sparsevec"("public"."halfvec", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_to_vector"("public"."halfvec", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_to_vector"("public"."halfvec", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_to_vector"("public"."halfvec", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_to_vector"("public"."halfvec", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_to_halfvec"("public"."sparsevec", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_to_halfvec"("public"."sparsevec", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_to_halfvec"("public"."sparsevec", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_to_halfvec"("public"."sparsevec", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec"("public"."sparsevec", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec"("public"."sparsevec", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec"("public"."sparsevec", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec"("public"."sparsevec", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_to_vector"("public"."sparsevec", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_to_vector"("public"."sparsevec", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_to_vector"("public"."sparsevec", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_to_vector"("public"."sparsevec", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_to_float4"("public"."vector", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_to_float4"("public"."vector", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_to_float4"("public"."vector", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_to_float4"("public"."vector", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_to_halfvec"("public"."vector", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_to_halfvec"("public"."vector", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_to_halfvec"("public"."vector", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_to_halfvec"("public"."vector", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_to_sparsevec"("public"."vector", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_to_sparsevec"("public"."vector", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_to_sparsevec"("public"."vector", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_to_sparsevec"("public"."vector", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector"("public"."vector", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector"("public"."vector", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."vector"("public"."vector", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector"("public"."vector", integer, boolean) TO "service_role";

















































































































































































GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."build_dependency_graph"("entity_id" "uuid", "max_depth" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."build_dependency_graph"("entity_id" "uuid", "max_depth" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."build_dependency_graph"("entity_id" "uuid", "max_depth" integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."check_user_permission"("user_id" "uuid", "permission_name" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."check_user_permission"("user_id" "uuid", "permission_name" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."check_user_permission"("user_id" "uuid", "permission_name" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."cleanup_expired_cache"() TO "anon";
GRANT ALL ON FUNCTION "public"."cleanup_expired_cache"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."cleanup_expired_cache"() TO "service_role";



GRANT ALL ON FUNCTION "public"."cleanup_old_logs"("days_to_keep" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."cleanup_old_logs"("days_to_keep" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."cleanup_old_logs"("days_to_keep" integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."compute_entity_similarity"("entity1_id" "uuid", "entity2_id" "uuid", "similarity_type" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."compute_entity_similarity"("entity1_id" "uuid", "entity2_id" "uuid", "similarity_type" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."compute_entity_similarity"("entity1_id" "uuid", "entity2_id" "uuid", "similarity_type" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."decrypt_data_source_credentials"("p_id" "uuid", "p_encryption_key" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."decrypt_data_source_credentials"("p_id" "uuid", "p_encryption_key" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."decrypt_data_source_credentials"("p_id" "uuid", "p_encryption_key" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."encrypt_data_source_credentials"("p_credentials" "jsonb", "p_encryption_key" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."encrypt_data_source_credentials"("p_credentials" "jsonb", "p_encryption_key" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."encrypt_data_source_credentials"("p_credentials" "jsonb", "p_encryption_key" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."exec_sql"("sql_query" "text", "query_params" "json") TO "anon";
GRANT ALL ON FUNCTION "public"."exec_sql"("sql_query" "text", "query_params" "json") TO "authenticated";
GRANT ALL ON FUNCTION "public"."exec_sql"("sql_query" "text", "query_params" "json") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_domain_entity_types"("domain_name" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."get_domain_entity_types"("domain_name" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_domain_entity_types"("domain_name" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_domain_relationship_types"("domain_name" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."get_domain_relationship_types"("domain_name" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_domain_relationship_types"("domain_name" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_entity_type_id"("type_name" "text", "domain_name" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."get_entity_type_id"("type_name" "text", "domain_name" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_entity_type_id"("type_name" "text", "domain_name" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_relationship_type_id"("type_name" "text", "domain_name" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."get_relationship_type_id"("type_name" "text", "domain_name" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_relationship_type_id"("type_name" "text", "domain_name" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_rule_performance_metrics"("rule_ids" "uuid"[]) TO "anon";
GRANT ALL ON FUNCTION "public"."get_rule_performance_metrics"("rule_ids" "uuid"[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_rule_performance_metrics"("rule_ids" "uuid"[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."get_step_dependencies"("step_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."get_step_dependencies"("step_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_step_dependencies"("step_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_user_permissions"("user_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."get_user_permissions"("user_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_user_permissions"("user_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_validation_summary"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_validation_summary"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_validation_summary"() TO "service_role";



GRANT ALL ON FUNCTION "public"."gin_extract_query_trgm"("text", "internal", smallint, "internal", "internal", "internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gin_extract_query_trgm"("text", "internal", smallint, "internal", "internal", "internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gin_extract_query_trgm"("text", "internal", smallint, "internal", "internal", "internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gin_extract_query_trgm"("text", "internal", smallint, "internal", "internal", "internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gin_extract_value_trgm"("text", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gin_extract_value_trgm"("text", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gin_extract_value_trgm"("text", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gin_extract_value_trgm"("text", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gin_trgm_consistent"("internal", smallint, "text", integer, "internal", "internal", "internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gin_trgm_consistent"("internal", smallint, "text", integer, "internal", "internal", "internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gin_trgm_consistent"("internal", smallint, "text", integer, "internal", "internal", "internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gin_trgm_consistent"("internal", smallint, "text", integer, "internal", "internal", "internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gin_trgm_triconsistent"("internal", smallint, "text", integer, "internal", "internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gin_trgm_triconsistent"("internal", smallint, "text", integer, "internal", "internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gin_trgm_triconsistent"("internal", smallint, "text", integer, "internal", "internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gin_trgm_triconsistent"("internal", smallint, "text", integer, "internal", "internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_compress"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_compress"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_compress"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_compress"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_consistent"("internal", "text", smallint, "oid", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_consistent"("internal", "text", smallint, "oid", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_consistent"("internal", "text", smallint, "oid", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_consistent"("internal", "text", smallint, "oid", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_decompress"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_decompress"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_decompress"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_decompress"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_distance"("internal", "text", smallint, "oid", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_distance"("internal", "text", smallint, "oid", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_distance"("internal", "text", smallint, "oid", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_distance"("internal", "text", smallint, "oid", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_options"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_options"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_options"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_options"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_penalty"("internal", "internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_penalty"("internal", "internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_penalty"("internal", "internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_penalty"("internal", "internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_picksplit"("internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_picksplit"("internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_picksplit"("internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_picksplit"("internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_same"("public"."gtrgm", "public"."gtrgm", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_same"("public"."gtrgm", "public"."gtrgm", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_same"("public"."gtrgm", "public"."gtrgm", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_same"("public"."gtrgm", "public"."gtrgm", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_union"("internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_union"("internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_union"("internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_union"("internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_accum"(double precision[], "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_accum"(double precision[], "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_accum"(double precision[], "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_accum"(double precision[], "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_add"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_add"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_add"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_add"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_avg"(double precision[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_avg"(double precision[]) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_avg"(double precision[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_avg"(double precision[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_cmp"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_cmp"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_cmp"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_cmp"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_combine"(double precision[], double precision[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_combine"(double precision[], double precision[]) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_combine"(double precision[], double precision[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_combine"(double precision[], double precision[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_concat"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_concat"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_concat"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_concat"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_eq"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_eq"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_eq"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_eq"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_ge"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_ge"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_ge"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_ge"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_gt"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_gt"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_gt"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_gt"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_l2_squared_distance"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_l2_squared_distance"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_l2_squared_distance"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_l2_squared_distance"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_le"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_le"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_le"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_le"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_lt"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_lt"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_lt"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_lt"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_mul"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_mul"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_mul"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_mul"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_ne"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_ne"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_ne"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_ne"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_negative_inner_product"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_negative_inner_product"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_negative_inner_product"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_negative_inner_product"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_spherical_distance"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_spherical_distance"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_spherical_distance"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_spherical_distance"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_sub"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_sub"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_sub"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_sub"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."hamming_distance"(bit, bit) TO "postgres";
GRANT ALL ON FUNCTION "public"."hamming_distance"(bit, bit) TO "anon";
GRANT ALL ON FUNCTION "public"."hamming_distance"(bit, bit) TO "authenticated";
GRANT ALL ON FUNCTION "public"."hamming_distance"(bit, bit) TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "service_role";



GRANT ALL ON FUNCTION "public"."hnsw_bit_support"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."hnsw_bit_support"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."hnsw_bit_support"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."hnsw_bit_support"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."hnsw_halfvec_support"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."hnsw_halfvec_support"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."hnsw_halfvec_support"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."hnsw_halfvec_support"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."hnsw_sparsevec_support"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."hnsw_sparsevec_support"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."hnsw_sparsevec_support"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."hnsw_sparsevec_support"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."hnswhandler"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."hnswhandler"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."hnswhandler"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."hnswhandler"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."inner_product"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."inner_product"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."inner_product"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."ivfflat_bit_support"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."ivfflat_bit_support"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."ivfflat_bit_support"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."ivfflat_bit_support"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."ivfflat_halfvec_support"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."ivfflat_halfvec_support"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."ivfflat_halfvec_support"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."ivfflat_halfvec_support"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."ivfflathandler"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."ivfflathandler"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."ivfflathandler"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."ivfflathandler"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."jaccard_distance"(bit, bit) TO "postgres";
GRANT ALL ON FUNCTION "public"."jaccard_distance"(bit, bit) TO "anon";
GRANT ALL ON FUNCTION "public"."jaccard_distance"(bit, bit) TO "authenticated";
GRANT ALL ON FUNCTION "public"."jaccard_distance"(bit, bit) TO "service_role";



GRANT ALL ON FUNCTION "public"."l1_distance"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l1_distance"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l1_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_distance"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_distance"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_norm"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_norm"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_norm"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_norm"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_norm"("public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_norm"("public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_norm"("public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_norm"("public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."log_user_activity"("p_user_id" "uuid", "p_action" "text", "p_resource_type" "text", "p_resource_id" "uuid", "p_ip_address" "inet", "p_user_agent" "text", "p_details" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."log_user_activity"("p_user_id" "uuid", "p_action" "text", "p_resource_type" "text", "p_resource_id" "uuid", "p_ip_address" "inet", "p_user_agent" "text", "p_details" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."log_user_activity"("p_user_id" "uuid", "p_action" "text", "p_resource_type" "text", "p_resource_id" "uuid", "p_ip_address" "inet", "p_user_agent" "text", "p_details" "jsonb") TO "service_role";



GRANT ALL ON FUNCTION "public"."migrate_entity_types"() TO "anon";
GRANT ALL ON FUNCTION "public"."migrate_entity_types"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."migrate_entity_types"() TO "service_role";



GRANT ALL ON FUNCTION "public"."migrate_relationship_types"() TO "anon";
GRANT ALL ON FUNCTION "public"."migrate_relationship_types"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."migrate_relationship_types"() TO "service_role";



GRANT ALL ON FUNCTION "public"."set_limit"(real) TO "postgres";
GRANT ALL ON FUNCTION "public"."set_limit"(real) TO "anon";
GRANT ALL ON FUNCTION "public"."set_limit"(real) TO "authenticated";
GRANT ALL ON FUNCTION "public"."set_limit"(real) TO "service_role";



GRANT ALL ON FUNCTION "public"."show_limit"() TO "postgres";
GRANT ALL ON FUNCTION "public"."show_limit"() TO "anon";
GRANT ALL ON FUNCTION "public"."show_limit"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."show_limit"() TO "service_role";



GRANT ALL ON FUNCTION "public"."show_trgm"("text") TO "postgres";
GRANT ALL ON FUNCTION "public"."show_trgm"("text") TO "anon";
GRANT ALL ON FUNCTION "public"."show_trgm"("text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."show_trgm"("text") TO "service_role";



GRANT ALL ON FUNCTION "public"."similarity"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."similarity"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."similarity"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."similarity"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."similarity_dist"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."similarity_dist"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."similarity_dist"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."similarity_dist"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."similarity_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."similarity_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."similarity_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."similarity_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_cmp"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_cmp"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_cmp"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_cmp"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_eq"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_eq"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_eq"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_eq"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_ge"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_ge"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_ge"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_ge"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_gt"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_gt"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_gt"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_gt"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_l2_squared_distance"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_l2_squared_distance"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_l2_squared_distance"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_l2_squared_distance"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_le"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_le"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_le"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_le"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_lt"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_lt"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_lt"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_lt"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_ne"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_ne"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_ne"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_ne"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_negative_inner_product"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_negative_inner_product"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_negative_inner_product"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_negative_inner_product"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity_commutator_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_commutator_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_commutator_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_commutator_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_commutator_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_commutator_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_commutator_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_commutator_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."subvector"("public"."halfvec", integer, integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."subvector"("public"."halfvec", integer, integer) TO "anon";
GRANT ALL ON FUNCTION "public"."subvector"("public"."halfvec", integer, integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."subvector"("public"."halfvec", integer, integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."subvector"("public"."vector", integer, integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."subvector"("public"."vector", integer, integer) TO "anon";
GRANT ALL ON FUNCTION "public"."subvector"("public"."vector", integer, integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."subvector"("public"."vector", integer, integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."track_entity_change"() TO "anon";
GRANT ALL ON FUNCTION "public"."track_entity_change"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."track_entity_change"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_rule_statistics"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_rule_statistics"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_rule_statistics"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_timestamp"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_timestamp"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_timestamp"() TO "service_role";



GRANT ALL ON FUNCTION "public"."user_has_role"("user_id" "uuid", "role_name" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."user_has_role"("user_id" "uuid", "role_name" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."user_has_role"("user_id" "uuid", "role_name" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."validate_relationship_types"() TO "anon";
GRANT ALL ON FUNCTION "public"."validate_relationship_types"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."validate_relationship_types"() TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_accum"(double precision[], "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_accum"(double precision[], "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_accum"(double precision[], "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_accum"(double precision[], "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_add"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_add"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_add"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_add"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_avg"(double precision[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_avg"(double precision[]) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_avg"(double precision[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_avg"(double precision[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_cmp"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_cmp"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_cmp"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_cmp"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_combine"(double precision[], double precision[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_combine"(double precision[], double precision[]) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_combine"(double precision[], double precision[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_combine"(double precision[], double precision[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_concat"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_concat"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_concat"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_concat"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_dims"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_dims"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_eq"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_eq"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_eq"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_eq"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_ge"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_ge"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_ge"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_ge"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_gt"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_gt"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_gt"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_gt"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_l2_squared_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_l2_squared_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_l2_squared_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_l2_squared_distance"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_le"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_le"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_le"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_le"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_lt"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_lt"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_lt"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_lt"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_mul"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_mul"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_mul"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_mul"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_ne"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_ne"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_ne"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_ne"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_negative_inner_product"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_negative_inner_product"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_negative_inner_product"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_negative_inner_product"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_norm"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_norm"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_norm"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_norm"("public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_spherical_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_spherical_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_spherical_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_spherical_distance"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_sub"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_sub"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_sub"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_sub"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity_commutator_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity_commutator_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity_commutator_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity_commutator_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity_dist_commutator_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_commutator_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_commutator_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_commutator_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity_dist_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity_op"("text", "text") TO "service_role";












GRANT ALL ON FUNCTION "public"."avg"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."avg"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."avg"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."avg"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."avg"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."avg"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."avg"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."avg"("public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."sum"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sum"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."sum"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sum"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sum"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."sum"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."sum"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sum"("public"."vector") TO "service_role";









GRANT ALL ON TABLE "public"."api_keys" TO "anon";
GRANT ALL ON TABLE "public"."api_keys" TO "authenticated";
GRANT ALL ON TABLE "public"."api_keys" TO "service_role";



GRANT ALL ON TABLE "public"."api_usage_log" TO "anon";
GRANT ALL ON TABLE "public"."api_usage_log" TO "authenticated";
GRANT ALL ON TABLE "public"."api_usage_log" TO "service_role";



GRANT ALL ON TABLE "public"."conflicts" TO "anon";
GRANT ALL ON TABLE "public"."conflicts" TO "authenticated";
GRANT ALL ON TABLE "public"."conflicts" TO "service_role";



GRANT ALL ON TABLE "public"."data_sources" TO "anon";
GRANT ALL ON TABLE "public"."data_sources" TO "authenticated";
GRANT ALL ON TABLE "public"."data_sources" TO "service_role";



GRANT ALL ON TABLE "public"."extraction_results" TO "anon";
GRANT ALL ON TABLE "public"."extraction_results" TO "authenticated";
GRANT ALL ON TABLE "public"."extraction_results" TO "service_role";



GRANT ALL ON TABLE "public"."file_uploads" TO "anon";
GRANT ALL ON TABLE "public"."file_uploads" TO "authenticated";
GRANT ALL ON TABLE "public"."file_uploads" TO "service_role";



GRANT ALL ON TABLE "public"."kg_edit_logs" TO "anon";
GRANT ALL ON TABLE "public"."kg_edit_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."kg_edit_logs" TO "service_role";



GRANT ALL ON TABLE "public"."kg_entities" TO "anon";
GRANT ALL ON TABLE "public"."kg_entities" TO "authenticated";
GRANT ALL ON TABLE "public"."kg_entities" TO "service_role";



GRANT ALL ON TABLE "public"."kg_relationships" TO "anon";
GRANT ALL ON TABLE "public"."kg_relationships" TO "authenticated";
GRANT ALL ON TABLE "public"."kg_relationships" TO "service_role";



GRANT ALL ON TABLE "public"."notifications" TO "anon";
GRANT ALL ON TABLE "public"."notifications" TO "authenticated";
GRANT ALL ON TABLE "public"."notifications" TO "service_role";



GRANT ALL ON TABLE "public"."ontology_classes" TO "anon";
GRANT ALL ON TABLE "public"."ontology_classes" TO "authenticated";
GRANT ALL ON TABLE "public"."ontology_classes" TO "service_role";



GRANT ALL ON SEQUENCE "public"."ontology_classes_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."ontology_classes_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."ontology_classes_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."ontology_properties" TO "anon";
GRANT ALL ON TABLE "public"."ontology_properties" TO "authenticated";
GRANT ALL ON TABLE "public"."ontology_properties" TO "service_role";



GRANT ALL ON SEQUENCE "public"."ontology_properties_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."ontology_properties_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."ontology_properties_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."permissions" TO "anon";
GRANT ALL ON TABLE "public"."permissions" TO "authenticated";
GRANT ALL ON TABLE "public"."permissions" TO "service_role";



GRANT ALL ON SEQUENCE "public"."permissions_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."permissions_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."permissions_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."pipeline_runs" TO "anon";
GRANT ALL ON TABLE "public"."pipeline_runs" TO "authenticated";
GRANT ALL ON TABLE "public"."pipeline_runs" TO "service_role";



GRANT ALL ON TABLE "public"."pipeline_step_runs" TO "anon";
GRANT ALL ON TABLE "public"."pipeline_step_runs" TO "authenticated";
GRANT ALL ON TABLE "public"."pipeline_step_runs" TO "service_role";



GRANT ALL ON TABLE "public"."pipeline_steps" TO "anon";
GRANT ALL ON TABLE "public"."pipeline_steps" TO "authenticated";
GRANT ALL ON TABLE "public"."pipeline_steps" TO "service_role";



GRANT ALL ON TABLE "public"."pipelines" TO "anon";
GRANT ALL ON TABLE "public"."pipelines" TO "authenticated";
GRANT ALL ON TABLE "public"."pipelines" TO "service_role";



GRANT ALL ON TABLE "public"."profiles" TO "anon";
GRANT ALL ON TABLE "public"."profiles" TO "authenticated";
GRANT ALL ON TABLE "public"."profiles" TO "service_role";



GRANT ALL ON TABLE "public"."quality_assessments" TO "anon";
GRANT ALL ON TABLE "public"."quality_assessments" TO "authenticated";
GRANT ALL ON TABLE "public"."quality_assessments" TO "service_role";



GRANT ALL ON TABLE "public"."quality_monitoring_runs" TO "anon";
GRANT ALL ON TABLE "public"."quality_monitoring_runs" TO "authenticated";
GRANT ALL ON TABLE "public"."quality_monitoring_runs" TO "service_role";



GRANT ALL ON TABLE "public"."rate_limiter_logs" TO "anon";
GRANT ALL ON TABLE "public"."rate_limiter_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."rate_limiter_logs" TO "service_role";



GRANT ALL ON TABLE "public"."role_permissions" TO "anon";
GRANT ALL ON TABLE "public"."role_permissions" TO "authenticated";
GRANT ALL ON TABLE "public"."role_permissions" TO "service_role";



GRANT ALL ON SEQUENCE "public"."role_permissions_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."role_permissions_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."role_permissions_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."roles" TO "anon";
GRANT ALL ON TABLE "public"."roles" TO "authenticated";
GRANT ALL ON TABLE "public"."roles" TO "service_role";



GRANT ALL ON SEQUENCE "public"."roles_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."roles_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."roles_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."saved_queries" TO "anon";
GRANT ALL ON TABLE "public"."saved_queries" TO "authenticated";
GRANT ALL ON TABLE "public"."saved_queries" TO "service_role";



GRANT ALL ON TABLE "public"."user_activity_log" TO "anon";
GRANT ALL ON TABLE "public"."user_activity_log" TO "authenticated";
GRANT ALL ON TABLE "public"."user_activity_log" TO "service_role";



GRANT ALL ON TABLE "public"."user_roles" TO "anon";
GRANT ALL ON TABLE "public"."user_roles" TO "authenticated";
GRANT ALL ON TABLE "public"."user_roles" TO "service_role";



GRANT ALL ON SEQUENCE "public"."user_roles_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."user_roles_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."user_roles_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."visualizations" TO "anon";
GRANT ALL ON TABLE "public"."visualizations" TO "authenticated";
GRANT ALL ON TABLE "public"."visualizations" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "service_role";






























RESET ALL;

--
-- Dumped schema changes for auth and storage
--

CREATE OR REPLACE TRIGGER "on_auth_user_created" AFTER INSERT ON "auth"."users" FOR EACH ROW EXECUTE FUNCTION "public"."handle_new_user"();



