import axios, { AxiosInstance } from "axios";
import { API_BASE_URL } from "../utils/constants";
import { authService } from "./authService";

class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    /** ------------------------------------
     *  REQUEST INTERCEPTOR (FIXED)
     * -------------------------------------
     */
    this.client.interceptors.request.use(
      (config) => {
        const token = authService.getToken();

        if (token) {
          config.headers = {
            ...config.headers,
            Authorization: `Bearer ${token}`,   // FIX UTAMA
          };
        }

        return config;
      },
      (error) => Promise.reject(error)
    );

    /** ------------------------------------
     *  RESPONSE INTERCEPTOR
     * -------------------------------------
     */
    this.client.interceptors.response.use(
      (response) => response.data,
      (error) => {
        const status = error.response?.status;

        // Redirect hanya untuk 401 (token expired)
        if (status === 401) {
          authService.clearAuth();
          window.location.href = "/login";
        }

        return Promise.reject(error.response?.data || error);
      }
    );
  }

  /** Simple HTTP wrapper */
  public get(url: string, config?: any) {
    return this.client.get(url, config);
  }

  public post(url: string, data?: any, config?: any) {
    return this.client.post(url, data, config);
  }

  public put(url: string, data?: any, config?: any) {
    return this.client.put(url, data, config);
  }

  public delete(url: string, config?: any) {
    return this.client.delete(url, config);
  }
}

export default new ApiClient(API_BASE_URL);
