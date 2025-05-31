import {
  APIKey,
  APIKeyCreate,
  ApiResponse,
  PaginatedResponse,
  Permission,
  Role,
  SystemStats,
  User,
  UserActivity,
  UserUpdate,
} from "../models";

// Request Types
export interface IGetUsersRequest {
  skip?: number;
  limit?: number;
  role_filter?: string;
  department_filter?: string;
}

export interface IGetUserRequest {
  user_id: string;
}

export interface IUpdateUserRequest {
  user_id: string;
  data: UserUpdate;
}

export interface IDeleteUserRequest {
  user_id: string;
}

export interface IUpdateUserMeRequest {
  data: UserUpdate;
}

export interface ICreateAPIKeyRequest extends APIKeyCreate {}

export interface IGetUserActivityRequest {
  user_id?: string; // If not provided, gets current user's activity
  limit?: number;
  skip?: number;
  action_filter?: string;
}

export interface IAssignRoleRequest {
  user_id: string;
  role_name: string;
}

export interface IRemoveRoleRequest {
  user_id: string;
  role_name: string;
}

export interface IRevokeAPIKeyRequest {
  api_key_id: string;
}

// Response Types
export interface IGetUsersResponse extends PaginatedResponse<User> {}

export interface IGetUserResponse extends ApiResponse<User> {}

export interface IGetUserMeResponse extends ApiResponse<User> {}

export interface IUpdateUserResponse extends ApiResponse<User> {}

export interface IUpdateUserMeResponse extends ApiResponse<User> {}

export interface IDeleteUserResponse extends ApiResponse<{ message: string }> {}

export interface IGetRolesResponse extends ApiResponse<Role[]> {}

export interface IGetPermissionsResponse extends ApiResponse<Permission[]> {}

export interface ICreateAPIKeyResponse extends ApiResponse<APIKey> {}

export interface IGetAPIKeysResponse extends ApiResponse<APIKey[]> {}

export interface IRevokeAPIKeyResponse
  extends ApiResponse<{ message: string }> {}

export interface IGetUserActivityResponse extends ApiResponse<UserActivity[]> {}

export interface IAssignRoleResponse extends ApiResponse<{ message: string }> {}

export interface IRemoveRoleResponse extends ApiResponse<{ message: string }> {}

export interface IGetSystemStatsResponse extends ApiResponse<SystemStats> {}
