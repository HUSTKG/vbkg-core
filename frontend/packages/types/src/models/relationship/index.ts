export type RelationshipBase = {
  relationship_type: string;
  properties?: Record<string, any>;
  confidence?: number;
};

export type RelationshipCreate = RelationshipBase & {
  source_entity_id: string;
  target_entity_id: string;
  source_document_id?: string;
  is_verified?: boolean;
  verification_notes?: string;
};

export type RelationshipUpdate = Partial<RelationshipBase> & {
  is_verified?: boolean;
  verification_notes?: string;
};

export type Relationship = RelationshipBase & {
  id: string;
  source_entity_id: string;
  target_entity_id: string;
  source_document_id?: string;
  neo4j_id?: string;
  fibo_property_id?: number;
  is_verified: boolean;
  verification_notes?: string;
  verified_by?: string;
  created_at: Date;
  updated_at: Date;
};

export type RelationshipInDB = Relationship;

export type RelationshipSearchParams = {
  relationship_type?: string;
  source_entity_id?: string;
  target_entity_id?: string;
  source_document_id?: string;
  is_verified?: boolean;
  confidence_min?: number;
  skip: number;
  limit: number;
};
   
