export enum SourceType {
  FILE = "file",
  API = "api",
  DATABASE = "database",
  URL = "url",
}

export type FileFormat = "csv" | "json" | "xlsx" | "txt" | "pdf";
export type ApiMethod = "GET" | "POST" | "PUT" | "DELETE";
export type DatabaseType = "postgres" | "mysql" | "mssql" | "oracle" | "sqlite";

export interface ConnectionConfig {
  // Base model for connection details that will be extended by specific source types
}

export interface FileConnectionConfig extends ConnectionConfig {
  file_path?: string;
  file_format?: string; // Format of the file (e.g., csv, json, txt, pdf)
  encoding?: string;
  delimiter?: string; // For CSV files
}

export interface ApiConnectionConfig extends ConnectionConfig {
  url: string;
  method?: string;
  headers?: Record<string, string>;
  query_params?: Record<string, any>;
  body?: Record<string, any>;
  auth_type?: string;
  auth_config?: Record<string, any>;
}

export interface DatabaseConnectionConfig extends ConnectionConfig {
  host: string;
  port: number;
  database: string;
  username: string;
  password?: string;
  db_type: string; // Type of database (e.g., postgres, mysql, mssql)
  ssl?: boolean;
  query?: string;
  table?: string;
}

export interface UrlConnectionConfig extends ConnectionConfig {
  url: string;
  scrape_config?: Record<string, any>;
  headers?: Record<string, string>;
}

export interface DataSourceBase {
  name: string;
  description?: string;
  source_type: SourceType;
  connection_details: Record<string, any>; // Connection details specific to the source type
  credentials?: Record<string, any>;
}

export interface DataSourceCreate extends DataSourceBase {}

export interface DataSourceUpdate {
  name?: string;
  description?: string;
  connection_details?: Record<string, any>;
  credentials?: Record<string, any>;
  is_active?: boolean;
}

export interface DataSource extends DataSourceBase {
  id: string;
  is_active: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}
