import {
	ICreateEntityRequest,
	ICreateEntityResponse,
	ISearchKGEntitiesRequest,
	IReadEntityRequest,
	IReadEntityResponse,
	IKGCompletionRequest,
	IKGCompletionRequestResponse,
	IKGCompletionSuggestionsResponse,
	IKGCompletionStatsResponse,
	IKGCompletionActionResponse,
	IKGCompletionSuggestionResponse,
	ISuggestionActionRequest,
	ISuggestionFilterRequest,
	IUpdateEntityRequest,
	IUpdateEntityResponse,
	IDeleteEntityRequest,
	IDeleteEntityResponse,
	IReadEntityRelationshipsRequest,
	IReadEntityRelationshipsResponse,
	ICreateRelationshipRequest,
	ICreateRelationshipResponse,
	IGetKnowledgeGraphStatsRequest,
	IGetKnowledgeGraphStatsResponse,
	ICreateOrMergeEntityRequest,
	ICreateOrMergeEntityResponse,
	IGetEntityRequest,
	IEntitySearchResponse,
	IGetEntityTypesResponse,
	IGetEntityNeighborsRequest,
	IGetEntityNeighborsResponse,
	IGetRelationshipRequest,
	IGetEntityRelationshipsRequest,
	IRelationshipSearchResponse,
	IGetSubgraphRequest,
	ISubgraphResponse,
	IFindPathsRequest,
	IPathResponse,
	IExecuteQueryRequest,
	IExecuteQueryResponse,
	IGetStatsResponse,
	IGetInvestmentInsightsRequest,
	IGetInvestmentInsightsResponse,
	IGlobalSearchRequest,
	IGlobalSearchResponse,
	Entity,
	Relationship,
	ISearchRelationshipsRequest,
} from "@vbkg/types";

import { api } from "../config/axios";
import { API_ENDPOINTS } from "@vbkg/utils";

const createEntityRequest = async (input: ICreateEntityRequest) => {
	return await api().post<ICreateEntityResponse>(
		API_ENDPOINTS.CREATE_ENTITY,
		input,
	);
};

const readEntity = async (input: IReadEntityRequest) => {
	return await api().get<IReadEntityResponse>(
		API_ENDPOINTS.READ_ENTITY(input.id),
		{
			params: input,
		},
	);
};

const updateEntity = async (input: IUpdateEntityRequest) => {
	return await api().put<IUpdateEntityResponse>(
		API_ENDPOINTS.UPDATE_ENTITY(input.id),
		input,
	);
};

const deleteEntity = async (input: IDeleteEntityRequest) => {
	return await api().delete<IDeleteEntityResponse>(
		API_ENDPOINTS.DELETE_ENTITY(input.id),
	);
};

const readEntityRelationships = async (
	input: IReadEntityRelationshipsRequest,
) => {
	return await api().get<IReadEntityRelationshipsResponse>(
		API_ENDPOINTS.READ_ENTITY_RELATIONSHIPS(input.id),
		{
			params: input,
		},
	);
};

const createRelationship = async (input: ICreateRelationshipRequest) => {
	return await api().post<ICreateRelationshipResponse>(
		API_ENDPOINTS.CREATE_RELATIONSHIP,
		input,
	);
};

const getKnowledgeGraphStats = async (
	input: IGetKnowledgeGraphStatsRequest,
) => {
	return await api().get<IGetKnowledgeGraphStatsResponse>(
		API_ENDPOINTS.GET_KNOWLEDGE_GRAPH_STATS,
		{
			params: input,
		},
	);
};

const createOrMergeEntity = async (input: ICreateOrMergeEntityRequest) => {
	return await api().post<ICreateOrMergeEntityResponse>(
		API_ENDPOINTS.CREATE_OR_MERGE_ENTITY,
		input,
	);
};

// Entity endpoints
const getEntity = async (input: IGetEntityRequest) => {
	return await api().get<Entity>(API_ENDPOINTS.GET_KG_ENTITY(input.entity_id), {
		params: {
			include_relationships: input.include_relationships,
		},
	});
};

const searchEntities = async (input: ISearchKGEntitiesRequest) => {
	return await api().get<IEntitySearchResponse>(
		API_ENDPOINTS.SEARCH_KG_ENTITIES,
		{
			params: {
				query: input.query,
				limit: input.limit,
				skip: input.skip,
				min_confidence: input.min_confidence,
				verified_only: input.verified_only,
				semantic_search: input.semantic_search,
			},
			paramsSerializer: (params) => {
				const querySearch = new URLSearchParams();
				querySearch.append("query", params.query || "");
				querySearch.append("limit", String(params.limit || 10));
				querySearch.append("skip", String(params.skip || 0));
				querySearch.append(
					"min_confidence",
					String(params.min_confidence || 0),
				);
				querySearch.append(
					"verified_only",
					String(params.verified_only || false),
				);
				querySearch.append(
					"semantic_search",
					String(params.semantic_search || false),
				);

				return querySearch.toString();
			},
		},
	);
};

const searchRelationships = async (input: ISearchRelationshipsRequest) => {
	return await api().get<IRelationshipSearchResponse>(
		API_ENDPOINTS.SEARCH_KG_RELATIONSHIPS,
		{
			params: {
				query: input.query,
				limit: input.limit,
				skip: input.skip,
				min_confidence: input.min_confidence,
				verified_only: input.verified_only,
			},
			paramsSerializer: (params) => {
				const querySearch = new URLSearchParams();
				querySearch.append("query", params.query || "");
				querySearch.append("limit", String(params.limit || 10));
				querySearch.append("skip", String(params.skip || 0));
				querySearch.append(
					"min_confidence",
					String(params.min_confidence || 0),
				);
				querySearch.append(
					"verified_only",
					String(params.verified_only || false),
				);

				return querySearch.toString();
			},
		},
	);
};

const getEntityTypes = async () => {
	return await api().get<IGetEntityTypesResponse>(
		API_ENDPOINTS.GET_KG_ENTITY_TYPES,
	);
};

const getEntityNeighbors = async (input: IGetEntityNeighborsRequest) => {
	return await api().get<IGetEntityNeighborsResponse>(
		API_ENDPOINTS.GET_KG_ENTITY_NEIGHBORS(input.entity_id),
		{
			params: {
				max_depth: input.max_depth,
				relationship_types: input.relationship_types,
				limit_per_level: input.limit_per_level,
			},
		},
	);
};

// Relationship endpoints
const getRelationship = async (input: IGetRelationshipRequest) => {
	return await api().get<Relationship>(
		API_ENDPOINTS.GET_KG_RELATIONSHIP(input.relationship_id),
	);
};

const getEntityRelationships = async (
	input: IGetEntityRelationshipsRequest,
) => {
	return await api().get<IRelationshipSearchResponse>(
		API_ENDPOINTS.GET_KG_ENTITY_RELATIONSHIPS(input.entity_id),
		{
			params: {
				relationship_types: input.relationship_types,
				direction: input.direction,
				limit: input.limit,
				skip: input.skip,
			},
		},
	);
};

// Graph traversal endpoints
const getSubgraph = async (input: IGetSubgraphRequest) => {
	return await api().get<ISubgraphResponse>(
		API_ENDPOINTS.GET_KG_SUBGRAPH(input.entity_id),
		{
			params: {
				radius: input.radius,
				max_nodes: input.max_nodes,
				relationship_types: input.relationship_types,
			},
		},
	);
};

const findPaths = async (input: IFindPathsRequest) => {
	return await api().post<IPathResponse[]>(API_ENDPOINTS.FIND_KG_PATHS, input);
};

const executeQuery = async (input: IExecuteQueryRequest) => {
	return await api().post<IExecuteQueryResponse>(
		API_ENDPOINTS.EXECUTE_KG_QUERY,
		input,
	);
};

// Analytics & Statistics
const getStats = async () => {
	return await api().get<IGetStatsResponse>(API_ENDPOINTS.GET_KG_STATS);
};

const getInvestmentInsights = async (input: IGetInvestmentInsightsRequest) => {
	return await api().get<IGetInvestmentInsightsResponse>(
		API_ENDPOINTS.GET_KG_INVESTMENT_INSIGHTS,
		{
			params: {
				entity_type: input.entity_type,
				limit: input.limit,
			},
		},
	);
};

// Search & Discovery
const globalSearch = async (input: IGlobalSearchRequest) => {
	return await api().get<IGlobalSearchResponse>(
		API_ENDPOINTS.KG_GLOBAL_SEARCH,
		{
			params: {
				query: input.query,
				search_type: input.search_type,
				semantic: input.semantic,
				limit: input.limit,
			},
		},
	);
};

// Generate KG Completion
const generateKGCompletion = async (input: IKGCompletionRequest) => {
	return await api().post<IKGCompletionRequestResponse>(
		API_ENDPOINTS.KG_COMPLETION_GENERATE,
		input,
	);
};

// Get completion suggestions with filters
const getCompletionSuggestions = async (input: ISuggestionFilterRequest) => {
	return await api().get<IKGCompletionSuggestionsResponse>(
		API_ENDPOINTS.KG_COMPLETION_SUGGESTIONS,
		{
			params: {
				suggestion_type: input.suggestion_type,
				status: input.status,
				priority: input.priority,
				min_confidence: input.min_confidence,
				max_confidence: input.max_confidence,
				source: input.source,
				limit: input.limit || 50,
				skip: input.skip || 0,
			},
		},
	);
};

// Get single completion suggestion
const getCompletionSuggestion = async (suggestionId: string) => {
	return await api().get<IKGCompletionSuggestionResponse>(
		API_ENDPOINTS.KG_COMPLETION_SUGGESTION(suggestionId),
	);
};

// Handle suggestion actions (accept, reject, apply)
const handleSuggestionAction = async (input: ISuggestionActionRequest) => {
	return await api().post<IKGCompletionActionResponse>(
		API_ENDPOINTS.KG_COMPLETION_ACTIONS,
		input,
	);
};

// Delete suggestion
const deleteSuggestion = async (suggestionId: string) => {
	return await api().delete<IKGCompletionActionResponse>(
		API_ENDPOINTS.KG_COMPLETION_SUGGESTION(suggestionId),
	);
};

// Get completion statistics
const getCompletionStats = async () => {
	return await api().get<IKGCompletionStatsResponse>(
		API_ENDPOINTS.KG_COMPLETION_STATS,
	);
};

export const KnowledgeGraphService = {
	// Entities
	getEntity,
	searchEntities,
	getEntityTypes,
	getEntityNeighbors,

	// Relationships
	searchRelationships,
	getRelationship,
	getEntityRelationships,

	// Graph Traversal
	getSubgraph,
	findPaths,
	executeQuery,

	// Analytics
	getStats,
	getInvestmentInsights,

	// Search
	globalSearch,

	createEntityRequest,
	readEntity,
	updateEntity,
	deleteEntity,
	readEntityRelationships,
	createRelationship,
	getKnowledgeGraphStats,
	createOrMergeEntity,

	generateKGCompletion,
	getCompletionSuggestions,
	getCompletionSuggestion,
	handleSuggestionAction,
	deleteSuggestion,
	getCompletionStats,
};
