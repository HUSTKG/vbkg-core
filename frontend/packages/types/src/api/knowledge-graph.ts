import { Entity, PaginatedResponse, Relationship } from "../models";
import {
	ApiResponse,
	CypherQuery,
	EntityCreate,
	EntityUpdate,
	RelationshipCreate,
} from "../models";

// Entity related types
export interface IGetEntityRequest {
	entity_id: string;
	include_relationships?: boolean;
}

export interface ISearchKGEntitiesRequest {
	query?: string;
	entity_types?: string[];
	limit?: number;
	offset?: number;
	min_confidence?: number;
	verified_only?: boolean;
	semantic_search?: boolean;
}

export interface IEntitySearchResponse
	extends PaginatedResponse<
		Entity & {
			relationship_count?: number;
			similarity_score?: number;
		}
	> { }

export interface ISearchRelationshipsRequest {
	query?: string;
	relationship_types?: string[];
	limit?: number;
	offset?: number;
	min_confidence?: number;
	verified_only?: boolean;
	semantic_search?: boolean;
}

export interface IRelationshipSearchResponse
	extends PaginatedResponse<Relationship> { }

export interface IGetEntityTypesResponse {
	types: Array<{
		type: string;
		count: number;
		description?: string;
	}>;
}

export interface IGetEntityNeighborsRequest {
	entity_id: string;
	max_depth?: number;
	relationship_types?: string[];
	limit_per_level?: number;
}

export interface IGetEntityNeighborsResponse {
	entity_id: string;
	neighbors: Record<string, Entity[]>; // depth level as key
	relationships: Relationship[];
}

// Relationship related types
export interface IGetRelationshipRequest {
	relationship_id: string;
}

export interface IGetEntityRelationshipsRequest {
	entity_id: string;
	relationship_types?: string[];
	direction?: "incoming" | "outgoing" | "both";
	limit?: number;
	offset?: number;
}

// Graph traversal types
export interface IGetSubgraphRequest {
	entity_id: string;
	radius?: number;
	max_nodes?: number;
	relationship_types?: string[];
}

export interface INode {
	id: string;
	neo4j_id: string;
	label: string;
	type: string;
	properties: Record<string, any>;
	is_center?: boolean; // Optional, used for center node
}

export interface IEdge {
	id: string;
	neo4j_id: string;
	source: string;
	target: string;
	type: string;
	properties: Record<string, any>;
}

export interface ISubgraphResponse {
	center_entity_id: string;
	nodes: INode[];
	edges: IEdge[];
	node_count: number;
	edge_count: number;
	radius: number;
}

export interface IFindPathsRequest {
	source_entity_id: string;
	target_entity_id: string;
	max_depth?: number;
	relationship_types?: string[];
}

export interface IPathResponse {
	path_id: string;
	entities: Entity[];
	relationships: Relationship[];
	length: number;
	confidence?: number;
}

export interface IExecuteQueryRequest {
	cypher_query: string;
	parameters?: Record<string, any>;
	limit?: number;
}

export interface IExecuteQueryResponse {
	records: Record<string, any>[];
	query: string;
	parameters?: Record<string, any>;
	count: number;
	execution_time?: number;
}

// Analytics types
export interface IGetStatsResponse {
	total_entities: number;
	total_relationships: number;
	avg_relationships_per_entity: number;
	recent_entities_count: number;
	entity_types: Array<{
		entity_type: string;
		count: number;
	}>;
	relationship_types: Array<{
		relationship_type: string;
		count: number;
	}>;
	last_updated: string;
}

export interface IGetInvestmentInsightsRequest {
	entity_type?: string;
	limit?: number;
}

export interface IGetInvestmentInsightsResponse {
	insights: Array<{
		type: string;
		title: string;
		description: string;
		entities: Entity[];
		confidence: number;
	}>;
	metadata: {
		generated_at: string;
		entity_type: string;
	};
}

// Search types
export interface IGlobalSearchRequest {
	query: string;
	search_type?: "entities" | "relationships" | "mixed";
	semantic?: boolean;
	limit?: number;
}

export interface IGlobalSearchResponse {
	query: string;
	search_type: string;
	semantic: boolean;
	results: {
		entities?: IEntitySearchResponse;
		relationships?: Relationship[];
	};
}

export interface ICreateEntityRequest extends EntityCreate { }
export interface ICreateEntityResponse extends ApiResponse<Entity> { }

export interface IReadEntityRequest {
	id: string;
}
export interface IReadEntityResponse extends ApiResponse<Entity> { }

export interface IReadEntityRelationshipsRequest {
	id: string;
	direction: "incoming" | "outgoing";
}
export interface IReadEntityRelationshipsResponse
	extends ApiResponse<Relationship[]> { }

export interface IUpdateEntityRequest extends EntityUpdate {
	id: string;
}
export interface IUpdateEntityResponse extends ApiResponse<Entity> { }

export interface IDeleteEntityRequest {
	id: string;
}
export interface IDeleteEntityResponse extends ApiResponse<unknown> { }

export interface ICreateRelationshipRequest extends RelationshipCreate { }
export interface ICreateRelationshipResponse
	extends ApiResponse<Relationship> { }

export interface IExcuteQueryRequest extends CypherQuery { }
export interface IExcuteQueryResponse extends ApiResponse<unknown[]> { }

export interface IGetKnowledgeGraphStatsRequest { }
export interface IGetKnowledgeGraphStatsResponse extends ApiResponse<unknown> { }

export interface ICreateOrMergeEntityRequest extends EntityCreate { }
export interface ICreateOrMergeEntityResponse extends ApiResponse<Entity> { }

// KG Completion Request Types
export interface IKGCompletionRequest {
  entity_ids?: string[];
  completion_types: string[];
  auto_apply_suggestions: boolean;
  confidence_threshold: number;
  limit_entities?: number;
  limit_relationships?: number;
}

export interface ISuggestionActionRequest {
  suggestion_ids: string[];
  action: 'accept' | 'reject' | 'apply';
  review_notes?: string;
  rejection_reason?: string;
}

export interface ISuggestionFilterRequest {
  suggestion_type?: 'entity' | 'relationship';
  status?: 'pending' | 'accepted' | 'rejected' | 'applied';
  priority?: 'low' | 'medium' | 'high' | 'critical';
  min_confidence?: number;
  max_confidence?: number;
  source?: string;
  limit?: number;
  skip?: number;
}

// KG Completion Response Types
export interface ICompletionSuggestion {
  id: string;
  suggestion_type: 'entity' | 'relationship';
  status: 'pending' | 'accepted' | 'rejected' | 'applied';
  priority: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  reason: string;
  source: string;
  
  // Entity specific
  suggested_entity_text?: string;
  suggested_entity_type?: string;
  
  // Relationship specific
  source_entity_id?: string;
  target_entity_id?: string;
  source_entity_text?: string;
  target_entity_text?: string;
  suggested_relationship_type?: string;
  
  // Applied tracking
  applied_entity_id?: string;
  applied_relationship_id?: string;
  applied_at?: string;
  applied_by?: string;
  
  // Review tracking
  reviewed_by?: string;
  reviewed_at?: string;
  review_notes?: string;
  rejection_reason?: string;
  
  // Metadata
  context_data?: Record<string, any>;
  validation_errors?: Record<string, any>;
  
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface IKGCompletionStats {
  total_suggestions: number;
  pending_suggestions: number;
  accepted_suggestions: number;
  rejected_suggestions: number;
  applied_suggestions: number;
  entity_suggestions: number;
  relationship_suggestions: number;
  avg_confidence: number;
  high_priority_pending: number;
}

export interface IKGCompletionResponse {
  suggestions: ICompletionSuggestion[];
  stats: {
    input_entities: number;
    input_relationships: number;
    suggested_entities: number;
    suggested_relationships: number;
    auto_applied: number;
  };
  success: boolean;
  message?: string;
  error?: string;
}

export interface ISuggestionActionResponse {
  processed_suggestions: string[];
  applied_entities: string[];
  applied_relationships: string[];
  errors: string[];
  success: boolean;
  message: string;
}

// API Response wrapper types
export interface IKGCompletionRequestResponse extends ApiResponse<IKGCompletionResponse> {}
export interface IKGCompletionSuggestionsResponse extends PaginatedResponse<ICompletionSuggestion> {}
export interface IKGCompletionStatsResponse extends ApiResponse<IKGCompletionStats> {}
export interface IKGCompletionActionResponse extends ApiResponse<ISuggestionActionResponse> {}
export interface IKGCompletionSuggestionResponse extends ApiResponse<ICompletionSuggestion> {}
