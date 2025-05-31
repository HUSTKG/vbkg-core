import { api } from "../config/axios";
import {
  ILoginJsonRequest,
  ILoginJsonResponse,
  ILoginRequest,
  ILoginResponse,
  ILogoutRequest,
  ILogoutResponse,
} from "@vbkg/types";
import { IRegisterRequest, IRegisterResponse } from "@vbkg/types";
import { API_ENDPOINTS } from "@vbkg/utils";

const login = async (input: ILoginRequest): Promise<ILoginResponse> => {
  return await api()
    .post<ILoginResponse>(API_ENDPOINTS.LOGIN, input)
    .then((res) => res.data);
};

const loginJson = async (
  input: ILoginJsonRequest,
): Promise<ILoginJsonResponse> => {
  return await api()
    .post<ILoginJsonResponse>(API_ENDPOINTS.LOGIN_JSON, input)
    .then((res) => res.data);
};

const register = async (
  input: IRegisterRequest,
): Promise<IRegisterResponse> => {
  return await api()
    .post<IRegisterResponse>(API_ENDPOINTS.REGISTER, input)
    .then((res) => res.data);
};

const logout = async (input: ILogoutRequest): Promise<ILogoutResponse> => {
  return await api()
    .post<ILogoutResponse>(API_ENDPOINTS.LOGOUT, input)
    .then((res) => res.data);
};

export const AuthService = {
  login,
  loginJson,
  register,
  logout,
};
