interface InitializeApiProps {
  baseUrl: string;
  bearerToken?: string;
  headers?: Record<string, string>;
}

let config: {
  baseUrl: string;
  bearerToken?: string;
  headers: Record<string, string>;
} = {
  baseUrl: "",
  headers: {},
};

export const initializeApi = (userConfig: InitializeApiProps): void => {
  if (!userConfig?.baseUrl) {
    throw new Error("Base URL is required");
  }

  config = {
    ...config,
    ...userConfig,
  };
};

export const getConfig = () => {
  return config;
};
