import {
  ApiResponse,
  CypherQuery,
  EntityCreate,
  EntityUpdate,
  RelationshipCreate,
} from "../models";
import { Entity } from "../models/entity";
import { Relationship } from "../models/relationship";

export interface ICreateEntityRequest extends EntityCreate {}
export interface ICreateEntityResponse extends ApiResponse<Entity> {}

export interface IReadEntityRequest {
  id: string;
}
export interface IReadEntityResponse extends ApiResponse<Entity> {}

export interface IReadEntityRelationshipsRequest {
  id: string;
  direction: "incoming" | "outgoing";
}
export interface IReadEntityRelationshipsResponse
  extends ApiResponse<Relationship[]> {}

export interface IUpdateEntityRequest extends EntityUpdate {
  id: string;
}
export interface IUpdateEntityResponse extends ApiResponse<Entity> {}

export interface IDeleteEntityRequest {
  id: string;
}
export interface IDeleteEntityResponse extends ApiResponse<unknown> {}

export interface ICreateRelationshipRequest extends RelationshipCreate {}
export interface ICreateRelationshipResponse
  extends ApiResponse<Relationship> {}

export interface IExcuteQueryRequest extends CypherQuery {}
export interface IExcuteQueryResponse extends ApiResponse<unknown[]> {}

export interface IGetKnowledgeGraphStatsRequest {}
export interface IGetKnowledgeGraphStatsResponse extends ApiResponse<unknown> {}

export interface ICreateOrMergeEntityRequest extends EntityCreate {}
export interface ICreateOrMergeEntityResponse extends ApiResponse<Entity> {}
