'use client';

import { useState } from 'react';
import { apiClient, ChunkIngestRequest } from '../api';

export default function TestPage() {
  const [testResult, setTestResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const testChunk: ChunkIngestRequest = {
    record_id: "test-001",
    document_text: "This is a comprehensive guide about machine learning algorithms and their applications in data science. The document covers various topics including supervised learning, unsupervised learning, and deep learning techniques.",
    tags: ["machine learning", "algorithms", "data science", "AI"],
    source_connector: "SharePoint",
    file_id: "test-file-001"
  };

  const runTest = async () => {
    setLoading(true);
    setError(null);
    setTestResult(null);

    try {
      // Test 1: Health check
      const health = await apiClient.getHealth();
      
      // Test 2: Stats
      const stats = await apiClient.getStats();
      
      // Test 3: Ingest a chunk
      const ingestResult = await apiClient.ingestChunk(testChunk);
      
      // Test 4: Rules check
      const rulesResult = await apiClient.checkRules(testChunk);
      
      // Test 5: LLM analysis
      const llmResult = await apiClient.analyzeLLM(testChunk);
      
      // Test 6: Get records
      const records = await apiClient.getRecords();

      setTestResult({
        health,
        stats,
        ingestResult,
        rulesResult,
        llmResult,
        records
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Test failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">API Test Page</h1>
          
          <div className="mb-6">
            <button
              onClick={runTest}
              disabled={loading}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Running Tests...' : 'Run API Tests'}
            </button>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <h3 className="text-sm font-medium text-red-800">Test Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          )}

          {testResult && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-900">Test Results</h2>
              
              {/* Health Check */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">Health Check</h3>
                <pre className="text-sm text-gray-700 bg-white p-2 rounded border">
                  {JSON.stringify(testResult.health, null, 2)}
                </pre>
              </div>

              {/* Stats */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">System Stats</h3>
                <pre className="text-sm text-gray-700 bg-white p-2 rounded border">
                  {JSON.stringify(testResult.stats, null, 2)}
                </pre>
              </div>

              {/* Ingest Result */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">Ingest Result</h3>
                <pre className="text-sm text-gray-700 bg-white p-2 rounded border">
                  {JSON.stringify(testResult.ingestResult, null, 2)}
                </pre>
              </div>

              {/* Rules Check */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">Rules Check</h3>
                <pre className="text-sm text-gray-700 bg-white p-2 rounded border">
                  {JSON.stringify(testResult.rulesResult, null, 2)}
                </pre>
              </div>

              {/* LLM Analysis */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">LLM Analysis</h3>
                <pre className="text-sm text-gray-700 bg-white p-2 rounded border">
                  {JSON.stringify(testResult.llmResult, null, 2)}
                </pre>
              </div>

              {/* Records */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">Records</h3>
                <pre className="text-sm text-gray-700 bg-white p-2 rounded border">
                  {JSON.stringify(testResult.records, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 