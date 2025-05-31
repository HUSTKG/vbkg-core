import { z } from "zod";

// Schema for paginated user retrieval
export const ReadUsersSchema = z.object({
  skip: z.number().min(0).default(0), // Pagination offset
  limit: z.number().min(1).default(100), // Pagination limit
});

// Schema for current user retrieval (no input parameters)
export const ReadCurrentUserSchema = z.object({});

// Schema for updating current user
export const UpdateCurrentUserSchema = z.object({
  name: z.string().optional(), // Optional name update
  email: z.string().email().optional(), // Optional email update
  roles: z.array(z.string()).optional(), // Optional roles update, restricted by the endpoint logic
});

// Schema for retrieving a specific user by ID
export const ReadUserByIdSchema = z.object({
  user_id: z.string().uuid(), // User ID must be a valid UUID
});

// Schema for updating a specific user
export const UpdateUserSchema = z.object({
  user_id: z.string().uuid(), // User ID must be a valid UUID
  name: z.string().optional(), // Optional name update
  email: z.string().email().optional(), // Optional email update
  roles: z.array(z.string()).optional(), // Optional roles update
});

// Schema for deleting a specific user
export const DeleteUserSchema = z.object({
  user_id: z.string().uuid(), // User ID must be a valid UUID
});

// Schema for retrieving roles (no input parameters)
export const ReadRolesSchema = z.object({});

// Schema for retrieving permissions (no input parameters)
export const ReadPermissionsSchema = z.object({});
