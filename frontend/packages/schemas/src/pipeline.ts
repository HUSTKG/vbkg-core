import { PipelineType } from "@vbkg/types";
import { z } from "zod";

// Schema for retrieving pipelines with optional filters
export const ReadPipelinesSchema = z.object({
  skip: z.number().min(0).default(0), // Pagination offset
  limit: z.number().min(1).default(100), // Pagination limit
  pipeline_type: z.string().optional(), // Optional filter by pipeline type
  is_active: z.boolean().optional(), // Optional filter for active pipelines
});

// Schema for creating a pipeline
export const CreatePipelineSchema = z.object({
  name: z.string(), // Pipeline name
  description: z.string().optional(), // Optional description
  pipeline_type: z.nativeEnum(PipelineType), // Pipeline type
  schedule: z.string().optional(), // Optional schedule (CRON expression)
  is_active: z.boolean().default(true), // Default to active
});

// Schema for retrieving a specific pipeline by ID
export const ReadPipelineByIdSchema = z.object({
  pipeline_id: z.string().uuid(), // Pipeline ID must be a valid UUID
});

// Schema for updating a pipeline
export const UpdatePipelineSchema = z.object({
  pipeline_id: z.string().uuid(), // Pipeline ID must be a valid UUID
  name: z.string().optional(), // Optional name update
  description: z.string().optional(), // Optional description update
  step_type: z.string().optional(), // Optional type update
  config: z.record(z.string(), z.any()).optional(), // Optional configuration update
});

// Schema for deleting a pipeline
export const DeletePipelineSchema = z.object({
  pipeline_id: z.string().uuid(), // Pipeline ID must be a valid UUID
});

// Schema for running a pipeline
export const RunPipelineSchema = z.object({
  pipeline_id: z.string().uuid(), // Pipeline ID must be a valid UUID
  params: z.record(z.string(), z.any()).optional(), // Optional parameters for the pipeline run
});

// Schema for retrieving pipeline runs
export const ReadPipelineRunsSchema = z.object({
  skip: z.number().min(0).default(0), // Pagination offset
  limit: z.number().min(1).default(100), // Pagination limit
  pipeline_id: z.string().uuid().optional(), // Optional filter by pipeline ID
  status: z.string().optional(), // Optional filter by pipeline run status
});

// Schema for retrieving a specific pipeline run by ID
export const ReadPipelineRunByIdSchema = z.object({
  run_id: z.string().uuid(), // Pipeline run ID must be a valid UUID
});

// Schema for retrieving the status of a pipeline run
export const GetPipelineRunStatusSchema = z.object({
  run_id: z.string().uuid(), // Pipeline run ID must be a valid UUID
});

// Schema for cancelling a pipeline run
export const CancelPipelineRunSchema = z.object({
  run_id: z.string().uuid(), // Pipeline run ID must be a valid UUID
});
