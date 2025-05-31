import {
  IGetUsersRequest,
  IGetUsersResponse,
  IGetUserRequest,
  IGetUserResponse,
  IGetUserMeResponse,
  IUpdateUserRequest,
  IUpdateUserResponse,
  IUpdateUserMeRequest,
  IUpdateUserMeResponse,
  IDeleteUserRequest,
  IDeleteUserResponse,
  IGetRolesResponse,
  IGetPermissionsResponse,
  ICreateAPIKeyRequest,
  ICreateAPIKeyResponse,
  IGetAPIKeysResponse,
  IRevokeAPIKeyRequest,
  IRevokeAPIKeyResponse,
  IGetUserActivityRequest,
  IGetUserActivityResponse,
  IAssignRoleRequest,
  IAssignRoleResponse,
  IRemoveRoleRequest,
  IRemoveRoleResponse,
  IGetSystemStatsResponse,
} from "@vbkg/types";

import { API_ENDPOINTS } from "@vbkg/utils";
import { api } from "../config/axios";

const getUsers = async (
  input: IGetUsersRequest,
): Promise<IGetUsersResponse> => {
  return await api()
    .get<IGetUsersResponse>(API_ENDPOINTS.READ_USERS, {
      params: {
        ...input,
      },
    })
    .then((res) => res.data);
};

const getUser = async (input: IGetUserRequest): Promise<IGetUserResponse> => {
  return await api()
    .get<IGetUserResponse>(API_ENDPOINTS.READ_USER(input.user_id))
    .then((res) => res.data);
};

const getUserMe = async (): Promise<IGetUserMeResponse> => {
  return await api()
    .get<IGetUserMeResponse>(API_ENDPOINTS.READ_USER_ME)
    .then((res) => res.data);
};

const updateUser = async (
  input: IUpdateUserRequest,
): Promise<IUpdateUserResponse> => {
  return await api()
    .patch<IUpdateUserResponse>(
      API_ENDPOINTS.UPDATE_USER(input.user_id),
      input.data,
    )
    .then((res) => res.data);
};

const updateUserMe = async (
  input: IUpdateUserMeRequest,
): Promise<IUpdateUserMeResponse> => {
  return await api()
    .patch<IUpdateUserMeResponse>(API_ENDPOINTS.UPDATE_USER_ME, input.data)
    .then((res) => res.data);
};

const deleteUser = async (
  input: IDeleteUserRequest,
): Promise<IDeleteUserResponse> => {
  return await api()
    .delete<IDeleteUserResponse>(API_ENDPOINTS.DELETE_USER(input.user_id))
    .then((res) => res.data);
};

const getRoles = async (): Promise<IGetRolesResponse> => {
  return await api()
    .get<IGetRolesResponse>(API_ENDPOINTS.READ_ROLES)
    .then((res) => res.data);
};

const getPermissions = async (): Promise<IGetPermissionsResponse> => {
  return await api()
    .get<IGetPermissionsResponse>(API_ENDPOINTS.READ_PERMISSIONS)
    .then((res) => res.data);
};

const createAPIKey = async (
  input: ICreateAPIKeyRequest,
): Promise<ICreateAPIKeyResponse> => {
  return await api()
    .post<ICreateAPIKeyResponse>(API_ENDPOINTS.CREATE_API_KEY, null, {
      params: input,
    })
    .then((res) => res.data);
};

const getUserAPIKeys = async (): Promise<IGetAPIKeysResponse> => {
  return await api()
    .get<IGetAPIKeysResponse>(API_ENDPOINTS.READ_USER_API_KEYS)
    .then((res) => res.data);
};

const revokeAPIKey = async (
  input: IRevokeAPIKeyRequest,
): Promise<IRevokeAPIKeyResponse> => {
  return await api()
    .delete<IRevokeAPIKeyResponse>(
      API_ENDPOINTS.REVOKE_API_KEY(input.api_key_id),
    )
    .then((res) => res.data);
};

const getUserActivity = async (
  input: IGetUserActivityRequest,
): Promise<IGetUserActivityResponse> => {
  const endpoint = input.user_id
    ? API_ENDPOINTS.READ_USER_ACTIVITY(input.user_id)
    : API_ENDPOINTS.READ_MY_ACTIVITY;

  return await api()
    .get<IGetUserActivityResponse>(endpoint, {
      params: {
        limit: input.limit,
        skip: input.skip,
        action_filter: input.action_filter,
      },
    })
    .then((res) => res.data);
};

const assignRole = async (
  input: IAssignRoleRequest,
): Promise<IAssignRoleResponse> => {
  return await api()
    .post<IAssignRoleResponse>(
      API_ENDPOINTS.ASSIGN_USER_ROLE(input.user_id, input.role_name),
    )
    .then((res) => res.data);
};

const removeRole = async (
  input: IRemoveRoleRequest,
): Promise<IRemoveRoleResponse> => {
  return await api()
    .delete<IRemoveRoleResponse>(
      API_ENDPOINTS.REMOVE_USER_ROLE(input.user_id, input.role_name),
    )
    .then((res) => res.data);
};

const getSystemStats = async (): Promise<IGetSystemStatsResponse> => {
  return await api()
    .get<IGetSystemStatsResponse>(API_ENDPOINTS.ADMIN_SYSTEM_STATS)
    .then((res) => res.data);
};

export const UserService = {
  getUsers,
  getUser,
  getUserMe,
  updateUser,
  updateUserMe,
  deleteUser,
  getRoles,
  getPermissions,
  createAPIKey,
  getUserAPIKeys,
  revokeAPIKey,
  getUserActivity,
  assignRole,
  removeRole,
  getSystemStats,
};
