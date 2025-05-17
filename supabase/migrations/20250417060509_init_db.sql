-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search similarity

-- =============================================
-- AUTHENTICATION & USER MANAGEMENT
-- =============================================

-- Extend the auth.users table with additional profile information
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  full_name TEXT,
  avatar_url TEXT,
  department TEXT,
  position TEXT,
  bio TEXT,
  last_sign_in_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Roles table for RBAC
CREATE TABLE IF NOT EXISTS public.roles (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- User-roles relationship
CREATE TABLE IF NOT EXISTS public.user_roles (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  role_id INTEGER REFERENCES public.roles(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  UNIQUE(user_id, role_id)
);

-- Permissions
CREATE TABLE IF NOT EXISTS public.permissions (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Role-permissions relationship
CREATE TABLE IF NOT EXISTS public.role_permissions (
  id SERIAL PRIMARY KEY,
  role_id INTEGER REFERENCES public.roles(id) ON DELETE CASCADE,
  permission_id INTEGER REFERENCES public.permissions(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  UNIQUE(role_id, permission_id)
);

-- Notifications
CREATE TABLE IF NOT EXISTS public.notifications (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  icon TEXT,
  link TEXT,
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- =============================================
-- DATA SOURCES & PIPELINES
-- =============================================

-- Data sources
CREATE TABLE IF NOT EXISTS public.data_sources (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  source_type TEXT NOT NULL CHECK (source_type IN ('file', 'api', 'database', 'url')),
  connection_details JSONB NOT NULL,
  credentials JSONB,
  is_active BOOLEAN DEFAULT TRUE,
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- File data sources
CREATE TABLE IF NOT EXISTS public.file_uploads (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  data_source_id UUID REFERENCES public.data_sources(id) ON DELETE CASCADE,
  file_name TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  storage_path TEXT NOT NULL,
  upload_status TEXT DEFAULT 'pending' CHECK (upload_status IN ('pending', 'processing', 'completed', 'failed')),
  processed BOOLEAN DEFAULT FALSE,
  metadata JSONB,
  uploaded_by UUID REFERENCES auth.users(id),
  uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Pipeline configurations
CREATE TABLE IF NOT EXISTS public.pipelines (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  pipeline_type TEXT NOT NULL CHECK (pipeline_type IN ('extraction', 'transformation', 'loading', 'complete')),
  steps JSONB NOT NULL,
  schedule TEXT, -- CRON expression
  is_active BOOLEAN DEFAULT TRUE,
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Pipeline executions
CREATE TABLE IF NOT EXISTS public.pipeline_runs (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  pipeline_id UUID REFERENCES public.pipelines(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
  start_time TIMESTAMP WITH TIME ZONE NOT NULL,
  end_time TIMESTAMP WITH TIME ZONE,
  duration INTEGER, -- in seconds
  triggered_by UUID REFERENCES auth.users(id),
  log TEXT,
  error_message TEXT,
  stats JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Extraction results
CREATE TABLE IF NOT EXISTS public.extraction_results (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  pipeline_run_id UUID REFERENCES public.pipeline_runs(id) ON DELETE CASCADE,
  source_id UUID REFERENCES public.file_uploads(id),
  entity_count INTEGER DEFAULT 0,
  relationship_count INTEGER DEFAULT 0,
  processed_text_length INTEGER,
  extracted_entities JSONB,
  extracted_relationships JSONB,
  status TEXT NOT NULL CHECK (status IN ('pending', 'completed', 'failed', 'partially_completed')),
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- =============================================
-- FIBO ONTOLOGY & KNOWLEDGE GRAPH
-- =============================================

-- FIBO Ontology classes
CREATE TABLE IF NOT EXISTS public.fibo_classes (
  id SERIAL PRIMARY KEY,
  uri TEXT UNIQUE NOT NULL,
  label TEXT,
  description TEXT,
  parent_class_id INTEGER REFERENCES public.fibo_classes(id),
  properties JSONB,
  domain TEXT,
  is_custom BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Create GIN index for text search
CREATE INDEX fibo_classes_label_idx ON public.fibo_classes USING GIN (label gin_trgm_ops);
CREATE INDEX fibo_classes_uri_idx ON public.fibo_classes USING GIN (uri gin_trgm_ops);

-- FIBO Ontology properties
CREATE TABLE IF NOT EXISTS public.fibo_properties (
  id SERIAL PRIMARY KEY,
  uri TEXT UNIQUE NOT NULL,
  label TEXT,
  description TEXT,
  domain_class_id INTEGER REFERENCES public.fibo_classes(id),
  range_class_id INTEGER REFERENCES public.fibo_classes(id),
  property_type TEXT CHECK (property_type IN ('object', 'datatype')),
  is_custom BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Create GIN index for text search
CREATE INDEX fibo_properties_label_idx ON public.fibo_properties USING GIN (label gin_trgm_ops);
CREATE INDEX fibo_properties_uri_idx ON public.fibo_properties USING GIN (uri gin_trgm_ops);

-- Entity mappings cache
CREATE TABLE IF NOT EXISTS public.entity_mappings (
  id SERIAL PRIMARY KEY,
  entity_type TEXT NOT NULL,
  fibo_class_id INTEGER REFERENCES public.fibo_classes(id),
  confidence FLOAT,
  created_by UUID REFERENCES auth.users(id),
  is_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  UNIQUE(entity_type)
);

-- Relationship mappings cache
CREATE TABLE IF NOT EXISTS public.relationship_mappings (
  id SERIAL PRIMARY KEY,
  relationship_type TEXT NOT NULL,
  fibo_property_id INTEGER REFERENCES public.fibo_properties(id),
  confidence FLOAT,
  created_by UUID REFERENCES auth.users(id),
  is_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  UNIQUE(relationship_type)
);

-- Knowledge Graph entities
CREATE TABLE IF NOT EXISTS public.kg_entities (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  neo4j_id TEXT,
  entity_text TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  source_document_id UUID REFERENCES public.file_uploads(id),
  fibo_class_id INTEGER REFERENCES public.fibo_classes(id),
  properties JSONB,
  confidence FLOAT,
  is_verified BOOLEAN DEFAULT FALSE,
  verification_notes TEXT,
  verified_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Create text search index
CREATE INDEX kg_entities_text_idx ON public.kg_entities USING GIN (entity_text gin_trgm_ops);
CREATE INDEX kg_entities_type_idx ON public.kg_entities(entity_type);

-- Knowledge Graph relationships
CREATE TABLE IF NOT EXISTS public.kg_relationships (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  neo4j_id TEXT,
  source_entity_id UUID REFERENCES public.kg_entities(id) ON DELETE CASCADE,
  target_entity_id UUID REFERENCES public.kg_entities(id) ON DELETE CASCADE,
  relationship_type TEXT NOT NULL,
  source_document_id UUID REFERENCES public.file_uploads(id),
  fibo_property_id INTEGER REFERENCES public.fibo_properties(id),
  properties JSONB,
  confidence FLOAT,
  is_verified BOOLEAN DEFAULT FALSE,
  verification_notes TEXT,
  verified_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Create index for relationship lookups
CREATE INDEX kg_relationships_type_idx ON public.kg_relationships(relationship_type);
CREATE INDEX kg_relationships_source_idx ON public.kg_relationships(source_entity_id);
CREATE INDEX kg_relationships_target_idx ON public.kg_relationships(target_entity_id);

-- Entity conflicts that need manual resolution
CREATE TABLE IF NOT EXISTS public.entity_conflicts (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  entity_id_1 UUID REFERENCES public.kg_entities(id) ON DELETE CASCADE,
  entity_id_2 UUID REFERENCES public.kg_entities(id) ON DELETE CASCADE,
  similarity_score FLOAT,
  conflict_type TEXT CHECK (conflict_type IN ('possible_duplicate', 'inconsistent_attributes', 'conflicting_relations')),
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'resolved', 'ignored')),
  resolution_notes TEXT,
  resolved_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- =============================================
-- QUERY & VISUALIZATION
-- =============================================

-- Saved queries
CREATE TABLE IF NOT EXISTS public.saved_queries (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  query_type TEXT CHECK (query_type IN ('cypher', 'sparql', 'natural_language')),
  query_text TEXT NOT NULL,
  parameters JSONB,
  is_public BOOLEAN DEFAULT FALSE,
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Query execution history
CREATE TABLE IF NOT EXISTS public.query_history (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  query_id UUID REFERENCES public.saved_queries(id),
  query_text TEXT NOT NULL,
  parameters JSONB,
  execution_time INTEGER, -- in milliseconds
  result_count INTEGER,
  status TEXT CHECK (status IN ('completed', 'failed', 'timeout')),
  error_message TEXT,
  executed_by UUID REFERENCES auth.users(id),
  executed_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Custom visualizations
CREATE TABLE IF NOT EXISTS public.visualizations (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  query_id UUID REFERENCES public.saved_queries(id),
  visualization_type TEXT NOT NULL CHECK (visualization_type IN ('graph', 'tree', 'table', 'chart')),
  config JSONB NOT NULL,
  is_public BOOLEAN DEFAULT FALSE,
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- =============================================
-- TRIGGERS & FUNCTIONS
-- =============================================

-- Trigger to create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name)
  VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Function to check if a user has a permission
CREATE OR REPLACE FUNCTION public.check_user_permission(user_id UUID, permission_name TEXT)
RETURNS BOOLEAN AS $$
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
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update timestamp fields
CREATE OR REPLACE FUNCTION public.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables with that column
DO $$
DECLARE
  t text;
BEGIN
  FOR t IN
    SELECT table_name FROM information_schema.columns 
    WHERE column_name = 'updated_at' 
    AND table_schema = 'public'
  LOOP
    EXECUTE format('
      CREATE TRIGGER update_timestamp
      BEFORE UPDATE ON public.%I
      FOR EACH ROW EXECUTE PROCEDURE public.update_timestamp();
    ', t);
  END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- ROW LEVEL SECURITY POLICIES
-- =============================================

-- Enable RLS on all tables
DO $$
DECLARE
  t text;
BEGIN
  FOR t IN
    SELECT tablename FROM pg_tables WHERE schemaname = 'public'
  LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', t);
  END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Profiles policies
CREATE POLICY "Users can view their own profile" 
  ON public.profiles FOR SELECT 
  USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" 
  ON public.profiles FOR UPDATE 
  USING (auth.uid() = id);

-- Admin policies for user management
CREATE POLICY "Admins can view all profiles" 
  ON public.profiles FOR SELECT 
  USING (public.check_user_permission(auth.uid(), 'user:read'));

CREATE POLICY "Admins can manage roles" 
  ON public.roles FOR ALL 
  USING (public.check_user_permission(auth.uid(), 'user:write'));

CREATE POLICY "Admins can manage permissions" 
  ON public.permissions FOR ALL 
  USING (public.check_user_permission(auth.uid(), 'user:write'));

-- Notifications policies
CREATE POLICY "Users can view their own notifications" 
  ON public.notifications FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own notifications" 
  ON public.notifications FOR UPDATE 
  USING (auth.uid() = user_id);

-- Data sources policies
CREATE POLICY "Admins can manage data sources" 
  ON public.data_sources FOR ALL 
  USING (public.check_user_permission(auth.uid(), 'datasource:write'));

CREATE POLICY "Users can view data sources" 
  ON public.data_sources FOR SELECT 
  USING (public.check_user_permission(auth.uid(), 'datasource:read'));

-- File uploads policies
CREATE POLICY "Users can upload files" 
  ON public.file_uploads FOR INSERT 
  WITH CHECK (public.check_user_permission(auth.uid(), 'datasource:write'));

CREATE POLICY "Users can view uploads" 
  ON public.file_uploads FOR SELECT 
  USING (public.check_user_permission(auth.uid(), 'datasource:read'));

-- Pipeline policies
CREATE POLICY "Admins can manage pipelines" 
  ON public.pipelines FOR ALL 
  USING (public.check_user_permission(auth.uid(), 'pipeline:write'));

CREATE POLICY "Users can view pipelines" 
  ON public.pipelines FOR SELECT 
  USING (public.check_user_permission(auth.uid(), 'pipeline:read'));

-- Knowledge graph policies
CREATE POLICY "Users can view knowledge graph entities" 
  ON public.kg_entities FOR SELECT 
  USING (public.check_user_permission(auth.uid(), 'knowledge:read'));

CREATE POLICY "Knowledge editors can manage entities" 
  ON public.kg_entities FOR ALL 
  USING (public.check_user_permission(auth.uid(), 'knowledge:write'));

CREATE POLICY "Users can view knowledge graph relationships" 
  ON public.kg_relationships FOR SELECT 
  USING (public.check_user_permission(auth.uid(), 'knowledge:read'));

CREATE POLICY "Knowledge editors can manage relationships" 
  ON public.kg_relationships FOR ALL 
  USING (public.check_user_permission(auth.uid(), 'knowledge:write'));

-- Query policies
CREATE POLICY "Users can execute queries" 
  ON public.query_history FOR INSERT 
  WITH CHECK (public.check_user_permission(auth.uid(), 'knowledge:read'));

CREATE POLICY "Users can save queries" 
  ON public.saved_queries FOR INSERT 
  WITH CHECK (public.check_user_permission(auth.uid(), 'knowledge:read'));

CREATE POLICY "Users can view their own queries" 
  ON public.saved_queries FOR SELECT 
  USING (auth.uid() = created_by OR is_public);

CREATE POLICY "Users can update their own queries" 
  ON public.saved_queries FOR UPDATE 
  USING (auth.uid() = created_by);

-- =============================================
-- INITIAL DATA
-- =============================================

-- Insert default roles
INSERT INTO public.roles (name, description) VALUES 
  ('admin', 'Administrator with full access'),
  ('editor', 'Can edit knowledge graph data'),
  ('viewer', 'Read-only access to the system');

-- Insert default permissions
INSERT INTO public.permissions (name, description) VALUES 
  ('user:read', 'View user information'),
  ('user:write', 'Create and update users'),
  ('knowledge:read', 'View knowledge graph'),
  ('knowledge:write', 'Edit knowledge graph'),
  ('pipeline:read', 'View data pipelines'),
  ('pipeline:write', 'Configure and run pipelines'),
  ('datasource:read', 'View data sources'),
  ('datasource:write', 'Configure data sources');

-- Assign permissions to roles
INSERT INTO public.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM public.roles r, public.permissions p WHERE r.name = 'admin';

INSERT INTO public.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM public.roles r, public.permissions p 
WHERE r.name = 'editor' AND p.name IN ('knowledge:read', 'knowledge:write', 'datasource:read', 'pipeline:read');

INSERT INTO public.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM public.roles r, public.permissions p 
WHERE r.name = 'viewer' AND p.name IN ('knowledge:read', 'datasource:read', 'pipeline:read');
