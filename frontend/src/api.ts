import axios, { type InternalAxiosRequestConfig } from "axios";

type RetriableRequest = InternalAxiosRequestConfig & { authRetried?: boolean };

let refreshRequest: Promise<void> | null = null;

export const api = axios.create({
  baseURL: "/api",
  timeout: 10_000,
  withCredentials: true,
  xsrfCookieName: "threadflow_csrftoken",
  xsrfHeaderName: "X-CSRFToken",
});

api.interceptors.response.use(undefined, async (error: unknown) => {
  if (!axios.isAxiosError(error)) return Promise.reject(error);
  const request = error.config as RetriableRequest | undefined;
  const isAuthEndpoint = request?.url?.startsWith("/auth/") ?? false;
  if (error.response?.status !== 401 || !request || request.authRetried || isAuthEndpoint) {
    return Promise.reject(error);
  }

  request.authRetried = true;
  refreshRequest ??= api.post("/auth/refresh").then(() => undefined);
  try {
    await refreshRequest;
    return api.request(request);
  } finally {
    refreshRequest = null;
  }
});
