'use client'

import React, { useState, useEffect } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area,
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  ComposedChart
} from 'recharts'
import { 
  TrendingUp, 
  TrendingDown, 
  BarChart3, 
  PieChart as PieChartIcon, 
  Activity,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  Target,
  Users,
  Database,
  RefreshCw
} from 'lucide-react'
import { apiClient, AnalyticsData } from '../api'

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('7d')
  const [selectedMetric, setSelectedMetric] = useState<'quality' | 'volume' | 'cost'>('quality')
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.getDashboardAnalytics()
      setAnalyticsData(response)
    } catch (err) {
      console.error('Failed to fetch analytics data:', err)
      setError('Failed to load analytics data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalyticsData()
  }, [timeRange])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(fetchAnalyticsData, 30000)
    return () => clearInterval(interval)
  }, [])

  const MetricCard = ({ 
    title, 
    value, 
    change, 
    icon: Icon, 
    color = 'blue',
    format = 'number'
  }: {
    title: string
    value: number | null
    change: number
    icon: any
    color?: string
    format?: 'number' | 'percentage' | 'currency'
  }) => {
    const formatValue = (val: number | null, fmt: string) => {
      if (val === null || val === undefined) return '0'
      
      switch (fmt) {
        case 'percentage': return `${val}%`
        case 'currency': return `$${val.toFixed(2)}`
        default: return val.toLocaleString()
      }
    }

    const isPositive = change > 0
    const colorClass = {
      blue: 'bg-blue-500',
      green: 'bg-green-500',
      yellow: 'bg-yellow-500',
      red: 'bg-red-500',
      purple: 'bg-purple-500'
    }[color]

    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{formatValue(value, format)}</p>
          </div>
          <div className={`p-3 rounded-full ${colorClass}`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
        </div>
        <div className="mt-4 flex items-center">
          {isPositive ? (
            <TrendingUp className="h-4 w-4 text-green-500 mr-2" />
          ) : (
            <TrendingDown className="h-4 w-4 text-red-500 mr-2" />
          )}
          <span className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {Math.abs(change)}%
          </span>
          <span className="text-sm text-gray-500 ml-1">vs last period</span>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-2">
            <RefreshCw className="h-5 w-5 animate-spin text-blue-600" />
            <span className="text-gray-600">Loading analytics...</span>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load analytics</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={fetchAnalyticsData}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Try Again
            </button>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (!analyticsData) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <span className="text-gray-600">No analytics data available</span>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Analytics & Insights</h1>
            <p className="mt-1 text-sm text-gray-500">
              Deep dive into quality trends, performance metrics, and system insights
            </p>
          </div>
          <div className="mt-4 sm:mt-0 flex items-center space-x-4">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
            <button 
              onClick={fetchAnalyticsData}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm flex items-center space-x-2"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Avg Quality Score"
            value={analyticsData.today.avg_quality_score}
            change={5.4}
            icon={Target}
            color="green"
            format="percentage"
          />
          <MetricCard
            title="Total Processed"
            value={analyticsData.today.total_processed}
            change={12.3}
            icon={Activity}
            color="blue"
          />
          <MetricCard
            title="Active Issues"
            value={analyticsData.today.total_issues}
            change={-8.7}
            icon={AlertTriangle}
            color="yellow"
          />
          <MetricCard
            title="Weekly Cost"
            value={338.70}
            change={3.2}
            icon={DollarSign}
            color="purple"
            format="currency"
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Quality Trend */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Quality Trend</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analyticsData.qualityTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="avg_quality" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  name="Quality Score"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Source Performance */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Source Performance</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analyticsData.sourcePerformanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="source" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="avg_quality" fill="#10b981" name="Avg Quality" />
                <Bar dataKey="processed" fill="#3b82f6" name="Processed" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Issue Breakdown */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Issue Breakdown</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                                  <Pie
                    data={analyticsData.issueBreakdownData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${percent ? (percent * 100).toFixed(0) : 0}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                  {analyticsData.issueBreakdownData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            
            <div className="space-y-4">
              <h4 className="text-md font-medium text-gray-900">Top Failure Reasons</h4>
              <div className="space-y-3">
                {analyticsData.topFailureReasons.map((reason, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{reason.reason}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${reason.percentage}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-900">{reason.count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Company Metrics */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Company Performance</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Records</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Quality</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issues</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cost</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {analyticsData.companyMetricsData.map((company, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{company.company}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{(company.records || 0).toLocaleString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{company.avgQuality || 0}%</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{company.issues || 0}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${(company.cost || 0).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
} 