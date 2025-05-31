import { z } from "zod";

// Schema for creating a visualization
export const CreateVisualizationSchema = z.object({
  name: z.string().min(1), // Visualization name is required
  description: z.string().optional(), // Optional description
  entity_id: z.string().uuid().optional(), // Optional entity ID
  is_public: z.boolean().default(false), // Public or private flag
  config: z.record(z.string(), z.any()), // Configuration object for the visualization
});

// Schema for retrieving visualizations with optional filters
export const ReadVisualizationsSchema = z.object({
  type: z.string().optional(), // Optional filter by visualization type
  is_public: z.boolean().optional(), // Optional filter for public visualizations
  limit: z.number().min(1).max(1000).default(100), // Pagination limit
  skip: z.number().min(0).default(0), // Pagination offset
});

// Schema for retrieving a specific visualization by ID
export const ReadVisualizationByIdSchema = z.object({
  visualization_id: z.string().uuid(), // Visualization ID must be a valid UUID
});

// Schema for updating a visualization
export const UpdateVisualizationSchema = z.object({
  visualization_id: z.string().uuid(), // Visualization ID must be a valid UUID
  name: z.string().optional(), // Optional name update
  description: z.string().optional(), // Optional description update
  is_public: z.boolean().optional(), // Optional public/private flag update
  config: z.record(z.string(), z.any()).optional(), // Optional configuration update
});

// Schema for deleting a visualization
export const DeleteVisualizationSchema = z.object({
  visualization_id: z.string().uuid(), // Visualization ID must be a valid UUID
});

// Schema for retrieving data for a visualization
export const GetVisualizationDataSchema = z.object({
  visualization_id: z.string().uuid(), // Visualization ID must be a valid UUID
  params: z.record(z.string(), z.string()).optional(), // Query parameters as key-value pairs
});

// Schema for creating a default visualization
export const CreateDefaultVisualizationSchema = z.object({
  title: z.string().optional(), // Optional title
  description: z.string().optional(), // Optional description
  entity_id: z.string().uuid(), // Entity ID is required
  is_public: z.boolean().default(false), // Public or private flag
  visualization_type: z.enum(["GRAPH", "TREE", "TABLE", "CHART"]), // Must be one of the predefined visualization types
});

// Schema for retrieving visualization templates
export const GetVisualizationTemplatesSchema = z.object({});
