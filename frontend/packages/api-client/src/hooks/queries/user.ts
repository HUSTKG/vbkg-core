import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import {
  IGetUsersRequest,
  IGetUsersResponse,
  IGetUserRequest,
  IGetUserResponse,
  IGetUserMeResponse,
  IGetRolesResponse,
  IGetPermissionsResponse,
  IGetAPIKeysResponse,
  IGetUserActivityRequest,
  IGetUserActivityResponse,
  IGetSystemStatsResponse,
} from "@vbkg/types";
import { QueryKeys } from "../../config/queryKeys";
import { UserService } from "../../services/user";

// Fetch all users with pagination and filters
export const useUsers = (
  input: IGetUsersRequest = {},
  options?: Partial<UseQueryOptions<IGetUsersResponse, Error>>,
) => {
  return useQuery<IGetUsersResponse, Error>({
    queryKey: QueryKeys.users.list(input),
    queryFn: () => UserService.getUsers(input),
    ...options,
  });
};

// Fetch specific user
export const useUser = (
  input: IGetUserRequest,
  options?: Partial<UseQueryOptions<IGetUserResponse, Error>>,
) => {
  return useQuery<IGetUserResponse, Error>({
    queryKey: QueryKeys.users.detail(input.user_id),
    queryFn: () => UserService.getUser(input),
    enabled: !!input.user_id,
    ...options,
  });
};

// Fetch current user
export const useUserMe = (
  options?: UseQueryOptions<IGetUserMeResponse, Error>,
) => {
  return useQuery<IGetUserMeResponse, Error>({
    queryKey: QueryKeys.users.me(),
    queryFn: () => UserService.getUserMe(),
    ...options,
  });
};

// Fetch all roles
export const useRoles = (
  options?: UseQueryOptions<IGetRolesResponse, Error>,
) => {
  return useQuery<IGetRolesResponse, Error>({
    queryKey: QueryKeys.users.roles(),
    queryFn: () => UserService.getRoles(),
    staleTime: 5 * 60 * 1000, // 5 minutes - roles don't change often
    ...options,
  });
};

// Fetch all permissions
export const usePermissions = (
  options?: UseQueryOptions<IGetPermissionsResponse, Error>,
) => {
  return useQuery<IGetPermissionsResponse, Error>({
    queryKey: QueryKeys.users.permissions(),
    queryFn: () => UserService.getPermissions(),
    staleTime: 5 * 60 * 1000, // 5 minutes - permissions don't change often
    ...options,
  });
};

// Fetch user's API keys
export const useUserAPIKeys = (
  options?: UseQueryOptions<IGetAPIKeysResponse, Error>,
) => {
  return useQuery<IGetAPIKeysResponse, Error>({
    queryKey: QueryKeys.users.apiKeys(),
    queryFn: () => UserService.getUserAPIKeys(),
    ...options,
  });
};

// Fetch user activity (current user)
export const useMyActivity = (
  input: IGetUserActivityRequest = { limit: 50 },
  options?: UseQueryOptions<IGetUserActivityResponse, Error>,
) => {
  return useQuery<IGetUserActivityResponse, Error>({
    queryKey: QueryKeys.users.activity.my(input),
    queryFn: () => UserService.getUserActivity(input),
    ...options,
  });
};

// Fetch specific user activity
export const useUserActivity = (
  input: IGetUserActivityRequest,
  options?: Partial<UseQueryOptions<IGetUserActivityResponse, Error>>,
) => {
  return useQuery<IGetUserActivityResponse, Error>({
    queryKey: QueryKeys.users.activity.user(input.user_id!, input),
    queryFn: () => UserService.getUserActivity(input),
    enabled: !!input.user_id,
    ...options,
  });
};

// Fetch system statistics (admin only)
export const useSystemStats = (
  options?: Partial<UseQueryOptions<IGetSystemStatsResponse, Error>>,
) => {
  return useQuery<IGetSystemStatsResponse, Error>({
    queryKey: QueryKeys.users.stats(),
    queryFn: () => UserService.getSystemStats(),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    ...options,
  });
};
