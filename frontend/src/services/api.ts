import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
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

export default api; 
