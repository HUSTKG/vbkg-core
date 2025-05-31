import {
  useMutation,
  UseMutationOptions,
  useQueryClient,
} from "@tanstack/react-query";
import {
  IUpdateUserRequest,
  IUpdateUserResponse,
  IUpdateUserMeRequest,
  IUpdateUserMeResponse,
  IDeleteUserRequest,
  IDeleteUserResponse,
  ICreateAPIKeyRequest,
  ICreateAPIKeyResponse,
  IRevokeAPIKeyRequest,
  IRevokeAPIKeyResponse,
  IAssignRoleRequest,
  IAssignRoleResponse,
  IRemoveRoleRequest,
  IRemoveRoleResponse,
} from "@vbkg/types";
import { UserService } from "../../services/user";
import { QueryKeys } from "../../config/queryKeys";

// Update user
export const useUpdateUser = (
  options?: UseMutationOptions<IUpdateUserResponse, Error, IUpdateUserRequest>,
) => {
  const queryClient = useQueryClient();
  return useMutation<IUpdateUserResponse, Error, IUpdateUserRequest>({
    mutationFn: UserService.updateUser,
    ...options,
    onSuccess: (data, variables, ...rest) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: QueryKeys.users.lists() });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.users.detail(variables.user_id),
      });
      options?.onSuccess?.(data, variables, ...rest);
    },
  });
};

// Update current user
export const useUpdateUserMe = (
  options?: UseMutationOptions<
    IUpdateUserMeResponse,
    Error,
    IUpdateUserMeRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<IUpdateUserMeResponse, Error, IUpdateUserMeRequest>({
    mutationFn: UserService.updateUserMe,
    ...options,
    onSuccess: (...params) => {
      // Invalidate current user query
      queryClient.invalidateQueries({ queryKey: QueryKeys.users.me() });
      options?.onSuccess?.(...params);
    },
  });
};

// Delete user
export const useDeleteUser = (
  options?: UseMutationOptions<IDeleteUserResponse, Error, IDeleteUserRequest>,
) => {
  const queryClient = useQueryClient();
  return useMutation<IDeleteUserResponse, Error, IDeleteUserRequest>({
    mutationFn: UserService.deleteUser,
    ...options,
    onSuccess: (data, variables, ...rest) => {
      // Invalidate users list
      queryClient.invalidateQueries({ queryKey: QueryKeys.users.lists() });
      // Remove specific user from cache
      queryClient.removeQueries({
        queryKey: QueryKeys.users.detail(variables.user_id),
      });
      options?.onSuccess?.(data, variables, ...rest);
    },
  });
};

// Create API key
export const useCreateAPIKey = (
  options?: UseMutationOptions<
    ICreateAPIKeyResponse,
    Error,
    ICreateAPIKeyRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<ICreateAPIKeyResponse, Error, ICreateAPIKeyRequest>({
    mutationFn: UserService.createAPIKey,
    ...options,
    onSuccess: (...params) => {
      // Invalidate API keys query
      queryClient.invalidateQueries({ queryKey: QueryKeys.users.apiKeys() });
      options?.onSuccess?.(...params);
    },
  });
};

// Revoke API key
export const useRevokeAPIKey = (
  options?: UseMutationOptions<
    IRevokeAPIKeyResponse,
    Error,
    IRevokeAPIKeyRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<IRevokeAPIKeyResponse, Error, IRevokeAPIKeyRequest>({
    mutationFn: UserService.revokeAPIKey,
    ...options,
    onSuccess: (...params) => {
      // Invalidate API keys query
      queryClient.invalidateQueries({ queryKey: QueryKeys.users.apiKeys() });
      options?.onSuccess?.(...params);
    },
  });
};

// Assign role to user
export const useAssignRole = (
  options?: UseMutationOptions<IAssignRoleResponse, Error, IAssignRoleRequest>,
) => {
  const queryClient = useQueryClient();
  return useMutation<IAssignRoleResponse, Error, IAssignRoleRequest>({
    mutationFn: UserService.assignRole,
    ...options,
    onSuccess: (data, variables, ...rest) => {
      // Invalidate user queries to refresh roles
      queryClient.invalidateQueries({ queryKey: QueryKeys.users.lists() });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.users.detail(variables.user_id),
      });
      queryClient.invalidateQueries({ queryKey: QueryKeys.users.stats() });
      options?.onSuccess?.(data, variables, ...rest);
    },
  });
};

// Remove role from user
export const useRemoveRole = (
  options?: UseMutationOptions<IRemoveRoleResponse, Error, IRemoveRoleRequest>,
) => {
  const queryClient = useQueryClient();
  return useMutation<IRemoveRoleResponse, Error, IRemoveRoleRequest>({
    mutationFn: UserService.removeRole,
    ...options,
    onSuccess: (data, variables, ...rest) => {
      // Invalidate user queries to refresh roles
      queryClient.invalidateQueries({ queryKey: QueryKeys.users.lists() });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.users.detail(variables.user_id),
      });
      queryClient.invalidateQueries({ queryKey: QueryKeys.users.stats() });
      options?.onSuccess?.(data, variables, ...rest);
    },
  });
};
