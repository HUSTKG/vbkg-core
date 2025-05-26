-- =============================================
-- VALIDATION RULES SYSTEM MIGRATION
-- =============================================

-- Create validation rules table
CREATE TABLE IF NOT EXISTS public.validation_rules (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL CHECK (category IN (
        'completeness', 'accuracy', 'consistency', 'validity', 
        'uniqueness', 'timeliness', 'relevance'
    )),
    rule_type TEXT NOT NULL CHECK (rule_type IN (
        'field_validation', 'format_validation', 'business_logic',
        'uniqueness_check', 'relationship_validation', 'custom_validation'
    )),
    is_active BOOLEAN DEFAULT TRUE,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    
    -- Target scope
    target_entity_types TEXT[] NOT NULL DEFAULT ARRAY['*'], -- '*' means all types
    target_relationship_types TEXT[],
    
    -- Rule conditions (JSON structure for flexibility)
    conditions JSONB NOT NULL,
    error_message TEXT NOT NULL,
    
    -- Execution configuration
    execution_mode TEXT NOT NULL DEFAULT 'on_demand' CHECK (execution_mode IN (
        'on_demand', 'real_time', 'batch', 'scheduled'
    )),
    batch_size INTEGER DEFAULT 100,
    timeout_seconds INTEGER DEFAULT 300,
    
    -- Performance tracking
    execution_count INTEGER DEFAULT 0,
    violation_count INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 1.0,
    last_executed_at TIMESTAMP WITH TIME ZONE,
    average_execution_time INTEGER, -- milliseconds
    
    -- Rule metadata
    tags TEXT[],
    documentation TEXT,
    examples JSONB,
    
    -- Audit fields
    created_by UUID REFERENCES auth.users(id),
    updated_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Create validation rule executions table
CREATE TABLE IF NOT EXISTS public.validation_rule_executions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    rule_id UUID REFERENCES public.validation_rules(id) ON DELETE CASCADE,
    pipeline_run_id UUID REFERENCES public.pipeline_runs(id) ON DELETE SET NULL,
    
    -- Execution details
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    execution_time INTEGER, -- milliseconds
    
    -- Results
    entities_checked INTEGER DEFAULT 0,
    relationships_checked INTEGER DEFAULT 0,
    violations_found INTEGER DEFAULT 0,
    violations_details JSONB,
    
    -- Error handling
    error_message TEXT,
    stack_trace TEXT,
    
    -- Context
    triggered_by TEXT, -- 'manual', 'pipeline', 'scheduled', 'api'
    execution_context JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Create validation violations table
CREATE TABLE IF NOT EXISTS public.validation_violations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    rule_execution_id UUID REFERENCES public.validation_rule_executions(id) ON DELETE CASCADE,
    rule_id UUID REFERENCES public.validation_rules(id) ON DELETE CASCADE,
    
    -- Violation target
    entity_id UUID REFERENCES public.kg_entities(id) ON DELETE CASCADE,
    relationship_id UUID REFERENCES public.kg_relationships(id) ON DELETE CASCADE,
    
    -- Violation details
    violation_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    message TEXT NOT NULL,
    field_name TEXT,
    expected_value TEXT,
    actual_value TEXT,
    
    -- Resolution
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'ignored', 'false_positive')),
    resolution_action TEXT,
    resolved_by UUID REFERENCES auth.users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    
    -- Additional context
    context_data JSONB,
    suggestions JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Create rule templates table for common patterns
CREATE TABLE IF NOT EXISTS public.validation_rule_templates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    
    -- Template structure
    conditions_template JSONB NOT NULL,
    default_severity TEXT NOT NULL,
    default_error_message TEXT NOT NULL,
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    is_builtin BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    tags TEXT[],
    documentation TEXT,
    examples JSONB,
    
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================

-- Validation rules indexes
CREATE INDEX IF NOT EXISTS idx_validation_rules_category ON public.validation_rules(category);
CREATE INDEX IF NOT EXISTS idx_validation_rules_rule_type ON public.validation_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_validation_rules_is_active ON public.validation_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_validation_rules_severity ON public.validation_rules(severity);
CREATE INDEX IF NOT EXISTS idx_validation_rules_target_entity_types ON public.validation_rules USING GIN(target_entity_types);
CREATE INDEX IF NOT EXISTS idx_validation_rules_tags ON public.validation_rules USING GIN(tags);

-- Rule executions indexes
CREATE INDEX IF NOT EXISTS idx_validation_rule_executions_rule_id ON public.validation_rule_executions(rule_id);
CREATE INDEX IF NOT EXISTS idx_validation_rule_executions_status ON public.validation_rule_executions(status);
CREATE INDEX IF NOT EXISTS idx_validation_rule_executions_start_time ON public.validation_rule_executions(start_time);
CREATE INDEX IF NOT EXISTS idx_validation_rule_executions_pipeline_run_id ON public.validation_rule_executions(pipeline_run_id);

-- Violations indexes
CREATE INDEX IF NOT EXISTS idx_validation_violations_rule_id ON public.validation_violations(rule_id);
CREATE INDEX IF NOT EXISTS idx_validation_violations_entity_id ON public.validation_violations(entity_id);
CREATE INDEX IF NOT EXISTS idx_validation_violations_relationship_id ON public.validation_violations(relationship_id);
CREATE INDEX IF NOT EXISTS idx_validation_violations_status ON public.validation_violations(status);
CREATE INDEX IF NOT EXISTS idx_validation_violations_severity ON public.validation_violations(severity);
CREATE INDEX IF NOT EXISTS idx_validation_violations_created_at ON public.validation_violations(created_at);

-- =============================================
-- FUNCTIONS & TRIGGERS
-- =============================================

-- Function to update rule statistics
CREATE OR REPLACE FUNCTION public.update_rule_statistics()
RETURNS TRIGGER AS $$
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
$$ LANGUAGE plpgsql;

-- Trigger to update statistics
CREATE TRIGGER update_rule_statistics_trigger
    AFTER INSERT OR UPDATE ON public.validation_rule_executions
    FOR EACH ROW 
    EXECUTE FUNCTION public.update_rule_statistics();

-- Function to get rule performance metrics
CREATE OR REPLACE FUNCTION public.get_rule_performance_metrics(rule_ids UUID[] DEFAULT NULL)
RETURNS TABLE(
    rule_id UUID,
    rule_name TEXT,
    total_executions BIGINT,
    avg_execution_time FLOAT,
    total_violations BIGINT,
    success_rate FLOAT,
    last_executed TIMESTAMP WITH TIME ZONE
) AS $$
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
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get validation summary for quality dashboard
CREATE OR REPLACE FUNCTION public.get_validation_summary()
RETURNS TABLE(
    total_rules INTEGER,
    active_rules INTEGER,
    recent_violations BIGINT,
    avg_success_rate FLOAT,
    critical_violations BIGINT
) AS $$
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
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- ROW LEVEL SECURITY POLICIES
-- =============================================

-- Enable RLS
ALTER TABLE public.validation_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.validation_rule_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.validation_violations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.validation_rule_templates ENABLE ROW LEVEL SECURITY;

-- Validation rules policies
CREATE POLICY "Quality experts can manage validation rules" ON public.validation_rules
    FOR ALL USING (public.check_user_permission(auth.uid(), 'quality:expert'));

CREATE POLICY "Users can view validation rules" ON public.validation_rules
    FOR SELECT USING (public.check_user_permission(auth.uid(), 'quality:read'));

-- Rule executions policies  
CREATE POLICY "Quality experts can view rule executions" ON public.validation_rule_executions
    FOR SELECT USING (public.check_user_permission(auth.uid(), 'quality:expert'));

CREATE POLICY "System can create rule executions" ON public.validation_rule_executions
    FOR INSERT WITH CHECK (true); -- System processes

-- Violations policies
CREATE POLICY "Quality experts can manage violations" ON public.validation_violations
    FOR ALL USING (public.check_user_permission(auth.uid(), 'quality:expert'));

CREATE POLICY "Users can view violations" ON public.validation_violations
    FOR SELECT USING (public.check_user_permission(auth.uid(), 'quality:read'));

-- Templates policies
CREATE POLICY "Quality experts can manage templates" ON public.validation_rule_templates
    FOR ALL USING (public.check_user_permission(auth.uid(), 'quality:expert'));

CREATE POLICY "Users can view templates" ON public.validation_rule_templates
    FOR SELECT USING (public.check_user_permission(auth.uid(), 'quality:read'));

-- =============================================
-- INSERT BUILTIN RULE TEMPLATES
-- =============================================

INSERT INTO public.validation_rule_templates (name, description, category, rule_type, conditions_template, default_severity, default_error_message, is_builtin, tags, documentation) VALUES 

-- Completeness templates
('Required Field Check', 'Ensures required fields are not empty or null', 'completeness', 'field_validation', 
'{"field": "", "operator": "not_empty", "value": null}', 'high', 'Required field is missing or empty', 
true, ARRAY['required', 'completeness'], 'Validates that specified fields contain non-empty values'),

('Minimum Length Check', 'Validates minimum length for text fields', 'completeness', 'field_validation',
'{"field": "", "operator": "min_length", "value": 1}', 'medium', 'Field does not meet minimum length requirement',
true, ARRAY['length', 'completeness'], 'Ensures text fields meet minimum character requirements'),

-- Validity templates  
('Email Format', 'Validates email address format', 'validity', 'format_validation',
'{"field": "email", "operator": "matches_pattern", "value": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}', 'medium', 'Invalid email format',
true, ARRAY['email', 'format'], 'Validates email addresses using regex pattern'),

('Date Format', 'Validates date format (YYYY-MM-DD)', 'validity', 'format_validation',
'{"field": "", "operator": "matches_pattern", "value": "^\\d{4}-\\d{2}-\\d{2}$"}', 'medium', 'Invalid date format',
true, ARRAY['date', 'format'], 'Validates dates in ISO format'),

('Phone Number', 'Validates phone number format', 'validity', 'format_validation',
'{"field": "phone", "operator": "matches_pattern", "value": "^[+]?[1-9]?[0-9]{7,15}$"}', 'low', 'Invalid phone number format',
true, ARRAY['phone', 'format'], 'Validates international phone number formats'),

-- Uniqueness templates
('Unique Entity Name', 'Ensures entity names are unique within type', 'uniqueness', 'uniqueness_check',
'{"field": "name", "operator": "unique", "scope": "entity_type"}', 'critical', 'Entity name must be unique within its type',
true, ARRAY['unique', 'name'], 'Prevents duplicate entity names within the same entity type'),

('Unique Identifier', 'Ensures identifiers are globally unique', 'uniqueness', 'uniqueness_check',
'{"field": "identifier", "operator": "unique", "scope": "global"}', 'critical', 'Identifier must be globally unique',
true, ARRAY['unique', 'identifier'], 'Ensures identifiers are unique across all entities'),

-- Consistency templates
('Date Range Validation', 'Ensures start date is before end date', 'consistency', 'business_logic',
'{"start_field": "start_date", "end_field": "end_date", "operator": "date_range"}', 'high', 'Start date must be before end date',
true, ARRAY['date', 'range', 'consistency'], 'Validates that date ranges are logically consistent'),

('Relationship Consistency', 'Validates relationship logical consistency', 'consistency', 'relationship_validation',
'{"relationship_type": "", "validation_rules": []}', 'medium', 'Relationship violates consistency rules',
true, ARRAY['relationship', 'consistency'], 'Ensures relationships follow business logic rules');

-- =============================================
-- SAMPLE VALIDATION RULES FOR DEMO
-- =============================================

INSERT INTO public.validation_rules (name, description, category, rule_type, severity, target_entity_types, conditions, error_message, created_by) VALUES 

('Entity Name Required', 'All entities must have a non-empty name', 'completeness', 'field_validation', 'high', ARRAY['*'],
'{"field": "entity_text", "operator": "not_empty", "value": null}', 'Entity name cannot be empty', 
(SELECT id FROM auth.users LIMIT 1)),

('Email Format Validation', 'Email fields must have valid format', 'validity', 'format_validation', 'medium', ARRAY['PERSON', 'ORGANIZATION'],
'{"field": "email", "operator": "matches_pattern", "value": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}', 'Invalid email format',
(SELECT id FROM auth.users LIMIT 1)),

('Date of Birth Future Check', 'Date of birth cannot be in the future', 'consistency', 'business_logic', 'high', ARRAY['PERSON'],
'{"field": "date_of_birth", "operator": "less_than", "value": "CURRENT_DATE"}', 'Date of birth cannot be in the future',
(SELECT id FROM auth.users LIMIT 1)),

('Organization Name Uniqueness', 'Organization names must be unique', 'uniqueness', 'uniqueness_check', 'critical', ARRAY['ORGANIZATION'],
'{"field": "name", "operator": "unique", "scope": "entity_type"}', 'Organization name must be unique',
(SELECT id FROM auth.users LIMIT 1));

-- Update trigger for updated_at
CREATE TRIGGER update_validation_rules_timestamp
    BEFORE UPDATE ON public.validation_rules
    FOR EACH ROW EXECUTE PROCEDURE public.update_timestamp();

CREATE TRIGGER update_validation_violations_timestamp
    BEFORE UPDATE ON public.validation_violations
    FOR EACH ROW EXECUTE PROCEDURE public.update_timestamp();

CREATE TRIGGER update_validation_rule_templates_timestamp
    BEFORE UPDATE ON public.validation_rule_templates  
    FOR EACH ROW EXECUTE PROCEDURE public.update_timestamp();
