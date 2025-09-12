import axios from 'axios';

// Create axios instances for different backend services
const createApiClient = (baseURL: string) => {
  return axios.create({
    baseURL,
    headers: {
      'Content-Type': 'application/json',
    },
  });
};

// Main API client for the central MCP orchestrator
export const mainApi = createApiClient('http://localhost:8000/api');

// GitHub integration API client
export const githubApi = createApiClient('http://localhost:8005/api');

// File management API client
export const fileApi = createApiClient('http://localhost:8002/api');

// Communication API client
export const communicationApi = createApiClient('http://localhost:8003/api');

// System monitoring API client
export const systemApi = createApiClient('http://localhost:8004/api');

// Generic API request handler with error handling
export const apiRequest = async <T>(request: Promise<any>): Promise<T> => {
  try {
    const response = await request;
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.message || error.message;
      throw new Error(message);
    }
    throw error;
  }
};