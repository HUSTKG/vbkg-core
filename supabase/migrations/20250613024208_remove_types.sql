-- Migration: Remove entity_types and relationship_types, use ontology classes/properties instead
-- File: 20250614_remove_entity_relationship_types.sql

-- 3. Update kg_entities to reference ontology_classes instead of entity_types
UPDATE public.kg_entities 
SET ontology_class_id = oc.id
FROM public.entity_types et
JOIN public.ontology_classes oc ON oc.uri = 'http://internal.domain/' || lower(replace(et.name, ' ', '_'))
WHERE public.kg_entities.entity_type_id = et.id
AND public.kg_entities.ontology_class_id IS NULL;

-- 4. Update kg_relationships to reference ontology_properties instead of relationship_types
UPDATE public.kg_relationships 
SET ontology_property_id = op.id
FROM public.relationship_types rt
JOIN public.ontology_properties op ON op.uri = 'http://internal.domain/' || lower(replace(rt.name, ' ', '_'))
WHERE public.kg_relationships.relationship_type_id = rt.id
AND public.kg_relationships.ontology_property_id IS NULL;

-- 5. Update entity_mappings to reference ontology_classes
ALTER TABLE public.entity_mappings ADD COLUMN IF NOT EXISTS ontology_class_uri text;
ALTER TABLE public.entity_mappings ADD COLUMN IF NOT EXISTS ontology_class_id integer;
ALTER TABLE public.entity_mappings ADD COLUMN IF NOT EXISTS mapping_status text DEFAULT 'pending';
ALTER TABLE public.entity_mappings ADD COLUMN IF NOT EXISTS is_verified boolean DEFAULT false;
ALTER TABLE public.entity_mappings ADD COLUMN IF NOT EXISTS auto_mapped boolean DEFAULT false;
ALTER TABLE public.entity_mappings ADD COLUMN IF NOT EXISTS mapping_notes text;
ALTER TABLE public.entity_mappings ADD COLUMN IF NOT EXISTS created_by uuid;
ALTER TABLE public.entity_mappings ADD COLUMN IF NOT EXISTS reviewed_by uuid;
ALTER TABLE public.entity_mappings ADD COLUMN IF NOT EXISTS reviewed_at timestamp with time zone;

UPDATE public.entity_mappings 
SET ontology_class_uri = oc.uri,
    ontology_class_id = oc.id,
    mapping_status = 'mapped',
    is_verified = true,
    auto_mapped = true
FROM public.entity_types et
JOIN public.ontology_classes oc ON oc.uri = 'http://internal.domain/' || lower(replace(et.name, ' ', '_'))
WHERE public.entity_mappings.entity_type_id = et.id;

-- 6. Update relationship_mappings to reference ontology_properties  
ALTER TABLE public.relationship_mappings ADD COLUMN IF NOT EXISTS ontology_property_uri text;
ALTER TABLE public.relationship_mappings ADD COLUMN IF NOT EXISTS ontology_property_id integer;
ALTER TABLE public.relationship_mappings ADD COLUMN IF NOT EXISTS mapping_status text DEFAULT 'pending';
ALTER TABLE public.relationship_mappings ADD COLUMN IF NOT EXISTS is_verified boolean DEFAULT false;
ALTER TABLE public.relationship_mappings ADD COLUMN IF NOT EXISTS auto_mapped boolean DEFAULT false;
ALTER TABLE public.relationship_mappings ADD COLUMN IF NOT EXISTS mapping_notes text;
ALTER TABLE public.relationship_mappings ADD COLUMN IF NOT EXISTS created_by uuid;
ALTER TABLE public.relationship_mappings ADD COLUMN IF NOT EXISTS reviewed_by uuid;
ALTER TABLE public.relationship_mappings ADD COLUMN IF NOT EXISTS reviewed_at timestamp with time zone;

UPDATE public.relationship_mappings 
SET ontology_property_uri = op.uri,
    ontology_property_id = op.id,
    mapping_status = 'mapped',
    is_verified = true,
    auto_mapped = true
FROM public.relationship_types rt
JOIN public.ontology_properties op ON op.uri = 'http://internal.domain/' || lower(replace(rt.name, ' ', '_'))
WHERE public.relationship_mappings.relationship_type_id = rt.id;


-- 9. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_entity_mappings_ontology_class_id ON public.entity_mappings(ontology_class_id);
CREATE INDEX IF NOT EXISTS idx_entity_mappings_mapping_status ON public.entity_mappings(mapping_status);
CREATE INDEX IF NOT EXISTS idx_relationship_mappings_ontology_property_id ON public.relationship_mappings(ontology_property_id);
CREATE INDEX IF NOT EXISTS idx_relationship_mappings_mapping_status ON public.relationship_mappings(mapping_status);

-- 10. Update domains table to work with ontology classes/properties
ALTER TABLE public.domains ADD COLUMN IF NOT EXISTS ontology_namespace text;
ALTER TABLE public.domains ADD COLUMN IF NOT EXISTS ontology_prefix text;
ALTER TABLE public.domains ADD COLUMN IF NOT EXISTS config jsonb DEFAULT '{}';

-- 11. Create domain_ontology_classes junction table (many-to-many)
CREATE TABLE IF NOT EXISTS public.domain_ontology_classes (
    id integer NOT NULL,
    domain_id integer NOT NULL,
    ontology_class_id integer NOT NULL,
    is_primary boolean DEFAULT false,
    domain_specific_config jsonb DEFAULT '{}',
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT domain_ontology_classes_pkey PRIMARY KEY (id),
    CONSTRAINT domain_ontology_classes_unique UNIQUE (domain_id, ontology_class_id)
);

CREATE SEQUENCE IF NOT EXISTS public.domain_ontology_classes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.domain_ontology_classes_id_seq OWNED BY public.domain_ontology_classes.id;
ALTER TABLE ONLY public.domain_ontology_classes ALTER COLUMN id SET DEFAULT nextval('public.domain_ontology_classes_id_seq'::regclass);

-- 12. Create domain_ontology_properties junction table (many-to-many)
CREATE TABLE IF NOT EXISTS public.domain_ontology_properties (
    id integer NOT NULL,
    domain_id integer NOT NULL,
    ontology_property_id integer NOT NULL,
    is_primary boolean DEFAULT false,
    domain_specific_config jsonb DEFAULT '{}',
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT domain_ontology_properties_pkey PRIMARY KEY (id),
    CONSTRAINT domain_ontology_properties_unique UNIQUE (domain_id, ontology_property_id)
);

CREATE SEQUENCE IF NOT EXISTS public.domain_ontology_properties_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.domain_ontology_properties_id_seq OWNED BY public.domain_ontology_properties.id;
ALTER TABLE ONLY public.domain_ontology_properties ALTER COLUMN id SET DEFAULT nextval('public.domain_ontology_properties_id_seq'::regclass);

-- 13. Add foreign key constraints for new junction tables
ALTER TABLE public.domain_ontology_classes
    ADD CONSTRAINT domain_ontology_classes_domain_id_fkey 
    FOREIGN KEY (domain_id) REFERENCES public.domains(id) ON DELETE CASCADE;

ALTER TABLE public.domain_ontology_classes
    ADD CONSTRAINT domain_ontology_classes_ontology_class_id_fkey 
    FOREIGN KEY (ontology_class_id) REFERENCES public.ontology_classes(id) ON DELETE CASCADE;

ALTER TABLE public.domain_ontology_properties
    ADD CONSTRAINT domain_ontology_properties_domain_id_fkey 
    FOREIGN KEY (domain_id) REFERENCES public.domains(id) ON DELETE CASCADE;

ALTER TABLE public.domain_ontology_properties
    ADD CONSTRAINT domain_ontology_properties_ontology_property_id_fkey 
    FOREIGN KEY (ontology_property_id) REFERENCES public.ontology_properties(id) ON DELETE CASCADE;

-- 14. Migrate existing domain mappings to new junction tables
INSERT INTO public.domain_ontology_classes (domain_id, ontology_class_id, is_primary, domain_specific_config)
SELECT 
    d.id as domain_id,
    oc.id as ontology_class_id,
    etd.is_primary,
    COALESCE(etd.domain_specific_config, '{}')
FROM public.entity_type_domains etd
JOIN public.domains d ON etd.domain_id = d.id
JOIN public.entity_types et ON etd.entity_type_id = et.id
JOIN public.ontology_classes oc ON oc.uri = 'http://internal.domain/' || lower(replace(et.name, ' ', '_'))
ON CONFLICT (domain_id, ontology_class_id) DO NOTHING;

INSERT INTO public.domain_ontology_properties (domain_id, ontology_property_id, is_primary, domain_specific_config)
SELECT 
    d.id as domain_id,
    op.id as ontology_property_id,
    rtd.is_primary,
    COALESCE(rtd.domain_specific_config, '{}')
FROM public.relationship_type_domains rtd
JOIN public.domains d ON rtd.domain_id = d.id
JOIN public.relationship_types rt ON rtd.relationship_type_id = rt.id
JOIN public.ontology_properties op ON op.uri = 'http://internal.domain/' || lower(replace(rt.name, ' ', '_'))
ON CONFLICT (domain_id, ontology_property_id) DO NOTHING;

-- 15. Create indexes for new junction tables
CREATE INDEX IF NOT EXISTS idx_domain_ontology_classes_domain_id ON public.domain_ontology_classes(domain_id);
CREATE INDEX IF NOT EXISTS idx_domain_ontology_classes_ontology_class_id ON public.domain_ontology_classes(ontology_class_id);
CREATE INDEX IF NOT EXISTS idx_domain_ontology_properties_domain_id ON public.domain_ontology_properties(domain_id);
CREATE INDEX IF NOT EXISTS idx_domain_ontology_properties_ontology_property_id ON public.domain_ontology_properties(ontology_property_id);

-- 16. Grant permissions on new tables
GRANT ALL ON TABLE public.domain_ontology_classes TO anon;
GRANT ALL ON TABLE public.domain_ontology_classes TO authenticated;
GRANT ALL ON TABLE public.domain_ontology_classes TO service_role;

GRANT ALL ON TABLE public.domain_ontology_properties TO anon;
GRANT ALL ON TABLE public.domain_ontology_properties TO authenticated;
GRANT ALL ON TABLE public.domain_ontology_properties TO service_role;

GRANT ALL ON SEQUENCE public.domain_ontology_classes_id_seq TO anon;
GRANT ALL ON SEQUENCE public.domain_ontology_classes_id_seq TO authenticated;
GRANT ALL ON SEQUENCE public.domain_ontology_classes_id_seq TO service_role;

GRANT ALL ON SEQUENCE public.domain_ontology_properties_id_seq TO anon;
GRANT ALL ON SEQUENCE public.domain_ontology_properties_id_seq TO authenticated;
GRANT ALL ON SEQUENCE public.domain_ontology_properties_id_seq TO service_role;

-- 17. Drop foreign key constraints from kg_entities and kg_relationships referencing old tables
ALTER TABLE public.kg_entities DROP CONSTRAINT IF EXISTS kg_entities_entity_type_id_fkey;
ALTER TABLE public.kg_relationships DROP CONSTRAINT IF EXISTS validate_kg_relationships;

-- 18. Drop old tables (be careful - this removes data!)
-- Uncomment these lines when you're ready to remove the old tables
-- DROP TABLE IF EXISTS public.entity_type_domains CASCADE;
-- DROP TABLE IF EXISTS public.relationship_type_domains CASCADE;
-- DROP TABLE IF EXISTS public.entity_types CASCADE;
-- DROP TABLE IF EXISTS public.relationship_types CASCADE;

-- 19. Update database functions to work with new structure
CREATE OR REPLACE FUNCTION public.get_domain_ontology_classes(domain_name text)
RETURNS TABLE(
    id integer, 
    uri text, 
    label text, 
    description text, 
    domain text,
    parent_class_id integer,
    properties jsonb,
    is_custom boolean,
    created_at timestamp with time zone, 
    updated_at timestamp with time zone, 
    is_primary boolean,
    domain_specific_config jsonb
)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    oc.id, oc.uri, oc.label, oc.description, oc.domain, oc.parent_class_id,
    oc.properties, oc.is_custom, oc.created_at, oc.updated_at,
    doc.is_primary, doc.domain_specific_config
  FROM public.ontology_classes oc
  JOIN public.domain_ontology_classes doc ON oc.id = doc.ontology_class_id
  JOIN public.domains d ON doc.domain_id = d.id
  WHERE d.name = domain_name;
END;
$$;

CREATE OR REPLACE FUNCTION public.get_domain_ontology_properties(domain_name text)
RETURNS TABLE(
    id integer, 
    uri text, 
    label text, 
    description text,
    domain_class_id integer,
    range_class_id integer,
    property_type text,
    domain text,
    is_custom boolean,
    created_at timestamp with time zone, 
    updated_at timestamp with time zone, 
    is_primary boolean,
    domain_specific_config jsonb
)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    op.id, op.uri, op.label, op.description, op.domain_class_id, op.range_class_id,
    op.property_type, op.domain, op.is_custom, op.created_at, op.updated_at,
    dop.is_primary, dop.domain_specific_config
  FROM public.ontology_properties op
  JOIN public.domain_ontology_properties dop ON op.id = dop.ontology_property_id
  JOIN public.domains d ON dop.domain_id = d.id
  WHERE d.name = domain_name;
END;
$$;

-- 20. Create helper functions for ontology class/property lookup
CREATE OR REPLACE FUNCTION public.get_ontology_class_id(class_uri text, domain_name text DEFAULT NULL)
RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  class_id INTEGER;
BEGIN
  IF domain_name IS NULL THEN
    SELECT id INTO class_id FROM public.ontology_classes WHERE uri = class_uri;
  ELSE
    SELECT oc.id INTO class_id 
    FROM public.ontology_classes oc
    JOIN public.domain_ontology_classes doc ON oc.id = doc.ontology_class_id
    JOIN public.domains d ON doc.domain_id = d.id
    WHERE oc.uri = class_uri AND d.name = domain_name;
  END IF;
  RETURN class_id;
END;
$$;

CREATE OR REPLACE FUNCTION public.get_ontology_property_id(property_uri text, domain_name text DEFAULT NULL)
RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  property_id INTEGER;
BEGIN
  IF domain_name IS NULL THEN
    SELECT id INTO property_id FROM public.ontology_properties WHERE uri = property_uri;
  ELSE
    SELECT op.id INTO property_id
    FROM public.ontology_properties op
    JOIN public.domain_ontology_properties dop ON op.id = dop.ontology_property_id
    JOIN public.domains d ON dop.domain_id = d.id
    WHERE op.uri = property_uri AND d.name = domain_name;
  END IF;
  RETURN property_id;
END;
$$;

-- 21. Grant function permissions
GRANT ALL ON FUNCTION public.get_domain_ontology_classes(text) TO anon;
GRANT ALL ON FUNCTION public.get_domain_ontology_classes(text) TO authenticated;
GRANT ALL ON FUNCTION public.get_domain_ontology_classes(text) TO service_role;

GRANT ALL ON FUNCTION public.get_domain_ontology_properties(text) TO anon;
GRANT ALL ON FUNCTION public.get_domain_ontology_properties(text) TO authenticated;
GRANT ALL ON FUNCTION public.get_domain_ontology_properties(text) TO service_role;

GRANT ALL ON FUNCTION public.get_ontology_class_id(text, text) TO anon;
GRANT ALL ON FUNCTION public.get_ontology_class_id(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.get_ontology_class_id(text, text) TO service_role;

GRANT ALL ON FUNCTION public.get_ontology_property_id(text, text) TO anon;
GRANT ALL ON FUNCTION public.get_ontology_property_id(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.get_ontology_property_id(text, text) TO service_role;
