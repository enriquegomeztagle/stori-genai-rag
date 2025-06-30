import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  ThumbsUp, 
  ThumbsDown, 
  AlertTriangle, 
  MessageSquare,
  Download,
  RefreshCw
} from 'lucide-react';
import { 
  getSystemMetrics, 
  getRecentMetrics,
  exportMetrics,
  clearOldMetrics 
} from '../services/api';

interface SystemMetrics {
  total_queries: number;
  total_errors: number;
  average_response_time: number;
  like_percentage: number;
  tool_effectiveness: Record<string, number>;
  error_rate: number;
  conversation_retention_rate: number;
  timestamp: string;
}

interface ResponseMetrics {
  response_id: string;
  conversation_id: string;
  query: string;
  response: string;
  response_time: number;
  confidence_score: number;
  tools_used: string[];
  sources_count: number;
  timestamp: string;
  user_rating?: string;
  error_occurred: boolean;
  error_message?: string;
}

const MetricsDashboard: React.FC = () => {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [recentMetrics, setRecentMetrics] = useState<ResponseMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState<number | null>(null);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);

      const [system, recent] = await Promise.all([
        getSystemMetrics(),
        getRecentMetrics(24)
      ]);

      setSystemMetrics(system);
      setRecentMetrics(recent);
    } catch (err) {
      setError('Failed to fetch metrics');
      console.error('Error fetching metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();

    const interval = setInterval(fetchMetrics, 30000);
    setRefreshInterval(interval);

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, []);

  const handleExport = async () => {
    try {
      const data = await exportMetrics();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `metrics-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exporting metrics:', err);
    }
  };

  const handleClearOldMetrics = async () => {
    if (window.confirm('Are you sure you want to clear all metrics?')) {
      try {
        await clearOldMetrics(0);
        fetchMetrics();
      } catch (err) {
        console.error('Error clearing metrics:', err);
      }
    }
  };

  const formatTime = (seconds: number) => {
    if (seconds < 1) {
      return `${(seconds * 1000).toFixed(0)}ms`;
    }
    return `${seconds.toFixed(2)}s`;
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getStatusColor = (value: number, threshold: number) => {
    return value >= threshold ? 'text-green-600' : 'text-red-600';
  };

  if (loading && !systemMetrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-gray-500" />
        <span className="ml-2 text-gray-600">Loading metrics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-400" />
          <span className="ml-2 text-red-800">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Metrics Dashboard</h1>
          <p className="text-gray-600">Real-time performance and usage analytics</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={fetchMetrics}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={handleExport}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </button>
          <button
            onClick={handleClearOldMetrics}
            className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      {systemMetrics && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <MessageSquare className="h-8 w-8 text-blue-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Queries</p>
                  <p className="text-2xl font-bold text-gray-900">{systemMetrics.total_queries}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <Clock className="h-8 w-8 text-green-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Avg Response Time</p>
                  <p className={`text-2xl font-bold ${getStatusColor(systemMetrics.average_response_time, 2)}`}>
                    {formatTime(systemMetrics.average_response_time)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <ThumbsUp className="h-8 w-8 text-green-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Like Percentage</p>
                  <p className={`text-2xl font-bold ${getStatusColor(systemMetrics.like_percentage, 80)}`}>
                    {formatPercentage(systemMetrics.like_percentage)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <AlertTriangle className="h-8 w-8 text-red-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Error Rate</p>
                  <p className={`text-2xl font-bold ${getStatusColor(100 - systemMetrics.error_rate, 95)}`}>
                    {formatPercentage(systemMetrics.error_rate)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Tool Effectiveness</h3>
              <div className="space-y-3">
                {Object.entries(systemMetrics.tool_effectiveness).map(([tool, effectiveness]) => (
                  <div key={tool} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">{tool}</span>
                    <div className="flex items-center">
                      <div className="w-24 bg-gray-200 rounded-full h-2 mr-3">
                        <div
                          className="bg-green-500 h-2 rounded-full"
                          style={{ width: `${effectiveness}%` }}
                        ></div>
                      </div>
                      <span className={`text-sm font-medium ${getStatusColor(effectiveness, 80)}`}>
                        {formatPercentage(effectiveness)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Conversation Retention</h3>
              <div className="flex items-center justify-center h-32">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">
                    {formatPercentage(systemMetrics.conversation_retention_rate)}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">of conversations have follow-up questions</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Recent Activity (Last 24 Hours)</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Query
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Response Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rating
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tools Used
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {recentMetrics.slice(0, 10).map((metric) => (
                    <tr key={metric.response_id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(metric.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                        {metric.query}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatTime(metric.response_time)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {metric.user_rating ? (
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            metric.user_rating === 'like' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {metric.user_rating === 'like' ? (
                              <ThumbsUp className="h-3 w-3 mr-1" />
                            ) : (
                              <ThumbsDown className="h-3 w-3 mr-1" />
                            )}
                            {metric.user_rating}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {metric.tools_used.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {metric.tools_used.map((tool) => (
                              <span
                                key={tool}
                                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                              >
                                {tool}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-gray-400">None</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default MetricsDashboard; 
