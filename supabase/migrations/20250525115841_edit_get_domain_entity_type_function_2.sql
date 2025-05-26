-- Delete the existing function if it exists
DROP FUNCTION IF EXISTS public.get_domain_entity_types(TEXT);

-- Function to get entity types for a domain
CREATE OR REPLACE FUNCTION public.get_domain_entity_types(domain_name TEXT)
RETURNS TABLE(id INTEGER, name TEXT, display_name TEXT, description TEXT, color TEXT, icon TEXT, extraction_pattern TEXT, validation_rules jsonb, examples jsonb, is_active BOOL, created_by UUID, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ, is_primary BOOLEAN) AS $func$
BEGIN
  RETURN QUERY
  SELECT *, etd.is_primary
  FROM public.entity_types et
  JOIN public.entity_type_domains etd ON et.id = etd.entity_type_id
  JOIN public.domains d ON etd.domain_id = d.id
  WHERE d.name = domain_name AND et.is_active = TRUE;
END;
$func$ LANGUAGE plpgsql SECURITY DEFINER;


