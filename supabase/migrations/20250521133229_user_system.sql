-- =============================================
-- ENHANCE EXISTING DATABASE FOR KNOWLEDGE GRAPH SYSTEM
-- =============================================

-- Update existing roles with KG-specific roles
UPDATE public.roles SET description = 'System Administrator with full access to all features' WHERE name = 'admin';
UPDATE public.roles SET name = 'expert', description = 'Domain Expert with data management and conflict resolution permissions' WHERE name = 'editor';
UPDATE public.roles SET name = 'user', description = 'End User with read access and API usage' WHERE name = 'viewer';

-- Insert any missing roles
INSERT INTO public.roles (name, description) VALUES 
('expert', 'Domain Expert with data management and conflict resolution permissions'),
('user', 'End User with read access and API usage')
ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description;

-- Clear existing permissions and insert KG-specific permissions
DELETE FROM public.role_permissions;
DELETE FROM public.permissions;

-- Insert Knowledge Graph specific permissions
INSERT INTO public.permissions (name, description) VALUES 
-- Data source permissions
('datasource:read', 'View data sources'),
('datasource:write', 'Create and edit data sources'),
('datasource:delete', 'Delete data sources'),

-- Pipeline permissions  
('pipeline:read', 'View pipelines'),
('pipeline:write', 'Create and edit pipelines'),
('pipeline:execute', 'Execute pipelines'),
('pipeline:delete', 'Delete pipelines'),

-- Knowledge graph permissions
('kg:read', 'View knowledge graph data'),
('kg:search', 'Search knowledge graph'),
('kg:edit', 'Edit knowledge graph entities/relationships'),
('kg:delete', 'Delete knowledge graph data'),

-- Quality & conflict permissions
('quality:read', 'View quality metrics and reports'),
('quality:expert', 'Resolve conflicts and manage quality'),
('quality:admin', 'Advanced quality management'),

-- System administration
('user:management', 'Manage users and roles'),
('system:config', 'Configure system settings'),
('system:monitoring', 'Monitor system performance'),

-- API access
('api:access', 'Access API endpoints'),
('api:unlimited', 'Unlimited API access');

-- Assign permissions to roles
-- Admin gets all permissions
INSERT INTO public.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM public.roles r, public.permissions p WHERE r.name = 'admin';

-- Expert permissions
INSERT INTO public.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM public.roles r, public.permissions p 
WHERE r.name = 'expert' AND p.name IN (
    'kg:read', 'kg:search', 'api:access',
    'datasource:read', 'datasource:write',
    'pipeline:read', 'pipeline:write', 'pipeline:execute',
    'kg:edit', 'quality:read', 'quality:expert'
);

-- User permissions
INSERT INTO public.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM public.roles r, public.permissions p 
WHERE r.name = 'user' AND p.name IN (
    'kg:read', 'kg:search', 'api:access'
);

-- =============================================
-- ADD NEW TABLES FOR ENHANCED FUNCTIONALITY
-- =============================================

-- API Keys table
CREATE TABLE IF NOT EXISTS public.api_keys (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    key_hash TEXT NOT NULL UNIQUE,
    key_prefix TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    rate_limit INTEGER DEFAULT 1000,
    allowed_ips TEXT[],
    last_used TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- User activity log
CREATE TABLE IF NOT EXISTS public.user_activity_log (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- API usage tracking
CREATE TABLE IF NOT EXISTS public.api_usage_log (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    api_key_id UUID REFERENCES public.api_keys(id) ON DELETE SET NULL,
    method TEXT,
    path TEXT,
    status_code INTEGER,
    response_time FLOAT,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Pipeline steps (separate from pipeline config)
CREATE TABLE IF NOT EXISTS public.pipeline_steps (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    pipeline_id UUID REFERENCES public.pipelines(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    step_type TEXT NOT NULL CHECK (step_type IN (
        'file_reader', 'api_fetcher', 'database_extractor', 'text_extractor',
        'llm_entity_extractor', 'fibo_mapper', 'entity_resolution', 
        'knowledge_graph_writer', 'custom_python', 'data_validation',
        'data_transformation', 'conflict_detection', 'auto_resolution'
    )),
    config JSONB NOT NULL,
    run_order INTEGER NOT NULL,
    inputs TEXT, -- Comma-separated IDs of input steps
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Pipeline step runs (execution tracking)
CREATE TABLE IF NOT EXISTS public.pipeline_step_runs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    pipeline_run_id UUID REFERENCES public.pipeline_runs(id) ON DELETE CASCADE,
    step_id UUID REFERENCES public.pipeline_steps(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    run_order INTEGER NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    celery_task_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Enhanced conflicts table (replacing entity_conflicts)
DROP TABLE IF EXISTS public.entity_conflicts;

CREATE TABLE IF NOT EXISTS public.conflicts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    conflict_type TEXT NOT NULL CHECK (conflict_type IN (
        'duplicate_entity', 'contradictory_relationship', 'missing_relationship',
        'attribute_mismatch', 'temporal_conflict', 'source_conflict', 'schema_mismatch'
    )),
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status TEXT NOT NULL DEFAULT 'detected' CHECK (status IN (
        'detected', 'under_review', 'resolved_manual', 'resolved_auto', 'rejected', 'escalated'
    )),
    description TEXT NOT NULL,
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- Related entities/relationships
    source_entity_id UUID REFERENCES public.kg_entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES public.kg_entities(id) ON DELETE CASCADE,
    source_relationship_id UUID REFERENCES public.kg_relationships(id) ON DELETE CASCADE,
    target_relationship_id UUID REFERENCES public.kg_relationships(id) ON DELETE CASCADE,
    
    -- Context and resolution
    conflicting_attributes JSONB,
    context_data JSONB,
    resolution_method TEXT,
    resolution_data JSONB,
    resolution_reasoning TEXT,
    
    -- Assignment and tracking
    detected_by TEXT NOT NULL, -- 'system', 'user', 'expert'
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
    assigned_to UUID REFERENCES auth.users(id),
    resolved_by TEXT, -- user_id or 'ai_system'
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata
    auto_resolution_attempted BOOLEAN DEFAULT FALSE,
    auto_resolution_suggestions JSONB,
    review_notes TEXT,
    escalation_reason TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Quality assessments
CREATE TABLE IF NOT EXISTS public.quality_assessments (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    entity_id UUID REFERENCES public.kg_entities(id) ON DELETE CASCADE,
    relationship_id UUID REFERENCES public.kg_relationships(id) ON DELETE CASCADE,
    dimension TEXT NOT NULL CHECK (dimension IN (
        'completeness', 'accuracy', 'consistency', 'validity', 
        'uniqueness', 'timeliness', 'relevance'
    )),
    score FLOAT NOT NULL CHECK (score >= 0 AND score <= 1),
    assessment_method TEXT NOT NULL, -- 'automatic', 'manual', 'rule_based'
    assessment_date TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
    details JSONB,
    improvement_suggestions TEXT[],
    created_by UUID REFERENCES auth.users(id)
);

-- Quality monitoring runs
CREATE TABLE IF NOT EXISTS public.quality_monitoring_runs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    overall_score FLOAT,
    dimension_scores JSONB,
    issues_detected INTEGER DEFAULT 0,
    conflicts_pending INTEGER DEFAULT 0,
    steps JSONB, -- Array of step results
    status TEXT CHECK (status IN ('running', 'completed', 'failed')),
    error_message TEXT
);

-- Knowledge graph edit logs
CREATE TABLE IF NOT EXISTS public.kg_edit_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    action TEXT NOT NULL, -- create_entity, update_entity, delete_entity, etc.
    resource_type TEXT, -- entity, relationship
    resource_id UUID,
    changes JSONB, -- What was changed
    reason TEXT,
    rollback_info JSONB, -- Information needed for rollback
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- =============================================
-- ENHANCE EXISTING TABLES
-- =============================================

-- Add missing columns to existing tables
ALTER TABLE public.kg_entities 
ADD COLUMN IF NOT EXISTS embedding VECTOR(1536), -- For vector similarity search
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS merged_into UUID REFERENCES public.kg_entities(id),
ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES auth.users(id),
ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES auth.users(id);

ALTER TABLE public.kg_relationships 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES auth.users(id),
ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES auth.users(id);

-- Update pipeline_runs to include celery task tracking
ALTER TABLE public.pipeline_runs 
ADD COLUMN IF NOT EXISTS celery_task_id TEXT,
ADD COLUMN IF NOT EXISTS result JSONB,
ADD COLUMN IF NOT EXISTS input_parameters JSONB;

-- Add pipeline run status if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'pipeline_runs_status_check'
    ) THEN
        ALTER TABLE public.pipeline_runs DROP CONSTRAINT IF EXISTS pipeline_runs_status_check;
        ALTER TABLE public.pipeline_runs ADD CONSTRAINT pipeline_runs_status_check 
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'));
    END IF;
END $$;

-- Update extraction_results to link with pipeline_step_runs
ALTER TABLE public.extraction_results 
ADD COLUMN IF NOT EXISTS step_run_id UUID REFERENCES public.pipeline_step_runs(id),
ADD COLUMN IF NOT EXISTS synced_to_graph BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS synced_at TIMESTAMP WITH TIME ZONE;

-- =============================================
-- CREATE INDEXES FOR PERFORMANCE
-- =============================================

-- API Keys indexes
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON public.api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON public.api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON public.api_keys(is_active);

-- Activity log indexes
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON public.user_activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_action ON public.user_activity_log(action);
CREATE INDEX IF NOT EXISTS idx_user_activity_created_at ON public.user_activity_log(created_at);

-- API usage indexes
CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON public.api_usage_log(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON public.api_usage_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_usage_path ON public.api_usage_log(path);

-- Pipeline steps indexes
CREATE INDEX IF NOT EXISTS idx_pipeline_steps_pipeline_id ON public.pipeline_steps(pipeline_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_steps_step_type ON public.pipeline_steps(step_type);
CREATE INDEX IF NOT EXISTS idx_pipeline_steps_run_order ON public.pipeline_steps(run_order);

-- Pipeline step runs indexes
CREATE INDEX IF NOT EXISTS idx_pipeline_step_runs_pipeline_run_id ON public.pipeline_step_runs(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_step_runs_step_id ON public.pipeline_step_runs(step_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_step_runs_status ON public.pipeline_step_runs(status);

-- Conflicts indexes
CREATE INDEX IF NOT EXISTS idx_conflicts_status ON public.conflicts(status);
CREATE INDEX IF NOT EXISTS idx_conflicts_conflict_type ON public.conflicts(conflict_type);
CREATE INDEX IF NOT EXISTS idx_conflicts_severity ON public.conflicts(severity);
CREATE INDEX IF NOT EXISTS idx_conflicts_assigned_to ON public.conflicts(assigned_to);
CREATE INDEX IF NOT EXISTS idx_conflicts_source_entity_id ON public.conflicts(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_target_entity_id ON public.conflicts(target_entity_id);

-- Quality assessments indexes
CREATE INDEX IF NOT EXISTS idx_quality_assessments_entity_id ON public.quality_assessments(entity_id);
CREATE INDEX IF NOT EXISTS idx_quality_assessments_relationship_id ON public.quality_assessments(relationship_id);
CREATE INDEX IF NOT EXISTS idx_quality_assessments_dimension ON public.quality_assessments(dimension);

-- Enhanced KG indexes
CREATE INDEX IF NOT EXISTS idx_kg_entities_is_active ON public.kg_entities(is_active);
CREATE INDEX IF NOT EXISTS idx_kg_entities_created_by ON public.kg_entities(created_by);
CREATE INDEX IF NOT EXISTS idx_kg_relationships_is_active ON public.kg_relationships(is_active);

-- =============================================
-- ENHANCED FUNCTIONS
-- =============================================

-- Function to get user permissions (enhanced)
CREATE OR REPLACE FUNCTION public.get_user_permissions(user_id UUID)
RETURNS TABLE(permission_name TEXT, resource_type TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT p.name, SPLIT_PART(p.name, ':', 1) as resource_type
    FROM public.user_roles ur
    JOIN public.role_permissions rp ON ur.role_id = rp.role_id
    JOIN public.permissions p ON rp.permission_id = p.id
    WHERE ur.user_id = get_user_permissions.user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user has role
CREATE OR REPLACE FUNCTION public.user_has_role(user_id UUID, role_name TEXT)
RETURNS BOOLEAN AS $$
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
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to log user activity
CREATE OR REPLACE FUNCTION public.log_user_activity(
    p_user_id UUID,
    p_action TEXT,
    p_resource_type TEXT DEFAULT NULL,
    p_resource_id UUID DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_details JSONB DEFAULT NULL
)
RETURNS UUID AS $$
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
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get pipeline step dependencies
CREATE OR REPLACE FUNCTION public.get_step_dependencies(step_id UUID)
RETURNS TABLE(dependency_step_id UUID, dependency_step_name TEXT) AS $$
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
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- ENHANCED RLS POLICIES
-- =============================================

-- API Keys policies
CREATE POLICY "Users can manage own API keys" ON public.api_keys
    FOR ALL USING (
        user_id = auth.uid() OR 
        public.check_user_permission(auth.uid(), 'user:management')
    );

-- Pipeline steps policies
CREATE POLICY "Users can view pipeline steps" ON public.pipeline_steps
    FOR SELECT USING (public.check_user_permission(auth.uid(), 'pipeline:read'));

CREATE POLICY "Users can manage pipeline steps" ON public.pipeline_steps
    FOR ALL USING (public.check_user_permission(auth.uid(), 'pipeline:write'));

-- Conflicts policies
CREATE POLICY "Experts can view conflicts" ON public.conflicts
    FOR SELECT USING (public.check_user_permission(auth.uid(), 'quality:expert'));

CREATE POLICY "Experts can manage conflicts" ON public.conflicts
    FOR ALL USING (public.check_user_permission(auth.uid(), 'quality:expert'));

-- Quality assessments policies
CREATE POLICY "Users can view quality assessments" ON public.quality_assessments
    FOR SELECT USING (public.check_user_permission(auth.uid(), 'quality:read'));

CREATE POLICY "Experts can manage quality assessments" ON public.quality_assessments
    FOR ALL USING (public.check_user_permission(auth.uid(), 'quality:expert'));

-- User activity log policies
CREATE POLICY "Admins can view all activity" ON public.user_activity_log
    FOR SELECT USING (public.check_user_permission(auth.uid(), 'system:monitoring'));

CREATE POLICY "Users can view own activity" ON public.user_activity_log
    FOR SELECT USING (user_id = auth.uid());

-- =============================================
-- UPDATE EXISTING POLICIES
-- =============================================

-- Update KG entities policies
DROP POLICY IF EXISTS "Knowledge editors can manage entities" ON public.kg_entities;
CREATE POLICY "Knowledge editors can manage entities" ON public.kg_entities
    FOR ALL USING (public.check_user_permission(auth.uid(), 'kg:edit'));

DROP POLICY IF EXISTS "Users can view knowledge graph entities" ON public.kg_entities;
CREATE POLICY "Users can view knowledge graph entities" ON public.kg_entities
    FOR SELECT USING (public.check_user_permission(auth.uid(), 'kg:read'));

-- Update KG relationships policies
DROP POLICY IF EXISTS "Knowledge editors can manage relationships" ON public.kg_relationships;
CREATE POLICY "Knowledge editors can manage relationships" ON public.kg_relationships
    FOR ALL USING (public.check_user_permission(auth.uid(), 'kg:edit'));

DROP POLICY IF EXISTS "Users can view knowledge graph relationships" ON public.kg_relationships;
CREATE POLICY "Users can view knowledge graph relationships" ON public.kg_relationships
    FOR SELECT USING (public.check_user_permission(auth.uid(), 'kg:read'));

-- =============================================
-- CLEANUP & MAINTENANCE
-- =============================================

-- Function to cleanup old logs
CREATE OR REPLACE FUNCTION public.cleanup_old_logs(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
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
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- SAMPLE DATA FOR TESTING
-- =============================================

-- Add sample admin user to admin role if not exists
DO $$
DECLARE
    admin_role_id INTEGER;
    sample_user_id UUID;
BEGIN
    -- Get admin role id
    SELECT id INTO admin_role_id FROM public.roles WHERE name = 'admin';
    
    -- Check if there are any admin users
    IF NOT EXISTS (
        SELECT 1 FROM public.user_roles ur 
        WHERE ur.role_id = admin_role_id
    ) THEN
        -- Create a sample admin user role assignment
        -- Note: You'll need to create the actual user through Supabase auth
        RAISE NOTICE 'No admin users found. Please create an admin user through the auth system and assign the admin role.';
    END IF;
END $$;
