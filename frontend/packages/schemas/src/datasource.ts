import { SourceType } from "@vbkg/types";
import { z } from "zod";
import { jsonSchema } from "./common";

const ConnectionDetailsSchema = z.object({
  name: z.string().min(1), // Name must be a non-empty string
  description: z.string().optional(), // Description is optional
  credentials: z
    .array(
      z.object({
        key: z.string().min(1), // Key must be a non-empty string
        value: z.string().min(1), // Value must be a non-empty string
      }),
    )
    .optional(), // Credentials are optional
});

const _FileConnectionDetailsSchema = z
  .object({
    source_type: z.literal(SourceType.FILE), // Type must be "file"
    connection_details: z.object({
      file_path: z.string(), // File path must be a string
      file_format: z
        .string()
        .describe("Format of the file (e.g., csv, json, txt, pdf)"),
      encoding: z.string().optional(), // Optional encoding for the file
      delimiter: z.string().optional(), // Optional delimiter for the file
    }),
  })
  .extend(ConnectionDetailsSchema.shape); // Extend the base connection details schema

const _DatabaseConnectionDetailsSchema = z
  .object({
    source_type: z.literal(SourceType.DATABASE), // Type must be "database"
    connection_details: z.object({
      host: z.string(), // Host must be a string
      port: z.number().int(), // Port must be an integer
      database: z.string(), // Database name must be a string
      username: z.string(), // Username must be a string
      password: z.string().optional(), // Optional password for the database
      db_type: z.enum(["postgres", "mysql", "mssql"]), // Database type must be one of the specified enums
      ssl: z.boolean().default(false), // SSL connection option, default is false
      query: z.string().optional(), // Optional SQL query to execute
      table: z.string().optional(), // Optional table name to connect to
    }),
  })
  .extend(ConnectionDetailsSchema.shape); // Extend the base connection details schema

const _ApiConnectionDetailsSchema = z
  .object({
    source_type: z.literal(SourceType.API), // Type must be "api"
    connection_details: z.object({
      url: z.string().url(), // URL must be a valid URL
      method: z.enum(["GET", "POST", "PUT", "DELETE"]), // HTTP method must be one of the specified
      headers: z.record(z.string()).optional(), // Optional headers for the API request
      query_params: z.record(z.string()).optional(), // Optional query parameters for the API request
      body: jsonSchema.optional(), // Optional body for the API request
      auth_type: z.enum(["BASIC", "BEARER"]).optional(), // Optional authentication type
      auth_config: z.record(z.any()).optional(), // Optional authentication configuration
    }),
  })
  .extend(ConnectionDetailsSchema.shape); // Extend the base connection details schema

const _URLConnectionDetailsSchema = z
  .object({
    source_type: z.literal(SourceType.URL), // Type must be "url"
    connection_details: z.object({
      url: z.string().url(), // URL must be a valid URL
      scrape_config: z.record(z.any()).optional(), // Optional scraping configuration
      headers: z.record(z.string()).optional(), // Optional headers for the URL request
    }),
  })
  .extend(ConnectionDetailsSchema.shape); // Extend the base connection details schema

// Schema for creating a data source
export const CreateDataSourceSchema = z.discriminatedUnion("source_type", [
  _FileConnectionDetailsSchema,
  _DatabaseConnectionDetailsSchema,
  _ApiConnectionDetailsSchema,
  _URLConnectionDetailsSchema,
]);

// Schema for updating a data source
export const UpdateDataSourceSchema = z.object({
  name: z.string().min(1).optional(), // Name can be updated or omitted
  config: z.record(z.string(), z.any()).optional(), // Config can be updated or omitted
});

// Schema for reading data sources with optional filters
export const ReadDataSourcesSchema = z.object({
  skip: z.number().min(0).default(0), // Pagination offset
  limit: z.number().min(1).default(100), // Pagination limit
  source_type: z.string().optional(), // Optional filter for source type
  is_active: z.boolean().optional(), // Optional filter for active status
});

// Schema for retrieving a specific data source by ID
export const ReadDataSourceByIdSchema = z.object({
  datasource_id: z.string().uuid(), // ID must be a valid UUID
});

// Schema for file upload metadata
export const FileUploadMetadataSchema = z.object({
  metadata: z.string().optional(), // Optional JSON metadata as a string
});

// Schema for updating file status
export const UpdateFileStatusSchema = z.object({
  status: z.enum(["PENDING", "PROCESSING", "COMPLETED", "FAILED"]), // Example enum for file status
  processed: z.boolean().optional(), // Indicates if the file is processed
  error_message: z.string().optional(), // Optional error message
});

// Schema for retrieving file uploads with optional filters
export const ReadFileUploadsSchema = z.object({
  datasource_id: z.string().uuid().optional(), // Optional filter by datasource ID
  status: z.enum(["PENDING", "PROCESSING", "COMPLETED", "FAILED"]).optional(), // Optional filter for file status
  processed: z.boolean().optional(), // Optional filter for processed files
  skip: z.number().min(0).default(0), // Pagination offset
  limit: z.number().min(1).default(100), // Pagination limit
});

// Schema for retrieving a specific file upload by ID
export const ReadFileUploadByIdSchema = z.object({
  file_id: z.string().uuid(), // ID must be a valid UUID
});

// Schema for deleting a file upload
export const DeleteFileUploadSchema = z.object({
  file_id: z.string().uuid(), // ID must be a valid UUID
});

// Schema for retrieving file content
export const GetFileContentSchema = z.object({
  file_id: z.string().uuid(), // ID must be a valid UUID
});
