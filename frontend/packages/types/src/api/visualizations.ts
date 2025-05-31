import { ApiResponse, PaginatedResponse } from "../models";
import {
  DefaultVisualizationRequest,
  Visualization,
  VisualizationCreate,
  VisualizationType,
  VisualizationUpdate,
} from "../models/visualization";

export interface ICreateVisualizationRequest extends VisualizationCreate {}
export interface ICreateVisualizationResponse
  extends ApiResponse<Visualization> {}

export interface IReadVisualizationsRequest {
  type?: VisualizationType;
  is_public?: boolean;
  limit?: number;
  skip?: number;
}
export interface IReadVisualizationsResponse
  extends PaginatedResponse<Visualization> {}

export interface IReadPublicVisualizationsRequest {
  type?: VisualizationType;
  limit?: number;
  skip?: number;
}
export interface IReadPublicVisualizationsResponse
  extends PaginatedResponse<Visualization> {}

export interface IReadVisualizationRequest {
  id: string;
}
export interface IReadVisualizationResponse
  extends ApiResponse<Visualization> {}

export interface IUpdateVisualizationRequest extends VisualizationUpdate {
  id: string;
}
export interface IUpdateVisualizationResponse
  extends ApiResponse<Visualization> {}

export interface IDeleteVisualizationRequest {
  id: string;
}
export interface IDeleteVisualizationResponse extends ApiResponse<unknown> {}

export interface IGetVisualizationDataRequest extends Record<string, string> {
  id: string;
}
export interface IGetVisualizationDataResponse extends ApiResponse<unknown> {}

export interface ICreateDefaultVisualizationRequest
  extends DefaultVisualizationRequest {}
export interface ICreateDefaultVisualizationResponse
  extends ApiResponse<Visualization> {}

export interface IGetVisualizationTemplatesRequest {}
export interface IGetVisualizationTemplatesResponse
  extends ApiResponse<unknown[]> {}
