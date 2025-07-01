import { API_BASE_URL } from './runtime-config';

export const API_CONFIG = {
  BASE_URL: API_BASE_URL,
  ENDPOINTS: {
    HEALTH: '/api/v1/health/health',
    HEALTH_MEMORY: '/api/v1/health/health/memory',
    HEALTH_VECTOR: '/api/v1/health/health/vector-store',
    HEALTH_BEDROCK: '/api/v1/health/health/bedrock',
    CHAT: '/api/v1/chat',
    DOCUMENTS: '/api/v1/documents',
    METRICS: '/api/v1/metrics',
  }
};

export const buildApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

console.log('🔧 API Configuration:', {
  BASE_URL: API_CONFIG.BASE_URL,
  ENV_VAR: import.meta.env.VITE_API_URL,
  MODE: import.meta.env.MODE
});
