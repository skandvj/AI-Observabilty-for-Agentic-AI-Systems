// API client for connecting to the Indexing QA backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChunkIngestRequest {
  record_id: string;
  document_text: string;
  tags: string[];
  source_connector: 'SharePoint' | 'Confluence' | 'Notion' | 'GDrive';
  file_id: string;
  created_at?: string;
}

export interface QualityCheckResult {
  check_name: string;
  status: 'pass' | 'fail' | 'pending_review';
  confidence_score: number;
  failure_reason?: string;
  check_metadata?: Record<string, any>;
  
  // Additional fields for detailed quality check information
  type?: string;  // e.g., "stopwords detection", "tag validation", "llm_semantic_validation"
  severity?: string;  // e.g., "low", "medium", "high", "critical"
  description?: string;  // Detailed description of the check
  suggestion?: string;  // Suggested fix or improvement
  autoFixable?: boolean;  // Whether this issue can be auto-fixed
  category?: string;  // e.g., "tags", "content", "metadata", "llm"
  reasoning?: string;  // LLM reasoning for the decision
  issues?: Array<{tag: string; problem: string}>;  // List of specific issues found
  llm_assessment?: string;  // LLM's overall assessment
  llm_reasoning?: string;  // LLM's detailed reasoning
  issues_found?: number;  // Number of issues found
  processing_time_ms?: number;  // Processing time for this check
}

export interface ChunkAnalysisResponse {
  trace_id: string;
  record_id: string;
  overall_status: 'pass' | 'fail' | 'pending_review';
  quality_checks: QualityCheckResult[];
  processing_time_ms: number;
  created_at: string;
}

export interface SystemStats {
  total_processed: number;
  passed: number;
  failed: number;
  pass_rate: number;
  avg_processing_time_ms: number;
  total_chunks: number;
  llm_requests: number;
  llm_cost_usd: number;
}

export interface ChunkRecord {
  id: string;
  trace_id: string;
  record_id: string;
  source_connector: string;
  overall_status: 'pass' | 'fail' | 'pending_review';
  created_at: string;
  processed_at: string;
  quality_checks: QualityCheckResult[];
}

export interface RecordsResponse {
  records: ChunkRecord[];
  total_count: number;
}

export interface AnalyticsData {
  qualityTrendData: Array<{
    date: string
    processed: number
    avg_quality: number
  }>
  sourcePerformanceData: Array<{
    source: string
    processed: number
    avg_quality: number
  }>
  issueBreakdownData: Array<{
    name: string
    value: number
    color: string
  }>
  companyMetricsData: Array<{
    company: string
    records: number | null
    avgQuality: number | null
    issues: number | null
    cost: number | null
  }>
  topFailureReasons: Array<{
    reason: string
    count: number
    percentage: number
  }>
  today: {
    total_processed: number | null
    avg_quality_score: number | null
    total_issues: number | null
  }
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Health check
  async getHealth(): Promise<any> {
    return this.request('/health');
  }

  // Get system statistics
  async getStats(): Promise<SystemStats> {
    return this.request('/stats');
  }

  // Get all records
  async getRecords(): Promise<RecordsResponse> {
    return this.request('/records');
  }

  // Ingest a chunk
  async ingestChunk(chunk: ChunkIngestRequest): Promise<ChunkAnalysisResponse> {
    return this.request('/ingest', {
      method: 'POST',
      body: JSON.stringify(chunk),
    });
  }

  // Check rules only
  async checkRules(chunk: ChunkIngestRequest): Promise<any> {
    return this.request('/rules/check', {
      method: 'POST',
      body: JSON.stringify(chunk),
    });
  }

  // LLM analysis
  async analyzeLLM(chunk: ChunkIngestRequest): Promise<any> {
    return this.request('/llm/analyze', {
      method: 'POST',
      body: JSON.stringify(chunk),
    });
  }

  // Self test
  async runTest(): Promise<any> {
    return this.request('/test');
  }

  async getDashboardAnalytics(): Promise<AnalyticsData> {
    const response = await this.request<AnalyticsData>('/analytics/dashboard')
    return response
  }

  async getIssues() {
    const response = await this.request<{issues: any[]}>('/issues')
    return response.issues
  }

  async autoFixIssue(issueId: string) {
    const response = await this.request<any>(`/issues/${issueId}/auto-fix`)
    return response
  }

  async getDeadLetters() {
    const response = await this.request<{dead_letters: any[]}>('/dead-letters')
    return response.dead_letters
  }

  async retryDeadLetter(letterId: string) {
    const response = await this.request<any>(`/dead-letters/${letterId}/retry`)
    return response
  }

  async submitFeedback(feedback: any) {
    const response = await this.request<any>('/feedback', feedback)
    return response
  }

  // Get tag suggestions from LLM
  async getTagSuggestions(content: string, currentTags: string[] = []): Promise<{
    success: boolean;
    suggestions: string[];
    confidence_score: number;
    reasoning: string;
  }> {
    return this.request('/llm/tag-suggestions', {
      method: 'POST',
      body: JSON.stringify({
        content,
        current_tags: currentTags
      }),
    });
  }

  // Custom LLM analysis
  async customLLMAnalysis(request: {
    trace_id?: string;
    content: string;
    tags: string[];
    custom_prompt: string;
    constraints?: any[];
    quality_weights?: Record<string, number>;
    context?: any;
  }): Promise<any> {
    return this.request('/llm/custom-analyze', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Approve a flagged record
  async approveFlaggedRecord(recordId: string, userId: string) {
    return this.request(`/records/approve/${recordId}`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  }
}

export const apiClient = new ApiClient(); 