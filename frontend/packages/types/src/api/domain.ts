import { ApiResponse, PaginatedResponse } from "../models";
import {
  Domain,
  DomainDetail,
  EntityType,
  RelationshipType,
  CreateDomainRequest,
  UpdateDomainRequest,
  CreateEntityTypeRequest,
  UpdateEntityTypeRequest,
  CreateRelationshipTypeRequest,
  UpdateRelationshipTypeRequest,
  DomainSearchRequest,
  EntityTypeSearchRequest,
  RelationshipTypeSearchRequest,
  RelationshipTypeSearchResponse,
  TypeDomainMappingRequest,
  TypeValidationRequest,
  TypeValidationResponse,
  DomainStats,
  CompatibleRelationshipsResponse,
  DomainAnalyticsOverview,
  BulkCreateEntityTypesRequest,
  BulkCreateEntityTypesResponse,
  BulkCreateRelationshipTypesRequest,
  BulkCreateRelationshipTypesResponse,
} from "../models/domain";

// =============================================
// DOMAIN INTERFACES
// =============================================

export interface ICreateDomainRequest extends CreateDomainRequest {}
export interface ICreateDomainResponse extends ApiResponse<Domain> {}

export interface IReadDomainsRequest extends DomainSearchRequest {}
export interface IReadDomainsResponse extends PaginatedResponse<Domain> {}

export interface IReadDomainRequest {
  id: string;
  include_types?: boolean;
}
export interface IReadDomainResponse extends ApiResponse<DomainDetail> {}

export interface IUpdateDomainRequest extends UpdateDomainRequest {
  id: string;
}
export interface IUpdateDomainResponse extends ApiResponse<Domain> {}

export interface IDeleteDomainRequest {
  id: string;
}
export interface IDeleteDomainResponse
  extends ApiResponse<{ message: string }> {}

export interface IGetDomainStatsRequest {
  id: string;
}
export interface IGetDomainStatsResponse extends ApiResponse<DomainStats> {}

// =============================================
// ENTITY TYPE INTERFACES
// =============================================

export interface ICreateEntityTypeRequest extends CreateEntityTypeRequest {}
export interface ICreateEntityTypeResponse extends ApiResponse<EntityType> {}

export interface IReadEntityTypesRequest extends EntityTypeSearchRequest {}
export interface IReadEntityTypesResponse
  extends PaginatedResponse<EntityType> {}

export interface IReadEntityTypeRequest {
  id: string;
  include_domains?: boolean;
  include_usage?: boolean;
}
export interface IReadEntityTypeResponse extends ApiResponse<EntityType> {}

export interface IUpdateEntityTypeRequest extends UpdateEntityTypeRequest {
  id: string;
}
export interface IUpdateEntityTypeResponse extends ApiResponse<EntityType> {}

export interface IDeleteEntityTypeRequest {
  id: string;
}
export interface IDeleteEntityTypeResponse
  extends ApiResponse<{ message: string }> {}

// =============================================
// RELATIONSHIP TYPE INTERFACES
// =============================================

export interface ICreateRelationshipTypeRequest
  extends CreateRelationshipTypeRequest {}
export interface ICreateRelationshipTypeResponse
  extends ApiResponse<RelationshipType> {}

export interface IReadRelationshipTypesRequest
  extends RelationshipTypeSearchRequest {}
export interface IReadRelationshipTypesResponse
  extends ApiResponse<RelationshipTypeSearchResponse> {}

export interface IReadRelationshipTypeRequest {
  id: string;
  include_domains?: boolean;
  include_usage?: boolean;
}
export interface IReadRelationshipTypeResponse
  extends ApiResponse<RelationshipType> {}

export interface IUpdateRelationshipTypeRequest
  extends UpdateRelationshipTypeRequest {
  id: string;
}
export interface IUpdateRelationshipTypeResponse
  extends ApiResponse<RelationshipType> {}

export interface IDeleteRelationshipTypeRequest {
  id: string;
}
export interface IDeleteRelationshipTypeResponse
  extends ApiResponse<{ message: string }> {}

// =============================================
// DOMAIN MAPPING INTERFACES
// =============================================

export interface IAddEntityTypeToDomainRequest
  extends Omit<TypeDomainMappingRequest, "type_id"> {
  type_id: string;
}
export interface IAddEntityTypeToDomainResponse extends ApiResponse<unknown> {}

export interface IRemoveEntityTypeFromDomainRequest {
  type_id: string;
  domain_id: string;
}
export interface IRemoveEntityTypeFromDomainResponse
  extends ApiResponse<{ message: string }> {}

export interface IAddRelationshipTypeToDomainRequest
  extends Omit<TypeDomainMappingRequest, "type_id"> {
  type_id: string;
}
export interface IAddRelationshipTypeToDomainResponse
  extends ApiResponse<unknown> {}

export interface IRemoveRelationshipTypeFromDomainRequest {
  type_id: string;
  domain_id: string;
}
export interface IRemoveRelationshipTypeFromDomainResponse
  extends ApiResponse<{ message: string }> {}

// =============================================
// VALIDATION INTERFACES
// =============================================

export interface IValidateTypeConstraintsRequest
  extends TypeValidationRequest {}
export interface IValidateTypeConstraintsResponse
  extends ApiResponse<TypeValidationResponse> {}

// =============================================
// UTILITY INTERFACES
// =============================================

export interface IGetEntityTypesByDomainRequest {
  domain_name: string;
  primary_only?: boolean;
}
export interface IGetEntityTypesByDomainResponse
  extends ApiResponse<EntityType[]> {}

export interface IGetRelationshipTypesByDomainRequest {
  domain_name: string;
  primary_only?: boolean;
}
export interface IGetRelationshipTypesByDomainResponse
  extends ApiResponse<RelationshipType[]> {}

export interface IGetCompatibleRelationshipsRequest {
  source_entity_type_id: number;
  target_entity_type_id?: number;
  domain_ids?: number[];
}
export interface IGetCompatibleRelationshipsResponse
  extends ApiResponse<CompatibleRelationshipsResponse> {}

// =============================================
// ANALYTICS INTERFACES
// =============================================

export interface IGetDomainAnalyticsOverviewRequest {}
export interface IGetDomainAnalyticsOverviewResponse
  extends ApiResponse<DomainAnalyticsOverview> {}

// =============================================
// BULK OPERATION INTERFACES
// =============================================

export interface IBulkCreateEntityTypesRequest {
  entity_types: BulkCreateEntityTypesRequest;
}
export interface IBulkCreateEntityTypesResponse
  extends ApiResponse<BulkCreateEntityTypesResponse> {}

export interface IBulkCreateRelationshipTypesRequest {
  relationship_types: BulkCreateRelationshipTypesRequest;
}
export interface IBulkCreateRelationshipTypesResponse
  extends ApiResponse<BulkCreateRelationshipTypesResponse> {}
