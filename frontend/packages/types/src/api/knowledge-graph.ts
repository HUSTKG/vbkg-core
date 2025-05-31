import { Entity, Relationship } from "../models";

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

export interface IEntitySearchResponse {
  entities: Entity[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface ISearchRelationshipsRequest {
  query?: string;
  relationship_types?: string[];
  limit?: number;
  offset?: number;
  min_confidence?: number;
  verified_only?: boolean;
  semantic_search?: boolean;
}

export interface IRelationshipSearchResponse {
  relationships: Relationship[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

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

export interface ISubgraphResponse {
  center_entity_id: string;
  nodes: {
    id: string;
    neo4j_id: string;
    label: string;
    type: string;
    properties: Record<string, any>;
    is_center: string;
  }[];
  edges: {
    id: string;
    neo4j_id: string;
    source: string;
    target: string;
    type: string;
    properties: Record<string, any>;
  }[];
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
  entity_types: Array<{
    type: string;
    count: number;
  }>;
  relationship_types: Array<{
    type: string;
    count: number;
  }>;
  graph_metrics: {
    density: number;
    average_degree: number;
    connected_components: number;
  };
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
