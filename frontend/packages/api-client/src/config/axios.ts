import { getSession, setSession } from "@vbkg/utils";
import axios from "axios";
import { jwtDecode } from "jwt-decode";
import { getConfig } from "./apiConfig";

// Create API instance with current config
export const createApiInstance = () => {
  const config = getConfig();

  if (!config.baseUrl) {
    throw new Error("Base URL is required");
  }

  const defaultHeaders = {};

  // Merge default headers with user-defined headers
  config.headers = { ...defaultHeaders, ...config.headers };

  const api = axios.create({
    baseURL: config.baseUrl,
    headers: config.headers,
  });

  // Add auth token to requests
  api.interceptors.request.use(
    (config) => {
      const accessToken = getSession()?.session.accessToken;
      config.headers.Authorization = `Bearer ${accessToken}`;
      return config;
    },
    async (error) => {
      return Promise.reject(error);
    },
  );

  // Handle errors globally
  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;
      if (error.response?.status === 401) {
        const session = getSession();
        originalRequest._retry = true;
        try {
          if (session) {
            const token = session?.session.accessToken;
            const decodedToken = jwtDecode(token);
            const exp = Number(decodedToken?.exp) * 1000;
            if (Date.now() > exp) {
              // Token expired, redirect to login
              const response = await axios.post(
                config.baseUrl + "/auth/refresh-token",
                {
                  token: session?.session.refreshToken,
                },
              );
              setSession({
                session: {
                  accessToken: response.data.accessToken,
                  refreshToken: response.data.refreshToken,
                },
                user: session.user,
              });
              api.defaults.headers.common.Authorization = `Bearer ${response.data.accessToken}`;
              return api.request(originalRequest);
            }
          }
        } catch (error) {
          setSession(null);
          window.location.href = "/login";
          return Promise.reject(error);
        }
      }
    },
  );

  return api;
};

// Get a fresh instance with current config
export const api = () => createApiInstance();
