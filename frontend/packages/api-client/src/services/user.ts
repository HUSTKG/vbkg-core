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
) => {
  return await api()
    .get<IGetUsersResponse>(API_ENDPOINTS.READ_USERS, {
      params: {
        ...input,
      },
    })
};

const getUser = async (input: IGetUserRequest) => {
  return await api()
    .get<IGetUserResponse>(API_ENDPOINTS.READ_USER(input.user_id))
};

const getUserMe = async () => {
  return await api()
    .get<IGetUserMeResponse>(API_ENDPOINTS.READ_USER_ME)
};

const updateUser = async (
  input: IUpdateUserRequest,
) => {
  return await api()
    .patch<IUpdateUserResponse>(
      API_ENDPOINTS.UPDATE_USER(input.user_id),
      input.data,
    )
};

const updateUserMe = async (
  input: IUpdateUserMeRequest,
) => {
  return await api()
    .patch<IUpdateUserMeResponse>(API_ENDPOINTS.UPDATE_USER_ME, input.data)
};

const deleteUser = async (
  input: IDeleteUserRequest,
) => {
  return await api()
    .delete<IDeleteUserResponse>(API_ENDPOINTS.DELETE_USER(input.user_id))
};

const getRoles = async () => {
  return await api()
    .get<IGetRolesResponse>(API_ENDPOINTS.READ_ROLES)
};

const getPermissions = async () => {
  return await api()
    .get<IGetPermissionsResponse>(API_ENDPOINTS.READ_PERMISSIONS)
};

const createAPIKey = async (
  input: ICreateAPIKeyRequest,
) => {
  return await api()
    .post<ICreateAPIKeyResponse>(API_ENDPOINTS.CREATE_API_KEY, null, {
      params: input,
    })
};

const getUserAPIKeys = async () => {
  return await api()
    .get<IGetAPIKeysResponse>(API_ENDPOINTS.READ_USER_API_KEYS)
};

const revokeAPIKey = async (
  input: IRevokeAPIKeyRequest,
) => {
  return await api()
    .delete<IRevokeAPIKeyResponse>(
      API_ENDPOINTS.REVOKE_API_KEY(input.api_key_id),
    )
};

const getUserActivity = async (
  input: IGetUserActivityRequest,
) => {
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
};

const assignRole = async (
  input: IAssignRoleRequest,
) => {
  return await api()
    .post<IAssignRoleResponse>(
      API_ENDPOINTS.ASSIGN_USER_ROLE(input.user_id, input.role_name),
    )
};

const removeRole = async (
  input: IRemoveRoleRequest,
) => {
  return await api()
    .delete<IRemoveRoleResponse>(
      API_ENDPOINTS.REMOVE_USER_ROLE(input.user_id, input.role_name),
    )
};

const getSystemStats = async () => {
  return await api()
    .get<IGetSystemStatsResponse>(API_ENDPOINTS.ADMIN_SYSTEM_STATS)
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
