export type EntityBase = {
  entity_text: string;
  entity_type: string;
  properties?: Record<string, any>;
  confidence?: number;
};

export type EntityCreate = EntityBase & {
  source_document_id?: string;
  is_verified?: boolean;
  verification_notes?: string;
};

export type EntityUpdate = Partial<EntityBase> & {
  is_verified?: boolean;
  verification_notes?: string;
};

export type Entity = EntityBase & {
  id: string;
  source_document_id?: string;
  neo4j_id?: string;
  fibo_class_id?: number;
  is_verified: boolean;
  verification_notes?: string;
  verified_by?: string;
  created_at: Date;
  updated_at: Date;
  embedding?: number[];
};

export type EntityInDB = Entity;

export type EntitySearchParams = {
  query_text?: string;
  entity_type?: string;
  source_document_id?: string;
  is_verified?: boolean;
  confidence_min?: number;
  semantic_search: boolean;
  skip: number;
  limit: number;
};

export type EntityConflict = {
  id: string;
  entity_id_1: string;
  entity_id_2: string;
  similarity_score: number;
  conflict_type: string;
  status: string;
  resolution_notes?: string;
  resolved_by?: string;
  created_at: Date;
  updated_at: Date;
  entity1?: Entity;
  entity2?: Entity;
};

export type EntityResolution = {
  resolution_type: "merge" | "keep_separate" | "delete";
  keep_entity_id?: string;
  merged_properties?: Record<string, any>;
  notes?: string;
};
