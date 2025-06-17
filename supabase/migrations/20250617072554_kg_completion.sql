-- Migration: Create Knowledge Graph Completion Suggestions Table
-- File: 20250617000001_create_kg_completion_suggestions.sql

-- Create enum for suggestion types
CREATE TYPE suggestion_type AS ENUM ('entity', 'relationship');

-- Create enum for suggestion status
CREATE TYPE suggestion_status AS ENUM ('pending', 'accepted', 'rejected', 'applied');

-- Create enum for suggestion priority
CREATE TYPE suggestion_priority AS ENUM ('low', 'medium', 'high', 'critical');

-- Create the main suggestions table
CREATE TABLE IF NOT EXISTS public.kg_completion_suggestions (
    id UUID DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
    
    -- Basic suggestion info
    suggestion_type suggestion_type NOT NULL,
    status suggestion_status DEFAULT 'pending' NOT NULL,
    priority suggestion_priority DEFAULT 'medium' NOT NULL,
    
    -- Confidence and reasoning
    confidence FLOAT NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    reason TEXT NOT NULL,
    source TEXT NOT NULL, -- 'relationship_reference', 'domain_knowledge', 'cooccurrence', etc.
    
    -- Entity suggestion specific fields
    suggested_entity_text TEXT,
    suggested_entity_type TEXT,
    
    -- Relationship suggestion specific fields
    source_entity_id UUID REFERENCES public.kg_entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES public.kg_entities(id) ON DELETE CASCADE,
    suggested_relationship_type TEXT,
    source_entity_text TEXT, -- For display purposes
    target_entity_text TEXT, -- For display purposes
    
    -- Applied suggestion tracking
    applied_entity_id UUID REFERENCES public.kg_entities(id) ON DELETE SET NULL,
    applied_relationship_id UUID REFERENCES public.kg_relationships(id) ON DELETE SET NULL,
    applied_at TIMESTAMP WITH TIME ZONE,
    applied_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    
    -- Review and feedback
    reviewed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,
    rejection_reason TEXT,
    
    -- Metadata
    context_data JSONB, -- Additional context about the suggestion
    validation_errors JSONB, -- Any validation issues found
    
    -- Audit fields
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_suggestion_type CHECK (
        (suggestion_type = 'entity' AND suggested_entity_text IS NOT NULL AND suggested_entity_type IS NOT NULL) OR
        (suggestion_type = 'relationship' AND source_entity_id IS NOT NULL AND target_entity_id IS NOT NULL AND suggested_relationship_type IS NOT NULL)
    ),
    
    CONSTRAINT valid_applied_tracking CHECK (
        (suggestion_type = 'entity' AND status = 'applied' AND applied_entity_id IS NOT NULL) OR
        (suggestion_type = 'relationship' AND status = 'applied' AND applied_relationship_id IS NOT NULL) OR
        (status != 'applied')
    )
);

-- Create indexes for better performance
CREATE INDEX idx_kg_completion_suggestions_type ON public.kg_completion_suggestions(suggestion_type);
CREATE INDEX idx_kg_completion_suggestions_status ON public.kg_completion_suggestions(status);
CREATE INDEX idx_kg_completion_suggestions_priority ON public.kg_completion_suggestions(priority);
CREATE INDEX idx_kg_completion_suggestions_confidence ON public.kg_completion_suggestions(confidence);
CREATE INDEX idx_kg_completion_suggestions_source_entity ON public.kg_completion_suggestions(source_entity_id);
CREATE INDEX idx_kg_completion_suggestions_target_entity ON public.kg_completion_suggestions(target_entity_id);
CREATE INDEX idx_kg_completion_suggestions_created_by ON public.kg_completion_suggestions(created_by);
CREATE INDEX idx_kg_completion_suggestions_created_at ON public.kg_completion_suggestions(created_at);
CREATE INDEX idx_kg_completion_suggestions_applied_entity ON public.kg_completion_suggestions(applied_entity_id);
CREATE INDEX idx_kg_completion_suggestions_applied_relationship ON public.kg_completion_suggestions(applied_relationship_id);

-- Create GIN index for context_data JSONB
CREATE INDEX idx_kg_completion_suggestions_context_data ON public.kg_completion_suggestions USING GIN(context_data);

-- Create composite indexes for common queries
CREATE INDEX idx_kg_completion_suggestions_type_status ON public.kg_completion_suggestions(suggestion_type, status);
CREATE INDEX idx_kg_completion_suggestions_status_priority ON public.kg_completion_suggestions(status, priority);
CREATE INDEX idx_kg_completion_suggestions_type_confidence ON public.kg_completion_suggestions(suggestion_type, confidence DESC);

-- Create update timestamp trigger
CREATE TRIGGER update_kg_completion_suggestions_timestamp 
    BEFORE UPDATE ON public.kg_completion_suggestions 
    FOR EACH ROW 
    EXECUTE FUNCTION public.update_timestamp();

-- Create function to get suggestion statistics
CREATE OR REPLACE FUNCTION public.get_kg_completion_stats()
RETURNS TABLE (
    total_suggestions BIGINT,
    pending_suggestions BIGINT,
    accepted_suggestions BIGINT,
    rejected_suggestions BIGINT,
    applied_suggestions BIGINT,
    entity_suggestions BIGINT,
    relationship_suggestions BIGINT,
    avg_confidence FLOAT,
    high_priority_pending BIGINT
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_suggestions,
        COUNT(CASE WHEN s.status = 'pending' THEN 1 END)::BIGINT as pending_suggestions,
        COUNT(CASE WHEN s.status = 'accepted' THEN 1 END)::BIGINT as accepted_suggestions,
        COUNT(CASE WHEN s.status = 'rejected' THEN 1 END)::BIGINT as rejected_suggestions,
        COUNT(CASE WHEN s.status = 'applied' THEN 1 END)::BIGINT as applied_suggestions,
        COUNT(CASE WHEN s.suggestion_type = 'entity' THEN 1 END)::BIGINT as entity_suggestions,
        COUNT(CASE WHEN s.suggestion_type = 'relationship' THEN 1 END)::BIGINT as relationship_suggestions,
        AVG(s.confidence)::FLOAT as avg_confidence,
        COUNT(CASE WHEN s.status = 'pending' AND s.priority = 'high' THEN 1 END)::BIGINT as high_priority_pending
    FROM public.kg_completion_suggestions s;
END;
$$;

-- Grant permissions
GRANT ALL ON public.kg_completion_suggestions TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_kg_completion_stats() TO authenticated;

-- Add RLS policies
ALTER TABLE public.kg_completion_suggestions ENABLE ROW LEVEL SECURITY;

-- Policy for viewing suggestions (users with kg:read permission)
CREATE POLICY "Users can view kg completion suggestions" ON public.kg_completion_suggestions
    FOR SELECT USING (public.check_user_permission(auth.uid(), 'kg:read'));

-- Policy for managing suggestions (users with kg:edit permission)
CREATE POLICY "Users can manage kg completion suggestions" ON public.kg_completion_suggestions
    USING (public.check_user_permission(auth.uid(), 'kg:edit'));

-- Add comments for documentation
COMMENT ON TABLE public.kg_completion_suggestions IS 'Stores knowledge graph completion suggestions for entities and relationships';
