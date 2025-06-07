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
