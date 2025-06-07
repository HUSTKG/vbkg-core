import {
  ApiResponse,
  BulkMappingResponse,
  EntityMapping,
  EntityMappingCreate,
  EntityMappingUpdate,
  EntityTypeSuggestion,
  FIBOClass,
  FIBOClassCreate,
  FIBOClassSuggestion,
  FIBOClassUpdate,
  FIBOProperty,
  FIBOPropertyCreate,
  FIBOPropertySuggestion,
  FIBOPropertyUpdate,
  OntologyImportRequest,
  OntologyImportResponse,
  PaginatedResponse,
  RelationshipMapping,
  RelationshipMappingCreate,
  RelationshipMappingUpdate,
  RelationshipTypeSuggestion,
} from "../models";

export interface IReadFiboClassesRequest {
  domain?: string;
  search?: string;
  is_custom?: boolean;
  limit?: number;
  skip?: number;
}
export interface IReadFiboClassesResponse
  extends PaginatedResponse<FIBOClass> {}

export interface IReadFiboClassRequest {
  id: string;
}
export interface IReadFiboClassResponse extends ApiResponse<FIBOClass> {}

export interface ICreateFiboClassRequest extends FIBOClassCreate {}
export interface ICreateFiboClassResponse extends ApiResponse<FIBOClass> {}

export interface IUpdateFiboClassRequest extends FIBOClassUpdate {
  id: string;
}
export interface IUpdateFiboClassResponse extends ApiResponse<FIBOClass> {}

export interface IDeleteFiboClassRequest {
  id: string;
}
export interface IDeleteFiboClassResponse extends ApiResponse<unknown> {}

// FIBO Property Operations (keeping existing)
export interface IReadFiboPropertiesRequest {
  domain_class_id?: string;
  property_type?: "object" | "datatype";
  search?: string;
  is_custom?: boolean;
  limit?: number;
  skip?: number;
}
export interface IReadFiboPropertiesResponse
  extends PaginatedResponse<FIBOProperty> {}

export interface IReadFiboPropertyRequest {
  id: string;
}
export interface IReadFiboPropertyResponse extends ApiResponse<FIBOProperty> {}

export interface ICreateFiboPropertyRequest extends FIBOPropertyCreate {}
export interface ICreateFiboPropertyResponse
  extends ApiResponse<FIBOProperty> {}

export interface IUpdateFiboPropertyRequest extends FIBOPropertyUpdate {
  id: string;
}
export interface IUpdateFiboPropertyResponse
  extends ApiResponse<FIBOProperty> {}

export interface IDeleteFiboPropertyRequest {
  id: string;
}
export interface IDeleteFiboPropertyResponse extends ApiResponse<unknown> {}

// Ontology Import Operations (keeping existing)
export interface IImportOntologyRequest extends OntologyImportRequest {}
export interface IImportOntologyResponse
  extends ApiResponse<OntologyImportResponse> {}

// Updated Entity Mapping Operations
export interface IReadEntityMappingsRequest {
  entity_type_id?: number;
  mapping_status?: "pending" | "mapped" | "rejected" | "needs_review";
  is_verified?: boolean;
  auto_mapped?: boolean;
  search?: string;
  limit?: number;
  skip?: number;
}
export interface IReadEntityMappingsResponse
  extends PaginatedResponse<EntityMapping> {}

export interface IReadEntityMappingRequest {
  id: string;
}
export interface IReadEntityMappingResponse
  extends ApiResponse<EntityMapping> {}

export interface ICreateEntityMappingRequest extends EntityMappingCreate{ }
export interface ICreateEntityMappingResponse
  extends ApiResponse<EntityMapping> {}

export interface IUpdateEntityMappingRequest extends EntityMappingUpdate {
  id: string;
}
export interface IUpdateEntityMappingResponse
  extends ApiResponse<EntityMapping> {}

export interface IDeleteEntityMappingRequest {
  id: string;
}
export interface IDeleteEntityMappingResponse extends ApiResponse<unknown> {}

export interface IVerifyEntityMappingRequest {
  id: string;
  verified: boolean;
  notes?: string;
}
export interface IVerifyEntityMappingResponse
  extends ApiResponse<EntityMapping> {}

// Updated Relationship Mapping Operations
export interface IReadRelationshipMappingsRequest {
  relationship_type_id?: number;
  mapping_status?: "pending" | "mapped" | "rejected" | "needs_review";
  is_verified?: boolean;
  auto_mapped?: boolean;
  search?: string;
  limit?: number;
  skip?: number;
}
export interface IReadRelationshipMappingsResponse
  extends PaginatedResponse<RelationshipMapping> {}

export interface IReadRelationshipMappingRequest {
  id: string;
}
export interface IReadRelationshipMappingResponse
  extends ApiResponse<RelationshipMapping> {}

export interface ICreateRelationshipMappingRequest extends RelationshipMappingCreate {}

export interface IUpdateRelationshipMappingRequest
  extends RelationshipMappingUpdate {
  id: string;
}
export interface IUpdateRelationshipMappingResponse
  extends ApiResponse<RelationshipMapping> {}

export interface IDeleteRelationshipMappingRequest {
  id: string;
}
export interface IDeleteRelationshipMappingResponse
  extends ApiResponse<unknown> {}

export interface IVerifyRelationshipMappingRequest {
  id: string;
  verified: boolean;
  notes?: string;
}
export interface IVerifyRelationshipMappingResponse
  extends ApiResponse<RelationshipMapping> {}

// Suggestion Operations
export interface ISuggestEntityTypesRequest {
  text: string;
  context?: string;
  domain_id?: number;
  max_suggestions?: number;
}
export interface ISuggestEntityTypesResponse
  extends ApiResponse<EntityTypeSuggestion[]> {}

export interface ISuggestRelationshipTypesRequest {
  text: string;
  source_entity_type_id?: number;
  target_entity_type_id?: number;
  context?: string;
  domain_id?: number;
  max_suggestions?: number;
}
export interface ISuggestRelationshipTypesResponse
  extends ApiResponse<RelationshipTypeSuggestion[]> {}

export interface ISuggestFiboClassesRequest {
  entity_text?: string;
  entity_type?: string;
  entity_type_id?: number;
  context?: string;
  max_suggestions?: number;
}
export interface ISuggestFiboClassesResponse
  extends ApiResponse<FIBOClassSuggestion[]> {}

export interface ISuggestFiboPropertiesRequest {
  relationship_type?: string;
  relationship_type_id?: number;
  source_entity_type?: string;
  source_entity_type_id?: number;
  target_entity_type?: string;
  target_entity_type_id?: number;
  context?: string;
  max_suggestions?: number;
}
export interface ISuggestFiboPropertiesResponse
  extends ApiResponse<FIBOPropertySuggestion[]> {}

// Bulk Operations
export interface IBulkCreateEntityMappingsRequest {
  mappings: EntityMappingCreate[];
}
export interface IBulkCreateEntityMappingsResponse
  extends ApiResponse<BulkMappingResponse> {}

export interface IBulkCreateRelationshipMappingsRequest {
  mappings: RelationshipMappingCreate[];
}
export interface IBulkCreateRelationshipMappingsResponse
  extends ApiResponse<BulkMappingResponse> {}

// Analytics/Stats Operations
export interface IGetMappingStatsRequest {
  domain_id?: number;
}
export interface IGetMappingStatsResponse
  extends ApiResponse<{
    entity_mappings: {
      total: number;
      verified: number;
      pending: number;
      mapped: number;
      rejected: number;
      needs_review: number;
      auto_mapped: number;
    };
    relationship_mappings: {
      total: number;
      verified: number;
      pending: number;
      mapped: number;
      rejected: number;
      needs_review: number;
      auto_mapped: number;
    };
  }> {}
