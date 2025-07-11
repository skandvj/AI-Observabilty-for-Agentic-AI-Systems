'use client'

import React, { useState, useRef } from 'react'
import { 
  X, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  User, 
  Calendar,
  FileText,
  Tag,
  Edit,
  Save,
  RotateCcw,
  ExternalLink,
  Copy,
  Download,
  Brain,
  Settings,
  MessageSquare,
  Zap,
  Shield,
  Lightbulb
} from 'lucide-react'
import { QualityRecord, QualityIssue } from '@/types'
import { apiClient } from '../../app/api';

interface RecordDetailModalProps {
  record: QualityRecord | null
  isOpen: boolean
  onClose: () => void
  onUpdate?: (record: QualityRecord) => void
  onReprocess?: (recordId: string, content: string, tags: string[]) => void
  onRecordUpdated?: () => void
}

export default function RecordDetailModal({ 
  record, 
  isOpen, 
  onClose, 
  onUpdate,
  onReprocess,
  onRecordUpdated
}: RecordDetailModalProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'content' | 'quality' | 'llm-custom' | 'review'>('overview')
  const [isEditing, setIsEditing] = useState(false)
  const [editedContent, setEditedContent] = useState('')
  const [editedTags, setEditedTags] = useState<string[]>([])
  const [reviewDecision, setReviewDecision] = useState<'approve' | 'reject' | 'revise' | ''>('')
  const [reviewComments, setReviewComments] = useState('')
  const [isSubmittingReview, setIsSubmittingReview] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [reviewSubmitted, setReviewSubmitted] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  
  // LLM Custom state
  const [customPrompt, setCustomPrompt] = useState('')
  const [customResponse, setCustomResponse] = useState('')
  const [isCustomAnalyzing, setIsCustomAnalyzing] = useState(false)

  // Initialize editing state when record changes
  React.useEffect(() => {
    if (record) {
      setEditedContent(record.content)
      setEditedTags([...record.tags])
      setReviewDecision('')
      setReviewComments('')
      setIsEditing(false)
      setCustomPrompt('')
      setCustomResponse('')
    }
  }, [record])

  if (!isOpen || !record) return null

  const handleSaveContent = async () => {
    try {
      const updatedRecord = {
        ...record,
        content: editedContent,
        tags: editedTags,
        updatedAt: new Date().toISOString()
      }
      
      onUpdate?.(updatedRecord)
      onRecordUpdated?.() // Trigger refresh of records list
      setIsEditing(false)
    } catch (error) {
      console.error('Error saving content:', error)
    }
  }

  const handleReprocess = async () => {
    try {
      await onReprocess?.(record.id, editedContent, editedTags)
      onRecordUpdated?.() // Trigger refresh of records list
      setIsEditing(false)
    } catch (error) {
      console.error('Error reprocessing:', error)
    }
  }

  const handleSubmitReview = async () => {
    setIsSubmittingReview(true);
    setReviewError(null);
    try {
      await apiClient.submitFeedback({
        trace_id: record.traceId,
        decision: reviewDecision,
        comments: reviewComments,
        reviewer_id: 'current_user', // Replace with actual user ID if available
        reviewed_at: new Date().toISOString(),
      });
      setReviewSubmitted(true);
      onRecordUpdated?.() // Trigger refresh of records list
      setTimeout(() => {
        setReviewSubmitted(false);
        onClose();
      }, 1500);
    } catch (error) {
      setReviewError('Failed to submit review.');
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const handleCustomAnalysis = async () => {
    if (!customPrompt.trim()) return;
    
    setIsCustomAnalyzing(true);
    try {
      // This would call your custom LLM endpoint
      const response = await apiClient.customLLMAnalysis({
        trace_id: record.traceId,
        prompt: customPrompt,
        content: record.content,
        context: {
          record_id: record.recordId,
          quality_score: record.qualityScore,
          issues: record.issues
        }
      });
      setCustomResponse(response.analysis || 'Analysis completed');
    } catch (error) {
      setCustomResponse('Error: Failed to analyze with custom prompt');
    } finally {
      setIsCustomAnalyzing(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved': return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'rejected': return <XCircle className="h-5 w-5 text-red-500" />
      case 'flagged': return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      case 'under_review': return <Clock className="h-5 w-5 text-blue-500" />
      default: return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const getIssueIcon = (issueType: string) => {
    switch (issueType) {
      case 'generic_tags': return <Tag className="h-4 w-4 text-yellow-500" />
      case 'content_quality': return <FileText className="h-4 w-4 text-red-500" />
      case 'missing_context': return <AlertTriangle className="h-4 w-4 text-orange-500" />
      case 'pii_detected': return <User className="h-4 w-4 text-red-600" />
      case 'duplicate_content': return <Copy className="h-4 w-4 text-blue-500" />
      default: return <AlertTriangle className="h-4 w-4 text-gray-500" />
    }
  }

  const formatIssueType = (issueType: string) => {
    return issueType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon(record.status)}
            <div>
              <h2 className="text-xl font-bold text-gray-900">Record Details</h2>
              <p className="text-sm text-gray-500">{record.recordId}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full"
          >
            <X className="h-6 w-6 text-gray-400" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 px-6">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'overview', label: 'Overview', icon: FileText },
              { id: 'content', label: 'Content', icon: Edit },
              { id: 'quality', label: 'Quality Checks', icon: Shield },
              { id: 'llm-custom', label: 'LLM Custom', icon: Lightbulb },
              { id: 'review', label: 'Review', icon: MessageSquare }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Basic Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-500">Record ID:</span>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-900">{record.recordId}</span>
                        <button onClick={() => copyToClipboard(record.recordId)} className="p-1 hover:bg-gray-200 rounded">
                          <Copy className="h-3 w-3 text-gray-400" />
                        </button>
                      </div>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-500">Company:</span>
                      <span className="text-sm text-gray-900">{record.companyName}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-500">Source:</span>
                      <span className="text-sm text-gray-900">{record.sourceConnectorName}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-500">Created:</span>
                      <span className="text-sm text-gray-900">
                        {new Date(record.createdAt).toLocaleDateString()} {new Date(record.createdAt).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-500">Updated:</span>
                      <span className="text-sm text-gray-900">
                        {new Date(record.updatedAt).toLocaleDateString()} {new Date(record.updatedAt).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Quality Metrics</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-500">Quality Score:</span>
                      <span className={`text-sm font-medium ${
                        record.qualityScore >= 90 ? 'text-green-600' :
                        record.qualityScore >= 70 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {record.qualityScore}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-500">Confidence:</span>
                      <span className="text-sm text-gray-900">{(record.confidenceScore * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-500">Priority:</span>
                      <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                        record.priority === 'critical' ? 'bg-red-100 text-red-800' :
                        record.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                        record.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {record.priority.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-500">Status:</span>
                      <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                        record.status === 'approved' ? 'bg-green-100 text-green-800' :
                        record.status === 'rejected' ? 'bg-red-100 text-red-800' :
                        record.status === 'flagged' ? 'bg-yellow-100 text-yellow-800' :
                        record.status === 'under_review' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {record.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-500">Issues:</span>
                      <span className="text-sm text-gray-900">{record.issues.length}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tags */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Content Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {record.tags.map((tag, index) => (
                    <span 
                      key={index}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      <Tag className="h-3 w-3 mr-1" />
                      {tag}
                    </span>
                  ))}
                  {record.tags.length === 0 && (
                    <span className="text-sm text-gray-500 italic">No tags</span>
                  )}
                </div>
              </div>

              {/* Metadata */}
              {record.metadata && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Metadata</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(record.metadata).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-sm font-medium text-gray-500 capitalize">
                          {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}:
                        </span>
                        <span className="text-sm text-gray-900">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'content' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Document Content & Tags</h3>
                <div className="flex items-center space-x-2">
                  {isEditing ? (
                    <>
                      <button
                        onClick={() => {
                          setEditedContent(record.content)
                          setEditedTags([...record.tags])
                          setIsEditing(false)
                        }}
                        className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
                      >
                        <RotateCcw className="h-4 w-4 mr-1 inline" />
                        Cancel
                      </button>
                      <button
                        onClick={handleSaveContent}
                        className="px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                      >
                        <Save className="h-4 w-4 mr-1 inline" />
                        Save
                      </button>
                      <button
                        onClick={handleReprocess}
                        className="px-3 py-2 text-sm bg-green-600 text-white rounded-md hover:bg-green-700"
                      >
                        <RotateCcw className="h-4 w-4 mr-1 inline" />
                        Save & Reprocess
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                      <Edit className="h-4 w-4 mr-1 inline" />
                      Edit Content & Tags
                    </button>
                  )}
                </div>
              </div>

              {/* Content Editor */}
              <div className="border border-gray-300 rounded-lg">
                <div className="bg-gray-50 px-4 py-2 border-b border-gray-300 flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Document Text</span>
                  <span className="text-xs text-gray-500">
                    {isEditing ? editedContent.length : record.content.length} characters
                  </span>
                </div>
                <div className="p-4">
                  {isEditing ? (
                    <textarea
                      ref={textareaRef}
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      className="w-full h-64 p-3 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter document content..."
                    />
                  ) : (
                    <div className="whitespace-pre-wrap text-sm text-gray-900 max-h-64 overflow-y-auto p-3 bg-gray-50 rounded-md">
                      {record.content}
                    </div>
                  )}
                </div>
              </div>

              {/* Tags Editor */}
              <div className="border border-gray-300 rounded-lg">
                <div className="bg-gray-50 px-4 py-2 border-b border-gray-300 flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Content Tags</span>
                  <span className="text-xs text-gray-500">
                    {isEditing ? editedTags.length : record.tags.length} tags
                  </span>
                </div>
                <div className="p-4">
                  {isEditing ? (
                    <div className="space-y-3">
                      <div className="flex flex-wrap gap-2">
                        {editedTags.map((tag, index) => (
                          <div key={index} className="flex items-center bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm">
                            <Tag className="h-3 w-3 mr-1" />
                            {tag}
                            <button
                              onClick={() => setEditedTags(editedTags.filter((_, i) => i !== index))}
                              className="ml-2 text-blue-600 hover:text-blue-800"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </div>
                        ))}
                      </div>
                      <div className="flex space-x-2">
                        <input
                          type="text"
                          placeholder="Add new tag..."
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                              setEditedTags([...editedTags, e.currentTarget.value.trim()])
                              e.currentTarget.value = ''
                            }
                          }}
                        />
                        <button
                          onClick={(e) => {
                            const input = e.currentTarget.previousElementSibling as HTMLInputElement
                            if (input.value.trim()) {
                              setEditedTags([...editedTags, input.value.trim()])
                              input.value = ''
                            }
                          }}
                          className="px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                        >
                          Add
                        </button>
                        <button
                          onClick={async () => {
                            try {
                              const suggestions = await apiClient.getTagSuggestions(editedContent, editedTags)
                              if (suggestions.success && suggestions.suggestions.length > 0) {
                                // Show suggestions in a simple way - could be enhanced with a modal
                                alert(`Tag Suggestions:\n${suggestions.suggestions.join('\n')}`)
                              }
                            } catch (error) {
                              console.error('Error getting tag suggestions:', error)
                            }
                          }}
                          className="px-3 py-2 text-sm bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
                        >
                          <Lightbulb className="h-4 w-4 mr-1 inline" />
                          AI Suggestions
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {record.tags.map((tag, index) => (
                        <span 
                          key={index}
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          <Tag className="h-3 w-3 mr-1" />
                          {tag}
                        </span>
                      ))}
                      {record.tags.length === 0 && (
                        <span className="text-sm text-gray-500 italic">No tags</span>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* LLM Tag Suggestions */}
              {record.llmSuggestions && record.llmSuggestions.length > 0 && (
                <div className="border border-yellow-300 rounded-lg bg-yellow-50">
                  <div className="bg-yellow-100 px-4 py-2 border-b border-yellow-300">
                    <span className="text-sm font-medium text-yellow-800">AI Tag Suggestions</span>
                  </div>
                  <div className="p-4">
                    <ul className="space-y-2">
                      {record.llmSuggestions.map((suggestion, index) => (
                        <li key={index} className="flex items-start text-sm text-yellow-800">
                          <Lightbulb className="h-4 w-4 mr-2 mt-0.5 text-yellow-600" />
                          <span>{suggestion}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'quality' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">Quality Check Results</h3>
              {/* Quality Score Overview */}
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-md font-medium text-blue-900">Quality Analysis</h4>
                  <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${record.status === 'approved' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{record.status || '-'}</span>
                </div>
                {/* Compute confidence values from real-time quality_checks or issues */}
                {(() => {
                  const checks = (record.quality_checks || record.issues || []) as any[];
                  const llmChecks = checks.filter(qc => qc.category === 'llm');
                  const rulesChecks = checks.filter(qc => qc.category !== 'llm');
                  // Use actual confidence scores from record, fallback to calculated averages
                  const llmConfidence = record.llm_confidence ?? (llmChecks.length > 0 ? llmChecks.reduce((sum, qc) => sum + (qc.confidence_score ?? qc.confidence ?? 0), 0) / llmChecks.length : 0);
                  const rulesConfidence = record.rules_engine_confidence ?? (rulesChecks.length > 0 ? rulesChecks.reduce((sum, qc) => sum + (qc.confidence_score ?? qc.confidence ?? 0), 0) / rulesChecks.length : 0);
                  return (
                    <div className="flex flex-col md:flex-row gap-6">
                      {/* LLM Progress Bar */}
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-medium text-blue-800">LLM Confidence</span>
                          <span className="text-xs text-blue-800 font-mono">{(llmConfidence * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-blue-100 rounded-full h-2.5 mb-2">
                          <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${llmConfidence * 100}%` }}></div>
                        </div>
                      </div>
                      {/* Rules Engine Progress Bar */}
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-medium text-blue-800">Rules Engine Confidence</span>
                          <span className="text-xs text-blue-800 font-mono">{(rulesConfidence * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-blue-100 rounded-full h-2.5 mb-2">
                          <div className="bg-green-600 h-2.5 rounded-full" style={{ width: `${rulesConfidence * 100}%` }}></div>
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
              {/* Grouped Quality Checks - show only real-time backend fields */}
              <div className="flex flex-col md:flex-row gap-8">
                {/* LLM Checks (left) */}
                <div className="flex-1 min-w-[400px]">
                  <h4 className="text-md font-semibold mb-2">LLM Checks</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-xs border">
                      <thead>
                        <tr className="bg-gray-100">
                          <th className="px-2 py-1 text-left">Check</th>
                          <th className="px-2 py-1 text-left">Status</th>
                          <th className="px-2 py-1 text-left">Confidence</th>
                          <th className="px-2 py-1 text-left">Description</th>
                          <th className="px-2 py-1 text-left">Suggestion</th>
                          <th className="px-2 py-1 text-left">Category</th>
                          <th className="px-2 py-1 text-left">Auto-fixable</th>
                          <th className="px-2 py-1 text-left">Processing Time</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(record.quality_checks || []).filter((qc: any) => 
                          qc.category === 'llm' || 
                          qc.check_name === 'llm_semantic_validation' ||
                          qc.type === 'llm_semantic_validation'
                        ).map((qc: any, idx: number) => (
                          <tr key={qc.check_name + idx} className={qc.status === 'PASS' || qc.status === 'pass' ? 'bg-green-50' : 'bg-red-50'}>
                            <td className="px-2 py-1 font-mono">{qc.check_name || qc.type || 'LLM Check'}</td>
                            <td className="px-2 py-1">
                              <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${(qc.status === 'PASS' || qc.status === 'pass') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{qc.status || '-'}</span>
                            </td>
                            <td className="px-2 py-1">{((qc.confidence_score ?? qc.confidence ?? 0) * 100).toFixed(0)}%</td>
                            <td className="px-2 py-1">{qc.description || qc.failure_reason || '-'}</td>
                            <td className="px-2 py-1">{qc.suggestion || '-'}</td>
                            <td className="px-2 py-1">{qc.category || 'llm'}</td>
                            <td className="px-2 py-1">{qc.autoFixable !== undefined ? (qc.autoFixable ? 'Yes' : 'No') : '-'}</td>
                            <td className="px-2 py-1">{qc.processing_time_ms ?? qc.processingTimeMs ?? '-'}</td>
                          </tr>
                        ))}
                        {(record.quality_checks || []).filter((qc: any) => 
                          qc.category === 'llm' || 
                          qc.check_name === 'llm_semantic_validation' ||
                          qc.type === 'llm_semantic_validation'
                        ).length === 0 && (
                          <tr>
                            <td colSpan={8} className="px-2 py-4 text-center text-gray-500">No LLM checks available</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
                {/* Rules Engine Checks (right) */}
                <div className="flex-1 min-w-[400px]">
                  <h4 className="text-md font-semibold mb-2">Rules Engine Checks</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-xs border">
                      <thead>
                        <tr className="bg-gray-100">
                          <th className="px-2 py-1 text-left">Check</th>
                          <th className="px-2 py-1 text-left">Status</th>
                          <th className="px-2 py-1 text-left">Confidence</th>
                          <th className="px-2 py-1 text-left">Description</th>
                          <th className="px-2 py-1 text-left">Suggestion</th>
                          <th className="px-2 py-1 text-left">Category</th>
                          <th className="px-2 py-1 text-left">Auto-fixable</th>
                          <th className="px-2 py-1 text-left">Processing Time</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(record.quality_checks || []).filter((qc: any) => 
                          qc.category !== 'llm' && 
                          qc.check_name !== 'llm_semantic_validation' &&
                          qc.type !== 'llm_semantic_validation'
                        ).map((qc: any, idx: number) => (
                          <tr key={qc.check_name + idx} className={qc.status === 'PASS' || qc.status === 'pass' ? 'bg-green-50' : 'bg-red-50'}>
                            <td className="px-2 py-1 font-mono">{qc.check_name || qc.type || 'Rules Check'}</td>
                            <td className="px-2 py-1">
                              <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${(qc.status === 'PASS' || qc.status === 'pass') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{qc.status || '-'}</span>
                            </td>
                            <td className="px-2 py-1">{((qc.confidence_score ?? qc.confidence ?? 0) * 100).toFixed(0)}%</td>
                            <td className="px-2 py-1">{qc.description || qc.failure_reason || '-'}</td>
                            <td className="px-2 py-1">{qc.suggestion || '-'}</td>
                            <td className="px-2 py-1">{qc.category || 'rules'}</td>
                            <td className="px-2 py-1">{qc.autoFixable !== undefined ? (qc.autoFixable ? 'Yes' : 'No') : '-'}</td>
                            <td className="px-2 py-1">{qc.processing_time_ms ?? qc.processingTimeMs ?? '-'}</td>
                          </tr>
                        ))}
                        {(record.quality_checks || []).filter((qc: any) => 
                          qc.category !== 'llm' && 
                          qc.check_name !== 'llm_semantic_validation' &&
                          qc.type !== 'llm_semantic_validation'
                        ).length === 0 && (
                          <tr>
                            <td colSpan={8} className="px-2 py-4 text-center text-gray-500">No rules engine checks available</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
              {/* AI Suggestions Section */}
              {(record.llmSuggestions && record.llmSuggestions.length > 0) && (
                <div className="mb-4">
                  <h5 className="text-sm font-medium text-blue-900 mb-2">AI Suggestions</h5>
                  <ul className="space-y-1">
                    {record.llmSuggestions.map((suggestion: string, index: number) => (
                      <li key={index} className="flex items-start text-sm text-blue-800">
                        <span className="mr-2 text-blue-600">•</span>
                        <span>{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {/* LLM Reasoning Section */}
              {record.llmReasoning && (
                <div className="mb-4">
                  <h5 className="text-sm font-medium text-blue-900 mb-2">LLM Reasoning</h5>
                  <div className="bg-blue-50 rounded-md p-3">
                    <p className="text-sm text-blue-800">{record.llmReasoning}</p>
                  </div>
                </div>
              )}
              
              {/* Issues Detected Section */}
              {(record.issues && record.issues.length > 0) && (
                <div className="mb-4">
                  <h5 className="text-sm font-medium text-red-900 mb-2">Issues Detected</h5>
                  <ul className="space-y-2">
                    {record.issues.map((issue: any, index: number) => (
                      <li key={index} className="flex items-start text-sm text-red-800 bg-red-50 rounded-md p-3">
                        <span className="mr-2 text-red-600 mt-0.5">•</span>
                        <div className="flex-1">
                          <div className="font-medium">{issue.description}</div>
                          {issue.suggestion && (
                            <div className="text-red-700 mt-1">
                              <span className="font-medium">Suggestion:</span> {issue.suggestion}
                            </div>
                          )}
                          {issue.confidence && (
                            <div className="text-red-600 text-xs mt-1">
                              Confidence: {(issue.confidence * 100).toFixed(0)}%
                            </div>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {activeTab === 'llm-custom' && (
            <div className="space-y-6">
              <div className="flex items-center space-x-2 mb-4">
                <Lightbulb className="h-5 w-5 text-yellow-500" />
                <h3 className="text-lg font-medium text-gray-900">Custom LLM Analysis</h3>
              </div>
              
              <div className="bg-yellow-50 rounded-lg p-4 mb-6">
                <h4 className="text-md font-medium text-yellow-900 mb-2">Chain of Thought Prompts</h4>
                <p className="text-sm text-yellow-800">
                  Write custom prompts to understand specific issues and get detailed analysis. 
                  Use placeholders like {'{content}'}, {'{issues}'}, {'{quality_score}'} to reference record data.
                </p>
              </div>

              {/* Custom Prompt Input */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Custom Analysis Prompt
                  </label>
                  <textarea
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    placeholder="Enter your custom prompt here. Example: Analyze the content quality issues in {content} and provide specific recommendations for improvement..."
                    className="w-full h-32 p-3 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div className="flex items-center space-x-3">
                  <button
                    onClick={handleCustomAnalysis}
                    disabled={!customPrompt.trim() || isCustomAnalyzing}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    <Brain className="h-4 w-4" />
                    <span>{isCustomAnalyzing ? 'Analyzing...' : 'Run Analysis'}</span>
                  </button>
                  
                  <button
                    onClick={() => {
                      setCustomPrompt('Analyze the quality issues in this content and provide specific recommendations for improvement. Focus on clarity, accuracy, and completeness.')
                    }}
                    className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Load Example
                  </button>
                </div>
              </div>

              {/* Custom Analysis Results */}
              {customResponse && (
                <div className="mt-6">
                  <h4 className="text-md font-medium text-gray-900 mb-3">Analysis Results</h4>
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="bg-gray-50 rounded-md p-3">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{customResponse}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Quick Prompts */}
              <div className="mt-6">
                <h4 className="text-md font-medium text-gray-900 mb-3">Quick Prompts</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {[
                    {
                      title: 'Content Quality Analysis',
                      prompt: 'Analyze the content quality of {content} and identify specific areas for improvement.',
                      icon: FileText
                    },
                    {
                      title: 'Issue Resolution',
                      prompt: 'Given the issues {issues}, provide step-by-step solutions to resolve each problem.',
                      icon: AlertTriangle
                    },
                    {
                      title: 'Tag Optimization',
                      prompt: 'Review the current tags and suggest better, more specific tags for {content}.',
                      icon: Tag
                    },
                    {
                      title: 'Compliance Check',
                      prompt: 'Check {content} for potential compliance issues and suggest improvements.',
                      icon: Shield
                    }
                  ].map((quickPrompt, index) => (
                    <button
                      key={index}
                      onClick={() => setCustomPrompt(quickPrompt.prompt)}
                      className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 text-left"
                    >
                      <div className="flex items-center space-x-2 mb-2">
                        <quickPrompt.icon className="h-4 w-4 text-blue-500" />
                        <span className="text-sm font-medium text-gray-900">{quickPrompt.title}</span>
                      </div>
                      <p className="text-xs text-gray-600 line-clamp-2">{quickPrompt.prompt}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'review' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">Review & Feedback</h3>
              
              {reviewSubmitted ? (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <h4 className="text-lg font-medium text-gray-900">Review Submitted Successfully</h4>
                  <p className="text-sm text-gray-500">Thank you for your feedback.</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Review Decision */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="text-md font-medium text-gray-900 mb-4">Review Decision</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      {[
                        { value: 'approve', label: 'Approve', icon: CheckCircle, color: 'green' },
                        { value: 'reject', label: 'Reject', icon: XCircle, color: 'red' },
                        { value: 'revise', label: 'Needs Revision', icon: AlertTriangle, color: 'yellow' }
                      ].map(({ value, label, icon: Icon, color }) => (
                        <button
                          key={value}
                          onClick={() => setReviewDecision(value as any)}
                          className={`p-4 border-2 rounded-lg flex items-center space-x-3 transition-colors ${
                            reviewDecision === value
                              ? `border-${color}-500 bg-${color}-50`
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <Icon className={`h-5 w-5 ${
                            reviewDecision === value ? `text-${color}-600` : 'text-gray-400'
                          }`} />
                          <span className={`font-medium ${
                            reviewDecision === value ? `text-${color}-900` : 'text-gray-700'
                          }`}>
                            {label}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Review Comments */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="text-md font-medium text-gray-900 mb-4">Review Comments</h4>
                    <textarea
                      value={reviewComments}
                      onChange={(e) => setReviewComments(e.target.value)}
                      placeholder="Provide detailed feedback about this record..."
                      className="w-full h-32 p-3 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  {/* Submit Review */}
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-500">
                      Your review will help improve the quality analysis system.
                    </div>
                    <button
                      onClick={handleSubmitReview}
                      disabled={!reviewDecision || isSubmittingReview}
                      className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isSubmittingReview ? 'Submitting...' : 'Submit Review'}
                    </button>
                  </div>

                  {reviewError && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <p className="text-sm text-red-800">{reviewError}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 flex items-center justify-between bg-gray-50">
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <span>Record ID: {record.recordId}</span>
            <span>•</span>
            <span>Quality Score: {record.qualityScore}%</span>
            <span>•</span>
            <span>{record.issues.length} issues</span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => copyToClipboard(JSON.stringify(record, null, 2))}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
            >
              <Copy className="h-4 w-4 mr-1 inline" />
              Copy JSON
            </button>
            <button
              onClick={() => {
                const blob = new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `record-${record.recordId}.json`
                a.click()
                URL.revokeObjectURL(url)
              }}
              className="px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <Download className="h-4 w-4 mr-1 inline" />
              Export
            </button>
          </div>
        </div>
      </div>
    </div>
  )
} 