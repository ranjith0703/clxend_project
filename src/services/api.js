import axios from "axios";

// =======================================
// FASTAPI BACKEND URL
// =======================================
const BASE_URL = "http://localhost:8000";
console.log("BASE URL:", BASE_URL);

// =======================================
// AXIOS INSTANCE
// =======================================
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// =======================================
// REQUEST INTERCEPTOR
// =======================================
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// =======================================
// RESPONSE INTERCEPTOR
// =======================================
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }

    return Promise.reject(error);
  }
);

// =======================================
// API METHODS
// =======================================
export const getRequest = async (url, params = {}) => {
  const response = await api.get(url, { params });
  return response.data;
};

export const postRequest = async (url, data = {}) => {
  const response = await api.post(url, data);
  return response.data;
};

export const putRequest = async (url, data = {}) => {
  const response = await api.put(url, data);
  return response.data;
};

export const deleteRequest = async (url) => {
  const response = await api.delete(url);
  return response.data;
};

export default api;