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
	return await api().post<ILoginResponse>(API_ENDPOINTS.LOGIN, input);
};

const loginJson = async (input: ILoginJsonRequest) => {
	return await api().post<ILoginJsonResponse>(API_ENDPOINTS.LOGIN_JSON, input);
};

const register = async (input: IRegisterRequest) => {
	return await api().post<IRegisterResponse>(API_ENDPOINTS.REGISTER, input);
};

const logout = async (input: ILogoutRequest) => {
	return await api().post<ILogoutResponse>(API_ENDPOINTS.LOGOUT, input);
};

export const AuthService = {
	login,
	loginJson,
	register,
	logout,
};
