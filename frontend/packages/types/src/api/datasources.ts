import { ApiResponse, DataSource, PaginatedResponse } from "../models";
import { DataSourceCreate, SourceType } from "../models/datasource";

export interface ICreateDatasourceRequest extends DataSourceCreate {}

export interface ICreateDatasourceResponse extends ApiResponse<DataSource> {}

export interface IGetDatasourceRequest {
  id: string;
}
export interface IGetDatasourceResponse extends ApiResponse<DataSource> {}

export interface IGetDatasourcesRequest {
  skip?: number;
  limit?: number;
  source_type?: SourceType;
  is_active?: boolean;
}

export interface IGetDatasourcesResponse
  extends PaginatedResponse<DataSource> {}

export interface IUpdateDatasourceRequest {
  id: string;
}
export interface IUpdateDatasourceResponse extends ApiResponse<DataSource> {}

export interface IDeleteDatasourceRequest {
  id: string;
}
export interface IDeleteDatasourceResponse extends ApiResponse<unknown> {}

export interface IGetPipelineTemplatesRequest {
  datasource_id: string;
}

export interface IGetPipelineTemplatesResponse extends ApiResponse<any> {}

export interface ICreatePipelineFromTemplateRequest {
  datasource_id: string;
  template_name: string;
  custom_options: Record<string, any>;
}

export interface ICreatePipelineFromTemplateResponse extends ApiResponse<any> {}
