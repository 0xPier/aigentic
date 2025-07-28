import axios from 'axios';

// Base API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  withCredentials: true
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await api.post('/auth/refresh', {
            refresh_token: refreshToken
          });
          
          const { access_token, refresh_token: new_refresh_token, expires_in } = response.data;
          localStorage.setItem('token', access_token);
          localStorage.setItem('refresh_token', new_refresh_token);
          localStorage.setItem('token_expires_at', Date.now() + (expires_in * 1000));
          
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          localStorage.removeItem('token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('token_expires_at');
          window.location.href = '/login';
        }
      } else {
        // No refresh token, redirect to login
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    }
    
    // Handle subscription required errors
    if (error.response?.status === 402) {
      // Payment required - show upgrade modal or redirect
      console.warn('Subscription upgrade required:', error.response.data.detail);
    }
    
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login-json', credentials),
  register: (userData) => api.post('/auth/register', userData),
  refreshToken: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/users/me'),
};

// Admin API
export const adminAPI = {
  createUser: (userData) => api.post('/admin/create-user', userData),
  getUsers: (params = {}) => api.get('/admin/users/', { params }),
  demoLogin: () => api.post('/admin/demo-login'),
  devLogin: () => api.post('/admin/dev-login'),
};

// Users API
export const usersAPI = {
  getDashboardStats: () => api.get('/users/dashboard'),
  updateProfile: (data) => api.put('/users/me', data),
};

// Tasks API
export const tasksAPI = {
  getTasks: (params = {}) => api.get('/tasks', { params }),
  getTask: (taskId) => api.get(`/tasks/${taskId}`),
  createTask: (taskData) => api.post('/tasks', taskData),
  updateTask: (taskId, taskData) => api.put(`/tasks/${taskId}`, taskData),
  deleteTask: (taskId) => api.delete(`/tasks/${taskId}`),
  executeAgentTask: (taskRequest) => api.post('/tasks/execute', taskRequest),
};

// Projects API
export const projectsAPI = {
  getProjects: (params = {}) => api.get('/projects', { params }),
  getProject: (projectId) => api.get(`/projects/${projectId}`),
  createProject: (projectData) => api.post('/projects', projectData),
  updateProject: (projectId, projectData) => api.put(`/projects/${projectId}`, projectData),
  deleteProject: (projectId) => api.delete(`/projects/${projectId}`),
};

// Agents API
export const agentsAPI = {
  getAvailableAgents: () => api.get('/agents/available'),
  getAgentStatus: (agentName) => api.get(`/agents/status/${agentName}`),
  getAgentPerformance: () => api.get('/agents/performance'),
  getAgentMemory: (agentName, params = {}) => api.get(`/agents/memory/${agentName}`, { params }),
  createAgentMemory: (memoryData) => api.post('/agents/memory', memoryData),
};

// Feedback API
export const feedbackAPI = {
  getFeedback: (params = {}) => api.get('/feedback', { params }),
  createFeedback: (feedbackData) => api.post('/feedback', feedbackData),
  getTaskFeedback: (taskId) => api.get(`/feedback/task/${taskId}`),
};

// Integrations API
export const integrationsAPI = {
  getIntegrations: () => api.get('/integrations'),
  getIntegration: (integrationId) => api.get(`/integrations/${integrationId}`),
  createIntegration: (integrationData) => api.post('/integrations', integrationData),
  updateIntegration: (integrationId, integrationData) => api.put(`/integrations/${integrationId}`, integrationData),
  deleteIntegration: (integrationId) => api.delete(`/integrations/${integrationId}`),
};

// Convenience functions for React Query
export const fetchDashboardStats = async () => {
  const response = await usersAPI.getDashboardStats();
  return response.data;
};

export const fetchTasks = async (params = {}) => {
  const response = await tasksAPI.getTasks(params);
  return response.data;
};

export const fetchRecentTasks = async (params = {}) => {
  const response = await tasksAPI.getTasks({ ...params, limit: params.limit || 10 });
  return response.data;
};

export const fetchTask = async (taskId) => {
  const response = await tasksAPI.getTask(taskId);
  return response.data;
};

export const fetchProjects = async (params = {}) => {
  const response = await projectsAPI.getProjects(params);
  return response.data;
};

export const fetchProject = async (projectId) => {
  const response = await projectsAPI.getProject(projectId);
  return response.data;
};

export const fetchAvailableAgents = async () => {
  const response = await agentsAPI.getAvailableAgents();
  return response.data;
};

export const fetchAgentPerformance = async () => {
  const response = await agentsAPI.getAgentPerformance();
  return response.data;
};

export const fetchIntegrations = async () => {
  const response = await integrationsAPI.getIntegrations();
  return response.data;
};

// Task execution with subscription checking
export const executeAgentTask = async (taskRequest) => {
  try {
    const response = await tasksAPI.executeAgentTask(taskRequest);
    return response.data;
  } catch (error) {
    if (error.response?.status === 402) {
      // Handle subscription limit exceeded
      throw new Error(error.response.data.detail || 'Subscription upgrade required');
    }
    throw error;
  }
};

// Check subscription status
export const checkSubscriptionStatus = async () => {
  const response = await usersAPI.getDashboardStats();
  return {
    subscription_tier: response.data.subscription_tier || 'free',
    tasks_this_month: response.data.tasks_this_month || 0,
    monthly_limit: response.data.monthly_limit || 10,
    usage_percentage: ((response.data.tasks_this_month || 0) / (response.data.monthly_limit || 10)) * 100
  };
};

// File upload utility
export const uploadFile = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });

  return response.data;
};

export default api;
