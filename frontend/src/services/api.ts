import axios from 'axios';
import { API_BASE_URL } from '../config/runtime-config';

const API_BASE_URL_WITH_PATH = `${API_BASE_URL}/api/v1`;

const api = axios.create({
  baseURL: API_BASE_URL_WITH_PATH,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    console.log('Full URL:', `${API_BASE_URL_WITH_PATH}${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    console.error('Failed URL:', error.config?.url);
    return Promise.reject(error);
  }
);

export const sendMessage = async (data: {
  message: string;
  conversation_id?: string | null;
  use_tools?: boolean;
}) => {
  const response = await api.post('/conversation/chat', data);
  return response.data;
};

export const getConversationHistory = async (conversationId: string) => {
  const response = await api.get(`/conversation/${conversationId}/history`);
  return response.data;
};

export const deleteConversation = async (conversationId: string) => {
  const response = await api.delete(`/conversation/${conversationId}`);
  return response.data;
};

export const generateConversationSummary = async (conversationId: string) => {
  const response = await api.post(`/conversation/${conversationId}/summary`);
  return response.data;
};

export const classifyIntent = async (message: string) => {
  const response = await api.post('/conversation/intent/classify', {
    message,
    conversation_id: null,
    use_tools: false
  });
  return response.data;
};

export const escalateConversation = async (data: {
  conversation_id: string;
  reason: string;
  priority: string;
}) => {
  const response = await api.post('/conversation/escalate', data);
  return response.data;
};

export const listConversations = async () => {
  const response = await api.get('/conversation/conversations');
  return response.data;
};

export const uploadDocument = async (formData: FormData) => {
  const response = await api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getDocumentStats = async () => {
  const response = await api.get('/documents/stats');
  return response.data;
};

export const clearDocuments = async () => {
  const response = await api.delete('/documents/clear');
  return response.data;
};

export const searchDocuments = async (query: string, k: number = 3) => {
  const response = await api.get('/documents/search', {
    params: { query, k }
  });
  return response.data;
};

export const getHealthStatus = async () => {
  const response = await api.get('/health/health');
  return response.data;
};

export const getMemoryHealth = async () => {
  const response = await api.get('/health/memory');
  return response.data;
};

export const getVectorStoreHealth = async () => {
  const response = await api.get('/health/vector-store');
  return response.data;
};

export const getBedrockHealth = async () => {
  const response = await api.get('/health/bedrock');
  return response.data;
};

export const recordUserRating = async (data: {
  response_id: string;
  rating: 'like' | 'dislike';
}) => {
  const response = await api.post('/metrics/rating', data);
  return response.data;
};

export const getSystemMetrics = async () => {
  const response = await api.get('/metrics/system');
  return response.data;
};

export const getConversationMetrics = async (conversationId: string) => {
  const response = await api.get(`/metrics/conversation/${conversationId}`);
  return response.data;
};

export const getAllConversationMetrics = async () => {
  const response = await api.get('/metrics/conversations');
  return response.data;
};

export const getResponseMetrics = async (responseId: string) => {
  const response = await api.get(`/metrics/response/${responseId}`);
  return response.data;
};

export const getRecentMetrics = async (hours: number = 24) => {
  const response = await api.get('/metrics/recent', {
    params: { hours }
  });
  return response.data;
};

export const exportMetrics = async () => {
  const response = await api.post('/metrics/export');
  return response.data;
};

export const clearOldMetrics = async (days: number = 30) => {
  const response = await api.delete('/metrics/clear', {
    params: { days }
  });
  return response.data;
};

export default api; 
