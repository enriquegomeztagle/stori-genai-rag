import React, { useState, useEffect, useRef } from 'react';
import { Activity, RefreshCw, CheckCircle, XCircle, Database, Brain, HardDrive } from 'lucide-react';

interface HealthStatus {
  status: string;
  message: string;
  timestamp: string;
}

interface ServiceHealth {
  status: string;
  details?: any;
  error?: string;
}

interface ServicesHealth {
  memory: ServiceHealth;
  vectorStore: ServiceHealth;
  bedrock: ServiceHealth;
}

const HealthCheck: React.FC = () => {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [servicesHealth, setServicesHealth] = useState<ServicesHealth | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingServices, setIsLoadingServices] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const autoRefreshIntervalRef = useRef<number | null>(null);

  const checkHealth = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/health/health');
      const data = await response.json();
      
      setHealthStatus({
        status: data.status,
        message: data.message || 'Backend is running',
        timestamp: new Date().toLocaleTimeString()
      });
      
      const newLogs = [
        `🔍 Checking backend health...`,
        `📡 Request sent to: http://localhost:8000/api/v1/health/health`,
        `📊 Response received: ${response.status} ${response.statusText}`,
        `📋 Status: ${data.status}`,
        `💬 Message: ${data.message || 'Backend is running'}`,
        `⏰ Timestamp: ${new Date().toLocaleTimeString()}`
      ];
      
      setLogs(newLogs);
      setLastCheck(new Date());
    } catch (error) {
      setHealthStatus({
        status: 'error',
        message: 'Failed to connect to backend',
        timestamp: new Date().toLocaleTimeString()
      });
      
      const errorLogs = [
        `🔍 Checking backend health...`,
        `📡 Request sent to: http://localhost:8000/api/v1/health/health`,
        `❌ Connection failed: ${error}`,
        `💀 Backend appears to be down`,
        `⏰ Timestamp: ${new Date().toLocaleTimeString()}`
      ];
      
      setLogs(errorLogs);
      setLastCheck(new Date());
    } finally {
      setIsLoading(false);
    }
  };

  const checkServicesHealth = async () => {
    setIsLoadingServices(true);
    try {
      const memoryResponse = await fetch('http://localhost:8000/api/v1/health/health/memory');
      const memoryData = await memoryResponse.json();
      
      const vectorResponse = await fetch('http://localhost:8000/api/v1/health/health/vector-store');
      const vectorData = await vectorResponse.json();
      
      const bedrockResponse = await fetch('http://localhost:8000/api/v1/health/health/bedrock');
      const bedrockData = await bedrockResponse.json();
      
      setServicesHealth({
        memory: {
          status: memoryData.status,
          details: memoryData
        },
        vectorStore: {
          status: vectorData.status,
          details: vectorData
        },
        bedrock: {
          status: bedrockData.status,
          details: bedrockData
        }
      });
    } catch (error) {
      setServicesHealth({
        memory: { status: 'error', error: 'Failed to check memory service' },
        vectorStore: { status: 'error', error: 'Failed to check vector store service' },
        bedrock: { status: 'error', error: 'Failed to check bedrock service' }
      });
    } finally {
      setIsLoadingServices(false);
    }
  };

  const startAutoRefresh = () => {
    if (autoRefreshIntervalRef.current) {
      clearInterval(autoRefreshIntervalRef.current);
    }
    
    autoRefreshIntervalRef.current = setInterval(() => {
      if (autoRefreshEnabled) {
        console.log('🔄 Auto-refreshing health status...');
        checkHealth();
        checkServicesHealth();
      }
    }, 30000);
  };

  const stopAutoRefresh = () => {
    if (autoRefreshIntervalRef.current) {
      clearInterval(autoRefreshIntervalRef.current);
      autoRefreshIntervalRef.current = null;
    }
  };

  const toggleAutoRefresh = () => {
    setAutoRefreshEnabled(!autoRefreshEnabled);
    if (autoRefreshEnabled) {
      stopAutoRefresh();
    } else {
      startAutoRefresh();
    }
  };

  useEffect(() => {
    checkHealth();
    checkServicesHealth();
    startAutoRefresh();

    return () => {
      stopAutoRefresh();
    };
  }, []);

  useEffect(() => {
    if (autoRefreshEnabled) {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }
  }, [autoRefreshEnabled]);

  const getStatusIcon = () => {
    if (isLoading) {
      return <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />;
    }
    
    if (healthStatus?.status === 'healthy') {
      return <CheckCircle className="h-8 w-8 text-green-500" />;
    }
    
    return <XCircle className="h-8 w-8 text-red-500" />;
  };

  const getStatusEmoji = () => {
    if (isLoading) return '⏳';
    if (healthStatus?.status === 'healthy') return '✅';
    return '💀';
  };

  const getStatusColor = () => {
    if (isLoading) return 'bg-blue-50 border-blue-200';
    if (healthStatus?.status === 'healthy') return 'bg-green-50 border-green-200';
    return 'bg-red-50 border-red-200';
  };

  const getStatusText = () => {
    if (isLoading) return 'Checking Backend...';
    if (healthStatus?.status === 'healthy') return 'Backend is Healthy! 🎉';
    return 'Backend is Down! 😱';
  };

  const getServiceStatusColor = (status: string) => {
    if (status === 'healthy') return 'bg-green-50 border-green-200';
    if (status === 'unhealthy') return 'bg-red-50 border-red-200';
    return 'bg-yellow-50 border-yellow-200';
  };

  const getServiceStatusIcon = (status: string) => {
    if (status === 'healthy') return <CheckCircle className="h-6 w-6 text-green-500" />;
    if (status === 'unhealthy') return <XCircle className="h-6 w-6 text-red-500" />;
    return <RefreshCw className="h-6 w-6 text-yellow-500 animate-spin" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🏥 Health Check Dashboard
          </h1>
          <p className="text-gray-600">
            Monitoring the backend service status in real-time
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${autoRefreshEnabled ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
              <span className="font-semibold text-gray-700">
                Auto-refresh: {autoRefreshEnabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            <button
              onClick={toggleAutoRefresh}
              className={`px-4 py-2 rounded-lg font-semibold transition-colors duration-200 ${
                autoRefreshEnabled 
                  ? 'bg-green-600 hover:bg-green-700 text-white' 
                  : 'bg-gray-600 hover:bg-gray-700 text-white'
              }`}
            >
              {autoRefreshEnabled ? '🔄 Disable Auto-refresh' : '▶️ Enable Auto-refresh'}
            </button>
          </div>
        </div>

        <div className={`rounded-2xl border-2 p-8 mb-8 transition-all duration-300 ${getStatusColor()}`}>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              {getStatusIcon()}
              <div>
                <h2 className="text-2xl font-bold text-gray-800">
                  {getStatusText()}
                </h2>
                <p className="text-gray-600">
                  {healthStatus?.message || 'Checking connection...'}
                </p>
              </div>
            </div>
            <div className="text-6xl">
              {getStatusEmoji()}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center space-x-2">
                <Activity className="h-5 w-5 text-blue-500" />
                <span className="font-semibold text-gray-700">Status</span>
              </div>
              <p className="text-lg font-bold text-gray-800 mt-1">
                {healthStatus?.status || 'Unknown'}
              </p>
            </div>
            
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center space-x-2">
                <span className="text-2xl">⏰</span>
                <span className="font-semibold text-gray-700">Last Check</span>
              </div>
              <p className="text-lg font-bold text-gray-800 mt-1">
                {lastCheck?.toLocaleTimeString() || 'Never'}
              </p>
            </div>
            
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center space-x-2">
                <span className="text-2xl">🔗</span>
                <span className="font-semibold text-gray-700">Endpoint</span>
              </div>
              <p className="text-sm font-mono text-gray-600 mt-1 break-all">
                localhost:8000/api/v1/health/health
              </p>
            </div>
          </div>

          <div className="text-center space-x-4">
            <button
              onClick={checkHealth}
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 flex items-center space-x-2 mx-auto mb-2"
            >
              <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>{isLoading ? 'Checking...' : 'Check Health Again'}</span>
            </button>
            
            <button
              onClick={checkServicesHealth}
              disabled={isLoadingServices}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 flex items-center space-x-2 mx-auto"
            >
              <RefreshCw className={`h-5 w-5 ${isLoadingServices ? 'animate-spin' : ''}`} />
              <span>{isLoadingServices ? 'Checking Services...' : 'Check Services Health'}</span>
            </button>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <div className="flex items-center space-x-2 mb-6">
            <span className="text-2xl">🔧</span>
            <h3 className="text-xl font-bold text-gray-800">Individual Services Health</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className={`rounded-xl border-2 p-6 ${getServiceStatusColor(servicesHealth?.memory?.status || 'unknown')}`}>
              <div className="flex items-center space-x-3 mb-4">
                <HardDrive className="h-8 w-8 text-blue-500" />
                <div>
                  <h4 className="text-lg font-bold text-gray-800">Memory Service</h4>
                  <p className="text-sm text-gray-600">Redis & Conversation Storage</p>
                </div>
              </div>
              
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-gray-700">Status:</span>
                <div className="flex items-center space-x-2">
                  {getServiceStatusIcon(servicesHealth?.memory?.status || 'unknown')}
                  <span className={`font-bold ${
                    servicesHealth?.memory?.status === 'healthy' ? 'text-green-600' :
                    servicesHealth?.memory?.status === 'unhealthy' ? 'text-red-600' : 'text-yellow-600'
                  }`}>
                    {servicesHealth?.memory?.status || 'Unknown'}
                  </span>
                </div>
              </div>
              
              {servicesHealth?.memory?.details && (
                <div className="bg-white rounded-lg p-3 text-sm">
                  <p className="font-semibold text-gray-700">Details:</p>
                  <p className="text-gray-600">Connection: {servicesHealth.memory.details.connection || 'N/A'}</p>
                </div>
              )}
              
              {servicesHealth?.memory?.error && (
                <div className="bg-red-50 rounded-lg p-3 text-sm">
                  <p className="text-red-600 font-semibold">Error:</p>
                  <p className="text-red-500">{servicesHealth.memory.error}</p>
                </div>
              )}
            </div>

            <div className={`rounded-xl border-2 p-6 ${getServiceStatusColor(servicesHealth?.vectorStore?.status || 'unknown')}`}>
              <div className="flex items-center space-x-3 mb-4">
                <Database className="h-8 w-8 text-purple-500" />
                <div>
                  <h4 className="text-lg font-bold text-gray-800">Vector Store</h4>
                  <p className="text-sm text-gray-600">ChromaDB & Document Storage</p>
                </div>
              </div>
              
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-gray-700">Status:</span>
                <div className="flex items-center space-x-2">
                  {getServiceStatusIcon(servicesHealth?.vectorStore?.status || 'unknown')}
                  <span className={`font-bold ${
                    servicesHealth?.vectorStore?.status === 'healthy' ? 'text-green-600' :
                    servicesHealth?.vectorStore?.status === 'unhealthy' ? 'text-red-600' : 'text-yellow-600'
                  }`}>
                    {servicesHealth?.vectorStore?.status || 'Unknown'}
                  </span>
                </div>
              </div>
              
              {servicesHealth?.vectorStore?.details && (
                <div className="bg-white rounded-lg p-3 text-sm">
                  <p className="font-semibold text-gray-700">Stats:</p>
                  <p className="text-gray-600">Documents: {servicesHealth.vectorStore.details.total_documents ?? 'N/A'}</p>
                  <p className="text-gray-600">Chunks: {servicesHealth.vectorStore.details.total_chunks ?? 'N/A'}</p>
                </div>
              )}
              
              {servicesHealth?.vectorStore?.error && (
                <div className="bg-red-50 rounded-lg p-3 text-sm">
                  <p className="text-red-600 font-semibold">Error:</p>
                  <p className="text-red-500">{servicesHealth.vectorStore.error}</p>
                </div>
              )}
            </div>

            <div className={`rounded-xl border-2 p-6 ${getServiceStatusColor(servicesHealth?.bedrock?.status || 'unknown')}`}>
              <div className="flex items-center space-x-3 mb-4">
                <Brain className="h-8 w-8 text-orange-500" />
                <div>
                  <h4 className="text-lg font-bold text-gray-800">Bedrock Service</h4>
                  <p className="text-sm text-gray-600">AWS Bedrock & LLM</p>
                </div>
              </div>
              
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-gray-700">Status:</span>
                <div className="flex items-center space-x-2">
                  {getServiceStatusIcon(servicesHealth?.bedrock?.status || 'unknown')}
                  <span className={`font-bold ${
                    servicesHealth?.bedrock?.status === 'healthy' ? 'text-green-600' :
                    servicesHealth?.bedrock?.status === 'unhealthy' ? 'text-red-600' : 'text-yellow-600'
                  }`}>
                    {servicesHealth?.bedrock?.status || 'Unknown'}
                  </span>
                </div>
              </div>
              
              {servicesHealth?.bedrock?.details && (
                <div className="bg-white rounded-lg p-3 text-sm">
                  <p className="font-semibold text-gray-700">Response:</p>
                  <p className="text-gray-600">{servicesHealth.bedrock.details.response || 'N/A'}</p>
                </div>
              )}
              
              {servicesHealth?.bedrock?.error && (
                <div className="bg-red-50 rounded-lg p-3 text-sm">
                  <p className="text-red-600 font-semibold">Error:</p>
                  <p className="text-red-500">{servicesHealth.bedrock.error}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-6">
          <div className="flex items-center space-x-2 mb-4">
            <span className="text-2xl">📋</span>
            <h3 className="text-xl font-bold text-gray-800">Backend Logs</h3>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-4 h-64 overflow-y-auto">
            {logs.length === 0 ? (
              <div className="text-gray-400 text-center py-8">
                <span className="text-2xl">🤖</span>
                <p className="mt-2">No logs available yet...</p>
              </div>
            ) : (
              <div className="space-y-2">
                {logs.map((log, index) => (
                  <div key={index} className="text-green-400 font-mono text-sm">
                    {log}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="text-center mt-8 text-gray-500">
          <p>🔄 Auto-refresh every 30 seconds {autoRefreshEnabled ? '(Active)' : '(Disabled)'}</p>
          <p className="text-sm mt-2">
            Made for the Stori GenAI RAG Challenge
          </p>
        </div>
      </div>
    </div>
  );
};

export default HealthCheck; 
