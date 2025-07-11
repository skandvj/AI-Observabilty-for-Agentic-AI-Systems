'use client'

import React, { useState, useEffect } from 'react'
import { useDashboardContext } from '@/lib/DashboardContext';
import DashboardLayout from '@/components/layout/DashboardLayout'
import PageHeader from '@/components/layout/PageHeader'
import ContentLayout from '@/components/layout/ContentLayout'
import DashboardMetrics from '@/components/dashboard/DashboardMetrics'
import AdvancedFilters from '@/components/filters/AdvancedFilters'
import QualityRecordsTable from '@/components/table/QualityRecordsTable'
import RecordDetailModal from '@/components/modals/RecordDetailModal'
import { DashboardFilters, PaginatedResponse, QualityRecord, PaginationParams } from '@/types'
import { loadFromLocalStorage, saveToLocalStorage } from '@/lib/utils'
import apiClient from '@/lib/api'
import { 
  Plus, 
  Download, 
  RefreshCw, 
  Filter, 
  BarChart3, 
  FileText, 
  AlertTriangle,
  Zap,
  Brain,
  Shield,
  Database,
  Mail,
  Settings,
  TestTube,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Activity,
  Server,
  Cpu,
  AlertCircle,
  FileCode,
  Upload,
  Eye,
  Search,
  Target,
  Rocket,
  Wrench,
  Bug,
  MessageSquare,
  Building,
  Plug,
  Bell
} from 'lucide-react'

export default function DashboardPage() {
  const { filters, setFilters } = useDashboardContext();
  const [isInitialized, setIsInitialized] = useState(false)
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 1,
    pageSize: 25,
    sortBy: 'createdAt',
    sortOrder: 'desc'
  })
  const [data, setData] = useState<PaginatedResponse<QualityRecord>>({
    data: [],
    pagination: {
      page: 1,
      pageSize: 25,
      total: 0,
      totalPages: 0,
      hasNext: false,
      hasPrev: false,
    },
    filters: {
      companies: [],
      sourceConnectors: [],
      statuses: [],
      priorities: [],
      issueTypes: [],
      qualityScoreRange: [0, 100],
      dateRange: { from: '', to: '' },
      searchQuery: '',
      tags: [],
      departments: [],
      authors: []
    },
    appliedFiltersCount: 0,
  })
  const [loading, setLoading] = useState(false)
  const [selectedRecords, setSelectedRecords] = useState<string[]>([])
  const [selectedRecord, setSelectedRecord] = useState<QualityRecord | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [overrideModal, setOverrideModal] = useState<{ open: boolean, record: any } | null>(null);
  const [overrideReason, setOverrideReason] = useState('');
  const [userId, setUserId] = useState('user-123'); // Replace with real user ID logic

  // Backend integration state
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking')
  const [testResults, setTestResults] = useState<any[]>([])
  const [isTesting, setIsTesting] = useState(false)
  const [showBackendPanel, setShowBackendPanel] = useState(false)

  // Initialize data on component mount
  useEffect(() => {
    const savedFilters = loadFromLocalStorage('dashboard-filters', {})
    setFilters(savedFilters)
    setIsInitialized(true)
    checkBackendStatus()
  }, [])

  // Check backend status
  const checkBackendStatus = async () => {
    setBackendStatus('checking')
    try {
      await apiClient.getHealth()
      setBackendStatus('online')
    } catch (error) {
      setBackendStatus('offline')
    }
  }

  // Fetch data when filters or pagination changes
  useEffect(() => {
    if (isInitialized) {
      fetchAllRecords();
    }
  }, [filters, pagination, isInitialized]);

  // Unified fetch logic (same as Quality Records page)
  const [records, setRecords] = useState<any[]>([]);
  const fetchAllRecords = async () => {
    setLoading(true);
    try {
      const response = await apiClient.getQualityRecords(filters, pagination);
      let all = response.data || [];
      // Map all non-approved statuses to 'flagged' for display
      const mapped = all.map(r => ({ ...r, status: r.status === 'approved' ? 'approved' : 'flagged' }));
      setRecords(mapped);
    } catch (err) {
      console.error('Error fetching records:', err);
      setRecords([]);
    } finally {
      setLoading(false);
    }
  };

  // Listen for records-updated events from other components
  useEffect(() => {
    const handleRecordsUpdated = () => {
      fetchData()
    }

    window.addEventListener('records-updated', handleRecordsUpdated)
    
    return () => {
      window.removeEventListener('records-updated', handleRecordsUpdated)
    }
  }, [])

  // Fetch data function
  const fetchData = async () => {
    try {
      setLoading(true)
      
      try {
        const response = await apiClient.getQualityRecords(filters, pagination)
        setData(response)
      } catch (error) {
        console.error('Error fetching data:', error)
      }

      // Sort data
      const filteredData = data.data.sort((a, b) => {
        const aVal = a[pagination.sortBy || 'createdAt']
        const bVal = b[pagination.sortBy || 'createdAt']
        const multiplier = pagination.sortOrder === 'desc' ? -1 : 1
        
        if (typeof aVal === 'string' && typeof bVal === 'string') {
          return aVal.localeCompare(bVal) * multiplier
        }
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return (aVal - bVal) * multiplier
        }
        return 0
      })

      // Paginate
      const startIndex = (pagination.page - 1) * pagination.pageSize
      const endIndex = startIndex + pagination.pageSize
      const paginatedData = filteredData.slice(startIndex, endIndex)

      setData({
        data: paginatedData,
        pagination: {
          page: pagination.page,
          pageSize: pagination.pageSize,
          total: filteredData.length,
          totalPages: Math.ceil(filteredData.length / pagination.pageSize),
          hasNext: endIndex < filteredData.length,
          hasPrev: pagination.page > 1,
        },
        filters: {
          companies: filters.companies || [],
          sourceConnectors: filters.sourceConnectors || [],
          statuses: filters.statuses || [],
          priorities: filters.priorities || [],
          issueTypes: filters.issueTypes || [],
          qualityScoreRange: filters.qualityScoreRange || [0, 100],
          dateRange: filters.dateRange || { from: '', to: '' },
          searchQuery: filters.searchQuery || '',
          tags: filters.tags || [],
          departments: filters.departments || [],
          authors: filters.authors || []
        },
        appliedFiltersCount: Object.keys(filters).filter(key => {
          const value = filters[key as keyof DashboardFilters]
          return value && (Array.isArray(value) ? value.length > 0 : value !== '')
        }).length,
      })

    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Backend test functions
  const runBackendTest = async (testName: string, testFunction: () => Promise<any>) => {
    setIsTesting(true)
    const startTime = Date.now()
    
    try {
      const result = await testFunction()
      const endTime = Date.now()
      
      setTestResults(prev => [{
        name: testName,
        status: 'success',
        result,
        duration: endTime - startTime,
        timestamp: new Date().toISOString()
      }, ...prev.slice(0, 9)])
    } catch (error) {
      const endTime = Date.now()
      setTestResults(prev => [{
        name: testName,
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
        duration: endTime - startTime,
        timestamp: new Date().toISOString()
      }, ...prev.slice(0, 9)])
    } finally {
      setIsTesting(false)
    }
  }

  const testHealth = () => runBackendTest('Health Check', () => apiClient.getHealth())
  const testStats = () => runBackendTest('System Stats', () => apiClient.getStats())
  const testRecords = () => runBackendTest('Get Records', () => apiClient.getRecords())
  const testAnalytics = () => runBackendTest('Dashboard Analytics', () => apiClient.getDashboardAnalytics())
  const testIssues = () => runBackendTest('Get Issues', () => apiClient.getIssues())
  const testDeadLetters = () => runBackendTest('Get Dead Letters', () => apiClient.getDeadLetters())
  const testCompanies = () => runBackendTest('Get Companies', () => apiClient.getCompanies())
  const testConnectors = () => runBackendTest('Get Connectors', () => apiClient.getConnectors())
  const testRequestLogs = () => runBackendTest('Get Request Logs', () => apiClient.getRequestLogs())
  const testRequestAnalytics = () => runBackendTest('Request Analytics', () => apiClient.getRequestAnalytics())
  const testEvaluationMetrics = () => runBackendTest('Evaluation Metrics', () => apiClient.getEvaluationMetrics())
  const testRedTeamResults = () => runBackendTest('Red Team Results', () => apiClient.getRedTeamResults())
  const testAlertEmails = () => runBackendTest('Alert Emails', () => apiClient.getAlertEmails())
  const testAlertTemplate = () => runBackendTest('Alert Template', () => apiClient.getAlertTemplate())
  const testSelfTest = () => runBackendTest('Self Test', () => apiClient.selfTest())

  const testContentIngestion = async () => {
    const testContent = {
      record_id: "test-001",
      content: "This is a comprehensive guide about machine learning algorithms and their applications in data science. The document covers various topics including supervised learning, unsupervised learning, and deep learning techniques.",
      tags: ["machine learning", "algorithms", "data science", "AI"],
      source_connector: "SharePoint",
      content_metadata: {
        author: "Test User",
        department: "Engineering"
      }
    }
    
    await runBackendTest('Content Ingestion', () => apiClient.ingestContent(testContent))
  }

  const testRulesCheck = async () => {
    const testRules = {
      document_text: "API documentation for user authentication service. Handles login, registration, password reset, and session management.",
      tags: ["api", "authentication", "security", "documentation"],
      source_connector: "SharePoint"
    }
    
    await runBackendTest('Rules Check', () => apiClient.checkRules(testRules))
  }

  const testLLMAnalysis = async () => {
    const testLLM = {
      content: "Marketing strategy for Q1 2024 focusing on digital transformation initiatives and customer acquisition.",
      tags: ["marketing", "strategy", "digital-transformation"],
      context: {
        source: "strategy-docs",
        department: "Marketing"
      }
    }
    
    await runBackendTest('LLM Analysis', () => apiClient.analyzeLLM(testLLM))
  }

  const testCustomLLM = async () => {
    const testCustomLLM = {
      content: "Database migration plan for moving from MySQL to PostgreSQL with minimal downtime.",
      tags: ["database", "migration", "postgresql"],
      custom_prompt: "Analyze this technical plan for completeness and risk assessment.",
      constraints: [
        {
          id: "technical_completeness",
          name: "Technical Completeness",
          enabled: true,
          weight: 0.4
        }
      ],
      quality_weights: {
        technical_completeness: 0.4
      }
    }
    
    await runBackendTest('Custom LLM Analysis', () => apiClient.customLLMAnalysis(testCustomLLM))
  }

  const testRedTeam = async () => {
    const testRedTeam = {
      scenario_id: "generic_tags",
      content: "Test content with generic tags",
      tags: ["generic", "document", "test"],
      test_objectives: ["Detect generic tags", "Flag low-quality content"],
      expected_issues: ["generic_tags", "low_quality"]
    }
    
    await runBackendTest('Red Team Analysis', () => apiClient.redTeamAnalysis(testRedTeam))
  }

  const testChainOfThought = async () => {
    const testCOT = {
      content: "AI implementation plan for customer support automation using NLP and machine learning.",
      tags: ["ai", "nlp", "automation", "customer-support"],
      custom_prompt: "Analyze this plan step by step for feasibility and implementation challenges.",
      constraints: [],
      quality_weights: {}
    }
    
    await runBackendTest('Chain of Thought Analysis', () => apiClient.chainOfThoughtAnalysis(testCOT))
  }

  const testExportRecords = () => runBackendTest('Export Records', () => apiClient.exportRecords('json'))
  const testAddAlertEmail = () => runBackendTest('Add Alert Email', () => apiClient.addAlertEmail('test@example.com'))
  const testTestAlert = () => runBackendTest('Test Alert', () => apiClient.testAlert())

  const handleFiltersChange = (newFilters: Partial<DashboardFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }))
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handleFiltersReset = () => {
    setFilters({})
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handleSort = (sortBy: string, sortOrder: 'asc' | 'desc') => {
    setPagination(prev => ({ ...prev, sortBy: sortBy as keyof QualityRecord, sortOrder, page: 1 }))
  }

  const handlePageChange = (page: number) => {
    setPagination(prev => ({ ...prev, page }))
  }

  const handlePageSizeChange = (pageSize: number) => {
    setPagination(prev => ({ ...prev, pageSize, page: 1 }))
  }

  const handleRecordClick = (record: QualityRecord) => {
    setSelectedRecord(record)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedRecord(null)
  }

  const handleUpdateRecord = (updatedRecord: QualityRecord) => {
    // Update the record in the data array
    setData(prevData => ({
      ...prevData,
      data: prevData.data.map(record => 
        record.id === updatedRecord.id ? updatedRecord : record
      )
    }))
    
    // Update the selected record if it's the same one
    if (selectedRecord && selectedRecord.id === updatedRecord.id) {
      setSelectedRecord(updatedRecord)
    }
  }

  const handleReprocessRecord = async (recordId: string, content: string, tags: string[]) => {
    try {
      const result = await apiClient.ingestContent({
        record_id: recordId,
        content,
        tags,
        source_connector: 'SharePoint'
      })
      
      // Update the record with new processing results
      const updatedRecord = {
        ...selectedRecord!,
        quality_score: result.quality_score,
        quality_level: result.quality_level,
        quality_checks: result.quality_checks,
        llm_suggestions: result.suggestions,
        llm_reasoning: result.reasoning
      }
      
      handleUpdateRecord(updatedRecord)
    } catch (error) {
      console.error('Failed to reprocess record:', error)
    }
  }

  const handleRecordUpdated = () => {
    // Refresh the records list after any record update
    fetchData()
  }

  // Approve flagged record
  const [isApproving, setIsApproving] = useState(false);
  const handleBulkAction = async (action: string, recordIds: string[]) => {
    if (action === 'approve' && recordIds.length > 0) {
      setIsApproving(true);
      try {
        await apiClient.approveFlaggedRecord(recordIds[0], 'user-123');
        await fetchAllRecords();
      } catch (err) {
        alert('Failed to approve record.');
      } finally {
        setIsApproving(false);
      }
    }
  };

  const handleMetricClick = (metric: string) => {
    switch (metric) {
      case 'total_records':
        setFilters({})
        break
      case 'quality_score':
        setFilters(prev => ({ 
          ...prev, 
          qualityScoreRange: [0, 70] 
        }))
        break
      case 'total_issues':
        setFilters(prev => ({ 
          ...prev, 
          statuses: ['flagged', 'under_review'] 
        }))
        break
      case 'processing_rate':
        setFilters({})
        break
    }
  }

  // Calculate dashboard stats
  const dashboardStats = [
    {
      label: 'Total Records',
      value: data.pagination.total,
      trend: 12.3
    },
    {
      label: 'Quality Score',
      value: '88.2%',
      trend: 5.4
    },
    {
      label: 'Active Issues',
      value: data.data.filter(r => r.status === 'flagged' || r.status === 'under_review').length,
      trend: -8.7
    },
    {
      label: 'Processing Rate',
      value: '1.2K/hr',
      trend: 15.2
    }
  ]

  const pageActions = [
    {
      label: 'Refresh',
      icon: RefreshCw,
      variant: 'outline' as const,
      onClick: () => fetchData(),
      disabled: loading
    },
    {
      label: 'Export All',
      icon: Download,
      variant: 'outline' as const,
      onClick: () => console.log('Export all')
    },
    {
      label: 'New Record',
      icon: Plus,
      variant: 'primary' as const,
      onClick: () => console.log('New record')
    }
  ]

  const filterActions = (
    <div className="flex items-center space-x-3">
      <button
        onClick={() => setShowFilters(!showFilters)}
        className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
          showFilters ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }`}
      >
        <Filter className="h-4 w-4 mr-2" />
        Filters
      </button>
      
      <button
        onClick={() => setShowBackendPanel(!showBackendPanel)}
        className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
          showBackendPanel ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }`}
      >
        <Server className="h-4 w-4 mr-2" />
        Backend Tests
      </button>
      
      <button
        onClick={checkBackendStatus}
        className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
          backendStatus === 'online' ? 'bg-green-100 text-green-700' :
          backendStatus === 'offline' ? 'bg-red-100 text-red-700' :
          'bg-yellow-100 text-yellow-700'
        }`}
      >
        <div className={`w-2 h-2 rounded-full mr-2 ${
          backendStatus === 'online' ? 'bg-green-500' :
          backendStatus === 'offline' ? 'bg-red-500' :
          'bg-yellow-500'
        }`} />
        {backendStatus}
      </button>
    </div>
  )

  // Handler for manual override
  const handleOverride = async (record: any) => {
    setOverrideModal({ open: true, record });
  };
  const confirmOverride = async () => {
    if (!overrideModal) return;
    await apiClient.overrideApprovedRecord(overrideModal.record.recordId, userId, overrideReason);
    setOverrideModal(null);
    setOverrideReason('');
    // Refresh lists
    // apiClient.getApprovedRecords().then(res => setApprovedRecords(res.records));
    // apiClient.getReviewQueue().then(res => setReviewQueue(res.reviewQueue));
  };

  // Split records by status for display
  const approvedRecords = records.filter(r => r.status === 'approved');
  const reviewQueue = records.filter(r => r.status === 'flagged');

  return (
    <DashboardLayout>
      <PageHeader
        title="Dashboard"
        description="Monitor and manage your content quality pipeline"
        actions={pageActions}
      />

      {/* Override Modal */}
      {overrideModal && overrideModal.open && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Flag Record for Review</h3>
              <textarea
                value={overrideReason}
                onChange={e => setOverrideReason(e.target.value)}
                placeholder="Reason for flagging this record..."
                rows={3}
                className="w-full p-2 border border-gray-300 rounded-md mb-4"
              />
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setOverrideModal(null)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmOverride}
                  disabled={!overrideReason.trim()}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  Confirm
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <ContentLayout>
        {/* Dashboard Metrics */}
        <DashboardMetrics
          stats={dashboardStats}
          onMetricClick={handleMetricClick}
          loading={loading}
        />

        {/* Filters */}
        {showFilters && (
          <AdvancedFilters
            filters={filters}
            onFiltersChange={setFilters}
            onReset={() => setFilters({})}
          />
        )}

        {/* Approved Records Table */}
        <div className="mt-8">
          <h2 className="text-lg font-semibold mb-2">Approved Records</h2>
          <QualityRecordsTable
            data={approvedRecords}
            loading={loading || isApproving}
            onRecordClick={handleRecordClick}
            onOverride={handleOverride}
            onBulkAction={handleBulkAction}
          />
        </div>

        {/* Review Queue Table */}
        <div className="mt-8">
          <h2 className="text-lg font-semibold mb-2">Review Queue</h2>
          <QualityRecordsTable
            data={reviewQueue}
            loading={loading || isApproving}
            onRecordClick={handleRecordClick}
            onOverride={handleOverride}
            onBulkAction={handleBulkAction}
          />
        </div>
      </ContentLayout>

      {/* Record Detail Modal */}
      <RecordDetailModal
        record={selectedRecord}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onUpdate={handleUpdateRecord}
        onReprocess={handleReprocessRecord}
      />
    </DashboardLayout>
  );
}
