
declare global {
  interface Window {
    __RUNTIME_CONFIG__?: {
      VITE_API_URL?: string;
    };
  }
}

export const getRuntimeConfig = () => {
  if (typeof window !== 'undefined' && window.__RUNTIME_CONFIG__) {
    return window.__RUNTIME_CONFIG__;
  }
  
  return {
    VITE_API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000'
  };
};

export const API_BASE_URL = getRuntimeConfig().VITE_API_URL || 'http://localhost:8000';
