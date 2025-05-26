-- =============================================
-- DOMAIN TYPES MIGRATION
-- Add entity types and relationship types tables
-- Update mapping tables to reference type tables
-- =============================================

-- Drop existing constraints and indexes that will be modified
DROP INDEX IF EXISTS kg_entities_type_idx;
DROP INDEX IF EXISTS kg_relationships_type_idx;

-- =============================================
-- DOMAIN CONFIGURATION TABLE
-- =============================================

-- Domain configuration for managing different business domains
CREATE TABLE IF NOT EXISTS public.domains (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  description TEXT,
  color TEXT DEFAULT '#6366F1',
  icon TEXT,
  ontology_namespace TEXT, -- Base namespace for this domain's ontology
  is_active BOOLEAN DEFAULT TRUE,
  config JSONB, -- Domain-specific configuration
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- =============================================
-- DOMAIN TYPE TABLES
-- =============================================

-- Entity types table (domain-agnostic)
CREATE TABLE IF NOT EXISTS public.entity_types (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  description TEXT,
  color TEXT DEFAULT '#3B82F6', -- UI color for visualization
  icon TEXT, -- Icon identifier for UI
  extraction_pattern TEXT, -- Regex or pattern for AI extraction
  validation_rules JSONB, -- Rules for validating extracted entities
  examples JSONB, -- Example entities of this type
  is_active BOOLEAN DEFAULT TRUE,
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Relationship types table (domain-agnostic)
CREATE TABLE IF NOT EXISTS public.relationship_types (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  description TEXT,
  source_entity_types INTEGER[], -- Array of allowed source entity type IDs
  target_entity_types INTEGER[], -- Array of allowed target entity type IDs
  is_bidirectional BOOLEAN DEFAULT FALSE,
  color TEXT DEFAULT '#10B981', -- UI color for visualization
  extraction_pattern TEXT, -- Pattern for AI extraction
  validation_rules JSONB, -- Rules for validating extracted relationships
  examples JSONB, -- Example relationships of this type
  is_active BOOLEAN DEFAULT TRUE,
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- Many-to-many: Entity types can belong to multiple domains
CREATE TABLE IF NOT EXISTS public.entity_type_domains (
  id SERIAL PRIMARY KEY,
  entity_type_id INTEGER REFERENCES public.entity_types(id) ON DELETE CASCADE,
  domain_id INTEGER REFERENCES public.domains(id) ON DELETE CASCADE,
  is_primary BOOLEAN DEFAULT FALSE, -- Mark primary domain for this type
  domain_specific_config JSONB, -- Domain-specific configuration for this type
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  UNIQUE(entity_type_id, domain_id)
);

-- Many-to-many: Relationship types can belong to multiple domains  
CREATE TABLE IF NOT EXISTS public.relationship_type_domains (
  id SERIAL PRIMARY KEY,
  relationship_type_id INTEGER REFERENCES public.relationship_types(id) ON DELETE CASCADE,
  domain_id INTEGER REFERENCES public.domains(id) ON DELETE CASCADE,
  is_primary BOOLEAN DEFAULT FALSE, -- Mark primary domain for this type
  domain_specific_config JSONB, -- Domain-specific configuration for this type
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  UNIQUE(relationship_type_id, domain_id)
);

-- Create indexes for performance
CREATE INDEX entity_types_name_idx ON public.entity_types(name);
CREATE INDEX entity_types_active_idx ON public.entity_types(is_active);

CREATE INDEX relationship_types_name_idx ON public.relationship_types(name);  
CREATE INDEX relationship_types_active_idx ON public.relationship_types(is_active);

-- Indexes for junction tables
CREATE INDEX entity_type_domains_entity_idx ON public.entity_type_domains(entity_type_id);
CREATE INDEX entity_type_domains_domain_idx ON public.entity_type_domains(domain_id);
CREATE INDEX entity_type_domains_primary_idx ON public.entity_type_domains(is_primary);

CREATE INDEX relationship_type_domains_relationship_idx ON public.relationship_type_domains(relationship_type_id);
CREATE INDEX relationship_type_domains_domain_idx ON public.relationship_type_domains(domain_id);  
CREATE INDEX relationship_type_domains_primary_idx ON public.relationship_type_domains(is_primary);

-- =============================================
-- UPDATE EXISTING MAPPING TABLES
-- =============================================

-- Add new columns to entity_mappings (keeping old column for migration)
ALTER TABLE public.entity_mappings 
ADD COLUMN IF NOT EXISTS entity_type_id INTEGER REFERENCES public.entity_types(id),
ADD COLUMN IF NOT EXISTS mapping_status TEXT DEFAULT 'pending' CHECK (mapping_status IN ('pending', 'mapped', 'rejected', 'needs_review')),
ADD COLUMN IF NOT EXISTS mapping_notes TEXT,
ADD COLUMN IF NOT EXISTS auto_mapped BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS reviewed_by UUID REFERENCES auth.users(id),
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE;

-- Add new columns to relationship_mappings (keeping old column for migration)
ALTER TABLE public.relationship_mappings
ADD COLUMN IF NOT EXISTS relationship_type_id INTEGER REFERENCES public.relationship_types(id),
ADD COLUMN IF NOT EXISTS mapping_status TEXT DEFAULT 'pending' CHECK (mapping_status IN ('pending', 'mapped', 'rejected', 'needs_review')),
ADD COLUMN IF NOT EXISTS mapping_notes TEXT,
ADD COLUMN IF NOT EXISTS auto_mapped BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS reviewed_by UUID REFERENCES auth.users(id),
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE;

-- Update unique constraints
ALTER TABLE public.entity_mappings DROP CONSTRAINT IF EXISTS entity_mappings_entity_type_key;
ALTER TABLE public.relationship_mappings DROP CONSTRAINT IF EXISTS relationship_mappings_relationship_type_key;

-- =============================================
-- UPDATE KNOWLEDGE GRAPH TABLES  
-- =============================================

-- Add entity_type_id to kg_entities (keeping entity_type for backward compatibility)
ALTER TABLE public.kg_entities
ADD COLUMN IF NOT EXISTS entity_type_id INTEGER REFERENCES public.entity_types(id),
ADD COLUMN IF NOT EXISTS extraction_confidence FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS validation_status TEXT DEFAULT 'pending' CHECK (validation_status IN ('pending', 'valid', 'invalid', 'needs_review')),
ADD COLUMN IF NOT EXISTS validation_errors JSONB;

-- Add relationship_type_id to kg_relationships (keeping relationship_type for backward compatibility)
ALTER TABLE public.kg_relationships  
ADD COLUMN IF NOT EXISTS relationship_type_id INTEGER REFERENCES public.relationship_types(id),
ADD COLUMN IF NOT EXISTS extraction_confidence FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS validation_status TEXT DEFAULT 'pending' CHECK (validation_status IN ('pending', 'valid', 'invalid', 'needs_review')),
ADD COLUMN IF NOT EXISTS validation_errors JSONB;

-- Create new indexes
CREATE INDEX kg_entities_type_id_idx ON public.kg_entities(entity_type_id);
CREATE INDEX kg_entities_validation_status_idx ON public.kg_entities(validation_status);

CREATE INDEX kg_relationships_type_id_idx ON public.kg_relationships(relationship_type_id);
CREATE INDEX kg_relationships_validation_status_idx ON public.kg_relationships(validation_status);


-- =============================================
-- EXTRACTION TEMPLATES
-- =============================================

-- Templates for AI extraction configuration
CREATE TABLE IF NOT EXISTS public.extraction_templates (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  domain TEXT NOT NULL,
  entity_types INTEGER[], -- Array of entity type IDs to extract
  relationship_types INTEGER[], -- Array of relationship type IDs to extract
  prompt_template TEXT NOT NULL, -- AI prompt template
  extraction_config JSONB, -- Configuration for extraction process
  is_active BOOLEAN DEFAULT TRUE,
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- =============================================
-- HELPER FUNCTIONS
-- =============================================

-- Function to get entity type by name (optionally filtered by domain)
CREATE OR REPLACE FUNCTION public.get_entity_type_id(type_name TEXT, domain_name TEXT DEFAULT NULL)
RETURNS INTEGER AS $func$
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
$func$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get relationship type by name (optionally filtered by domain)
CREATE OR REPLACE FUNCTION public.get_relationship_type_id(type_name TEXT, domain_name TEXT DEFAULT NULL)
RETURNS INTEGER AS $func$
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
$func$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get entity types for a domain
CREATE OR REPLACE FUNCTION public.get_domain_entity_types(domain_name TEXT)
RETURNS TABLE(id INTEGER, name TEXT, display_name TEXT, description TEXT, color TEXT, icon TEXT, extraction_pattern TEXT, validation_rules JSONB, is_active BOOL, created_by UUID, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ, is_primary BOOLEAN) AS $func$
BEGIN
  RETURN QUERY
  SELECT *, etd.is_primary
  FROM public.entity_types et
  JOIN public.entity_type_domains etd ON et.id = etd.entity_type_id
  JOIN public.domains d ON etd.domain_id = d.id
  WHERE d.name = domain_name AND et.is_active = TRUE;
END;
$func$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get relationship types for a domain
CREATE OR REPLACE FUNCTION public.get_domain_relationship_types(domain_name TEXT)
RETURNS TABLE(id INTEGER, name TEXT, display_name TEXT, is_primary BOOLEAN) AS $func$
BEGIN
  RETURN QUERY
  SELECT rt.id, rt.name, rt.display_name, rtd.is_primary
  FROM public.relationship_types rt
  JOIN public.relationship_type_domains rtd ON rt.id = rtd.relationship_type_id  
  JOIN public.domains d ON rtd.domain_id = d.id
  WHERE d.name = domain_name AND rt.is_active = TRUE;
END;
$func$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to validate relationship type constraints
CREATE OR REPLACE FUNCTION public.validate_relationship_types()
RETURNS TRIGGER AS $function$
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
$function$ LANGUAGE plpgsql;

-- Add trigger for relationship validation
CREATE TRIGGER validate_kg_relationships
  BEFORE INSERT OR UPDATE ON public.kg_relationships
  FOR EACH ROW
  WHEN (NEW.relationship_type_id IS NOT NULL)
  EXECUTE FUNCTION public.validate_relationship_types();

-- =============================================
-- MIGRATION DATA FUNCTIONS
-- =============================================

-- Function to migrate existing entity types to new table
CREATE OR REPLACE FUNCTION public.migrate_entity_types()
RETURNS VOID AS $func$
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
$func$ LANGUAGE plpgsql;

-- Function to migrate existing relationship types to new table
CREATE OR REPLACE FUNCTION public.migrate_relationship_types()
RETURNS VOID AS $func$
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
$func$ LANGUAGE plpgsql;

-- =============================================
-- ROW LEVEL SECURITY POLICIES
-- =============================================

-- Entity types policies
CREATE POLICY "Users can view entity types" 
  ON public.entity_types FOR SELECT 
  USING (public.check_user_permission(auth.uid(), 'knowledge:read'));

CREATE POLICY "Knowledge editors can manage entity types" 
  ON public.entity_types FOR ALL 
  USING (public.check_user_permission(auth.uid(), 'knowledge:write'));

-- Relationship types policies  
CREATE POLICY "Users can view relationship types"
  ON public.relationship_types FOR SELECT
  USING (public.check_user_permission(auth.uid(), 'knowledge:read'));

CREATE POLICY "Knowledge editors can manage relationship types"
  ON public.relationship_types FOR ALL
  USING (public.check_user_permission(auth.uid(), 'knowledge:write'));

-- Entity type domains policies
CREATE POLICY "Users can view entity type domains"
  ON public.entity_type_domains FOR SELECT
  USING (public.check_user_permission(auth.uid(), 'knowledge:read'));

CREATE POLICY "Knowledge editors can manage entity type domains"
  ON public.entity_type_domains FOR ALL
  USING (public.check_user_permission(auth.uid(), 'knowledge:write'));

-- Relationship type domains policies
CREATE POLICY "Users can view relationship type domains"
  ON public.relationship_type_domains FOR SELECT
  USING (public.check_user_permission(auth.uid(), 'knowledge:read'));

CREATE POLICY "Knowledge editors can manage relationship type domains"
  ON public.relationship_type_domains FOR ALL
  USING (public.check_user_permission(auth.uid(), 'knowledge:write'));

-- Domains policies
CREATE POLICY "Users can view domains"
  ON public.domains FOR SELECT  
  USING (public.check_user_permission(auth.uid(), 'knowledge:read'));

CREATE POLICY "Admins can manage domains"
  ON public.domains FOR ALL
  USING (public.check_user_permission(auth.uid(), 'user:write'));

-- Extraction templates policies
CREATE POLICY "Users can view extraction templates"
  ON public.extraction_templates FOR SELECT
  USING (public.check_user_permission(auth.uid(), 'pipeline:read'));

CREATE POLICY "Pipeline editors can manage extraction templates"  
  ON public.extraction_templates FOR ALL
  USING (public.check_user_permission(auth.uid(), 'pipeline:write'));

-- =============================================
-- INITIAL SAMPLE DATA
-- =============================================

-- Insert sample domains
INSERT INTO public.domains (name, display_name, description, ontology_namespace) VALUES 
  ('financial', 'Financial Services', 'Financial instruments, institutions, and relationships', 'https://spec.edmcouncil.org/fibo/ontology/'),
  ('legal', 'Legal & Compliance', 'Legal entities, contracts, and regulatory relationships', 'https://example.org/legal/'),
  ('business', 'Business Operations', 'General business entities and operational relationships', 'https://example.org/business/'),
  ('general', 'General Domain', 'Generic entities and relationships', 'https://example.org/general/');

-- Insert sample entity types (domain-agnostic)
INSERT INTO public.entity_types (name, display_name, description, color, examples) VALUES 
  ('organization', 'Organization', 'Companies, institutions, and other organizational entities', '#3B82F6', '["Apple Inc.", "Goldman Sachs", "Federal Reserve"]'),
  ('person', 'Person', 'Individual persons including executives, customers, etc.', '#10B981', '["John Smith", "CEO", "Board Member"]'),
  ('financial_instrument', 'Financial Instrument', 'Stocks, bonds, derivatives, and other financial products', '#F59E0B', '["AAPL Stock", "US Treasury Bond", "Credit Default Swap"]'),
  ('currency', 'Currency', 'Monetary units and currency types', '#EF4444', '["USD", "EUR", "Bitcoin"]'),
  ('location', 'Location', 'Geographic entities including countries, cities, addresses', '#8B5CF6', '["New York", "United States", "Wall Street"]'),
  ('date', 'Date', 'Temporal entities including dates, periods, events', '#06B6D4', '["2024-01-01", "Q1 2024", "Fiscal Year 2024"]'),
  ('contract', 'Contract', 'Legal agreements and contracts', '#F97316', '["Loan Agreement", "Employment Contract", "NDA"]'),
  ('regulation', 'Regulation', 'Laws, regulations, and compliance requirements', '#84CC16', '["Basel III", "GDPR", "SOX"]');

-- Insert sample relationship types (domain-agnostic)
INSERT INTO public.relationship_types (name, display_name, description, source_entity_types, target_entity_types, examples) VALUES
  ('owns', 'Owns', 'Ownership relationship between entities', ARRAY[1,2], ARRAY[1,3], '["Company owns subsidiary", "Person owns shares"]'),
  ('works_for', 'Works For', 'Employment relationship', ARRAY[2], ARRAY[1], '["John works for Apple Inc."]'),
  ('located_in', 'Located In', 'Geographic location relationship', ARRAY[1,2], ARRAY[5], '["Company located in New York"]'),
  ('issued_by', 'Issued By', 'Financial instrument issuance relationship', ARRAY[3], ARRAY[1], '["Bond issued by Government"]'),
  ('trades_in', 'Trades In', 'Currency trading relationship', ARRAY[1], ARRAY[4], '["Bank trades in USD"]'),
  ('occurred_on', 'Occurred On', 'Temporal relationship for events', NULL, ARRAY[6], '["Event occurred on 2024-01-01"]'),
  ('governed_by', 'Governed By', 'Regulatory relationship', ARRAY[1,3,7], ARRAY[8], '["Bank governed by Basel III"]'),
  ('party_to', 'Party To', 'Contract participation relationship', ARRAY[1,2], ARRAY[7], '["Company party to contract"]');

-- Link entity types to appropriate domains
DO $func$
DECLARE
  financial_domain_id INTEGER;
  legal_domain_id INTEGER;
  business_domain_id INTEGER;
  general_domain_id INTEGER;
BEGIN
  -- Get domain IDs
  SELECT id INTO financial_domain_id FROM public.domains WHERE name = 'financial';
  SELECT id INTO legal_domain_id FROM public.domains WHERE name = 'legal';
  SELECT id INTO business_domain_id FROM public.domains WHERE name = 'business';
  SELECT id INTO general_domain_id FROM public.domains WHERE name = 'general';
  
  -- Entity type - domain mappings
  INSERT INTO public.entity_type_domains (entity_type_id, domain_id, is_primary) VALUES
    -- Organization: all domains (primary = business)
    ((SELECT id FROM public.entity_types WHERE name = 'organization'), financial_domain_id, FALSE),
    ((SELECT id FROM public.entity_types WHERE name = 'organization'), legal_domain_id, FALSE),
    ((SELECT id FROM public.entity_types WHERE name = 'organization'), business_domain_id, TRUE),
    ((SELECT id FROM public.entity_types WHERE name = 'organization'), general_domain_id, FALSE),
    
    -- Person: all domains (primary = general)
    ((SELECT id FROM public.entity_types WHERE name = 'person'), financial_domain_id, FALSE),
    ((SELECT id FROM public.entity_types WHERE name = 'person'), legal_domain_id, FALSE),
    ((SELECT id FROM public.entity_types WHERE name = 'person'), business_domain_id, FALSE),
    ((SELECT id FROM public.entity_types WHERE name = 'person'), general_domain_id, TRUE),
    
    -- Financial instrument: primarily financial
    ((SELECT id FROM public.entity_types WHERE name = 'financial_instrument'), financial_domain_id, TRUE),
    ((SELECT id FROM public.entity_types WHERE name = 'financial_instrument'), legal_domain_id, FALSE),
    
    -- Currency: primarily financial
    ((SELECT id FROM public.entity_types WHERE name = 'currency'), financial_domain_id, TRUE),
    ((SELECT id FROM public.entity_types WHERE name = 'currency'), business_domain_id, FALSE),
    
    -- Location: all domains (primary = general)
    ((SELECT id FROM public.entity_types WHERE name = 'location'), financial_domain_id, FALSE),
    ((SELECT id FROM public.entity_types WHERE name = 'location'), legal_domain_id, FALSE),
    ((SELECT id FROM public.entity_types WHERE name = 'location'), business_domain_id, FALSE),
    ((SELECT id FROM public.entity_types WHERE name = 'location'), general_domain_id, TRUE),
    
    -- Date: all domains (primary = general)
    ((SELECT id FROM public.entity_types WHERE name = 'date'), financial_domain_id, FALSE),
    ((SELECT id FROM public.entity_types WHERE name = 'date'), legal_domain_id, FALSE),
    ((SELECT id FROM public.entity_types WHERE name = 'date'), business_domain_id, FALSE),
    ((SELECT id FROM public.entity_types WHERE name = 'date'), general_domain_id, TRUE),
    
    -- Contract: primarily legal
    ((SELECT id FROM public.entity_types WHERE name = 'contract'), legal_domain_id, TRUE),
    ((SELECT id FROM public.entity_types WHERE name = 'contract'), financial_domain_id, FALSE),
    ((SELECT id FROM public.entity_types WHERE name = 'contract'), business_domain_id, FALSE),
    
    -- Regulation: primarily legal
    ((SELECT id FROM public.entity_types WHERE name = 'regulation'), legal_domain_id, TRUE),
    ((SELECT id FROM public.entity_types WHERE name = 'regulation'), financial_domain_id, FALSE);
    
  -- Relationship type - domain mappings
  INSERT INTO public.relationship_type_domains (relationship_type_id, domain_id, is_primary) VALUES
    -- Owns: all domains (primary = financial)
    ((SELECT id FROM public.relationship_types WHERE name = 'owns'), financial_domain_id, TRUE),
    ((SELECT id FROM public.relationship_types WHERE name = 'owns'), legal_domain_id, FALSE),
    ((SELECT id FROM public.relationship_types WHERE name = 'owns'), business_domain_id, FALSE),
    
    -- Works for: primarily business
    ((SELECT id FROM public.relationship_types WHERE name = 'works_for'), business_domain_id, TRUE),
    ((SELECT id FROM public.relationship_types WHERE name = 'works_for'), legal_domain_id, FALSE),
    
    -- Located in: all domains (primary = general)
    ((SELECT id FROM public.relationship_types WHERE name = 'located_in'), financial_domain_id, FALSE),
    ((SELECT id FROM public.relationship_types WHERE name = 'located_in'), legal_domain_id, FALSE),
    ((SELECT id FROM public.relationship_types WHERE name = 'located_in'), business_domain_id, FALSE),
    ((SELECT id FROM public.relationship_types WHERE name = 'located_in'), general_domain_id, TRUE),
    
    -- Issued by: primarily financial
    ((SELECT id FROM public.relationship_types WHERE name = 'issued_by'), financial_domain_id, TRUE),
    
    -- Trades in: primarily financial
    ((SELECT id FROM public.relationship_types WHERE name = 'trades_in'), financial_domain_id, TRUE),
    
    -- Occurred on: all domains (primary = general)
    ((SELECT id FROM public.relationship_types WHERE name = 'occurred_on'), financial_domain_id, FALSE),
    ((SELECT id FROM public.relationship_types WHERE name = 'occurred_on'), legal_domain_id, FALSE),
    ((SELECT id FROM public.relationship_types WHERE name = 'occurred_on'), business_domain_id, FALSE),
    ((SELECT id FROM public.relationship_types WHERE name = 'occurred_on'), general_domain_id, TRUE),
    
    -- Governed by: primarily legal
    ((SELECT id FROM public.relationship_types WHERE name = 'governed_by'), legal_domain_id, TRUE),
    ((SELECT id FROM public.relationship_types WHERE name = 'governed_by'), financial_domain_id, FALSE),
    
    -- Party to: primarily legal
    ((SELECT id FROM public.relationship_types WHERE name = 'party_to'), legal_domain_id, TRUE),
    ((SELECT id FROM public.relationship_types WHERE name = 'party_to'), business_domain_id, FALSE);
END $func$;

-- Update extraction template to use entity/relationship type IDs
UPDATE public.extraction_templates 
SET entity_types = ARRAY[
  (SELECT id FROM public.entity_types WHERE name = 'organization'),
  (SELECT id FROM public.entity_types WHERE name = 'person'),
  (SELECT id FROM public.entity_types WHERE name = 'financial_instrument'),
  (SELECT id FROM public.entity_types WHERE name = 'currency'),
  (SELECT id FROM public.entity_types WHERE name = 'location'),
  (SELECT id FROM public.entity_types WHERE name = 'date')
],
relationship_types = ARRAY[
  (SELECT id FROM public.relationship_types WHERE name = 'owns'),
  (SELECT id FROM public.relationship_types WHERE name = 'works_for'),
  (SELECT id FROM public.relationship_types WHERE name = 'located_in'),
  (SELECT id FROM public.relationship_types WHERE name = 'issued_by'),
  (SELECT id FROM public.relationship_types WHERE name = 'trades_in'),
  (SELECT id FROM public.relationship_types WHERE name = 'occurred_on')
]
WHERE name = 'Financial Document Extraction';

-- Insert sample extraction template
INSERT INTO public.extraction_templates (name, description, domain, entity_types, relationship_types, prompt_template, extraction_config) VALUES
  ('Financial Document Extraction', 'Extract financial entities and relationships from documents', 'financial', 
   ARRAY[1,2,3,4,5,6], ARRAY[1,2,3,4,5,6],
   'Extract the following types of entities and relationships from this financial document: Organizations, Persons, Financial Instruments, Currencies, Locations, and Dates. Identify relationships such as ownership, employment, location, issuance, trading, and temporal connections.',
   '{"max_entities": 50, "confidence_threshold": 0.7, "include_context": true}');

-- =============================================
-- RUN MIGRATION
-- =============================================

-- Execute migration functions
SELECT public.migrate_entity_types();
SELECT public.migrate_relationship_types();

-- Update triggers for timestamp fields on new tables
CREATE TRIGGER update_timestamp_entity_types
  BEFORE UPDATE ON public.entity_types
  FOR EACH ROW EXECUTE PROCEDURE public.update_timestamp();

CREATE TRIGGER update_timestamp_relationship_types  
  BEFORE UPDATE ON public.relationship_types
  FOR EACH ROW EXECUTE PROCEDURE public.update_timestamp();

CREATE TRIGGER update_timestamp_domains
  BEFORE UPDATE ON public.domains  
  FOR EACH ROW EXECUTE PROCEDURE public.update_timestamp();

CREATE TRIGGER update_timestamp_extraction_templates
  BEFORE UPDATE ON public.extraction_templates
  FOR EACH ROW EXECUTE PROCEDURE public.update_timestamp();

-- Enable RLS on new tables
ALTER TABLE public.entity_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.relationship_types ENABLE ROW LEVEL SECURITY;  
ALTER TABLE public.entity_type_domains ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.relationship_type_domains ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.domains ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_templates ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE public.entity_types IS 'Defines entity types for domain-specific knowledge extraction';
COMMENT ON TABLE public.relationship_types IS 'Defines relationship types for domain-specific knowledge extraction';
COMMENT ON TABLE public.domains IS 'Business domain configurations for organizing knowledge';
COMMENT ON TABLE public.extraction_templates IS 'Templates for configuring AI-based knowledge extraction';
