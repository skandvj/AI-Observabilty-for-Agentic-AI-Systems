'use client';

import { useEffect, useState } from 'react';
import apiClient from '@/lib/api';
import { DashboardMetrics as MetricsType } from '@/types';

interface DashboardMetricsProps {
  onMetricClick?: (metric: string) => void;
}

export default function DashboardMetrics({ onMetricClick }: DashboardMetricsProps) {
  const [stats, setStats] = useState<MetricsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const data = await apiClient.getStats();
        setStats(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch stats');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    
    // Refresh stats every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded mb-2"></div>
            <div className="h-8 bg-gray-200 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading metrics</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const metrics = [
    {
      id: 'total_records',
      label: 'Total Records',
      value: stats.totalRecords?.toLocaleString() || '0',
      icon: (
        <svg className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      trend: stats.qualityTrend
    },
    {
      id: 'quality_score',
      label: 'Avg Quality Score',
      value: `${(stats.avgQualityScore || 0).toFixed(1)}%`,
      icon: (
        <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      trend: stats.qualityTrend || 0
    },
    {
      id: 'issues',
      label: 'Active Issues',
      value: (stats.issuesCount || 0).toLocaleString(),
      icon: (
        <svg className="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      trend: -2.1
    },
    {
      id: 'processing_rate',
      label: 'Processing Rate',
      value: `${(stats.processingRate || 0)}/hr`,
      icon: (
        <svg className="h-8 w-8 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      trend: 5.2
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {metrics.map((metric) => (
        <div 
          key={metric.id}
          className="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => onMetricClick?.(metric.id)}
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              {metric.icon}
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">{metric.label}</p>
              <div className="flex items-center">
                <p className="text-2xl font-semibold text-gray-900">{metric.value}</p>
                {metric.trend && (
                  <span className={`ml-2 text-sm font-medium ${
                    metric.trend > 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {metric.trend > 0 ? '+' : ''}{metric.trend}%
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
} 