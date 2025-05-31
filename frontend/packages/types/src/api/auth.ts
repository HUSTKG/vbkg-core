import { ApiResponse, Token, User, UserCreate } from "../models";

export interface ILoginRequest {
  email: string;
  password: string;
}

export interface ILoginResponse {}

export interface ILoginJsonRequest {
  email: string;
  password: string;
}

export interface ILoginJsonResponse
  extends ApiResponse<{
    session: Token;
    user: {
      email: string;
      id: string;
      full_name: string;
      is_active: boolean;
      roles: string[];
    };
  }> {}

export interface IRegisterRequest extends UserCreate {}

export interface IRegisterResponse extends ApiResponse<User> {}

export type ILogoutRequest = void;

export interface ILogoutResponse extends ApiResponse<null> {}
