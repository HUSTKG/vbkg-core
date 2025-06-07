-- Drop existing function if exists
DROP FUNCTION IF EXISTS exec_sql(text, json);

-- Main exec_sql function that can be called via RPC
CREATE OR REPLACE FUNCTION exec_sql(
  sql_query TEXT,
  query_params JSON DEFAULT '[]'::json
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result_json JSON;
  execution_start TIMESTAMP;
  execution_end TIMESTAMP;
  execution_time NUMERIC;
  affected_rows INTEGER DEFAULT 0;
  result_data JSON DEFAULT '[]'::json;
  error_message TEXT;
  sql_query TEXT;
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

