'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, Clock, Zap, TrendingUp, Server, Play, RefreshCw } from 'lucide-react';

interface ApiResponse {
  status: 'success' | 'error';
  data?: any;
  error?: string;
  timestamp?: string;
  processing_time?: number;
}

interface TestResult {
  endpoint: string;
  status: 'success' | 'error' | 'pending';
  response?: any;
  processing_time?: number;
  timestamp: string;
}

export default function ApiTestInterface() {
  const [selectedEndpoint, setSelectedEndpoint] = useState<string>('');
  const [requestPayload, setRequestPayload] = useState<string>('');
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [serverStatus, setServerStatus] = useState<'online' | 'offline' | 'checking'>('checking');

  const apiEndpoints = {
    'Content Ingestion': {
      '/ingest': {
        method: 'POST',
        description: 'Ingest content for quality analysis',
        samplePayload: JSON.stringify({
          "record_id": "test_001",
          "content": "Enterprise software development requires careful consideration of scalability, maintainability, and security best practices.",
          "tags": ["software-development", "enterprise", "best-practices"],
          "source_connector": "confluence",
          "metadata": {
            "author": "Tech Team",
            "department": "Engineering"
          }
        }, null, 2)
      }
    },
    'Quality Analysis': {
      '/rules/check': {
        method: 'POST',
        description: 'Run rules engine validation checks',
        samplePayload: JSON.stringify({
          "document_text": "API documentation for user authentication service. Handles login, registration, password reset, and session management.",
          "tags": ["api", "authentication", "security", "documentation"],
          "source_connector": "confluence"
        }, null, 2)
      },
      '/llm/analyze': {
        method: 'POST',
        description: 'Run LLM-based quality analysis',
        samplePayload: JSON.stringify({
          "content": "Marketing strategy for Q1 2024 focusing on digital transformation initiatives and customer acquisition.",
          "tags": ["marketing", "strategy", "digital-transformation"],
          "context": {
            "source": "strategy-docs",
            "department": "Marketing"
          }
        }, null, 2)
      }
    },
    'Advanced Analysis': {
      '/llm/analyze-custom': {
        method: 'POST',
        description: 'Custom LLM analysis with specific prompts',
        samplePayload: JSON.stringify({
          "content": "Database migration plan for moving from MySQL to PostgreSQL with minimal downtime.",
          "tags": ["database", "migration", "postgresql"],
          "custom_prompt": "Analyze this technical plan for completeness and risk assessment.",
          "constraints": [
            {
              "id": "technical_completeness",
              "name": "Technical Completeness",
              "enabled": true,
              "weight": 0.4
            }
          ]
        }, null, 2)
      },
      '/llm/analyze-cot': {
        method: 'POST',
        description: 'Chain-of-thought analysis for complex content',
        samplePayload: JSON.stringify({
          "content": "AI implementation plan for customer support automation using NLP and machine learning.",
          "tags": ["ai", "nlp", "automation", "customer-support"],
          "analysis_type": "chain_of_thought"
        }, null, 2)
      }
    },
    'System Health': {
      '/health': {
        method: 'GET',
        description: 'Check system health and status',
        samplePayload: ''
      },
      '/metrics': {
        method: 'GET',
        description: 'Get performance metrics',
        samplePayload: ''
      }
    }
  };

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

  useEffect(() => {
    checkServerStatus();
    // Check server status every 30 seconds
    const interval = setInterval(checkServerStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkServerStatus = async () => {
    setServerStatus('checking');
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        setServerStatus('online');
      } else {
        setServerStatus('offline');
      }
    } catch (error) {
      setServerStatus('offline');
    }
  };

  const handleEndpointChange = (value: string) => {
    setSelectedEndpoint(value);
    
    // Find the sample payload for the selected endpoint
    for (const category of Object.values(apiEndpoints)) {
      if (category[value as keyof typeof category]) {
        setRequestPayload(category[value as keyof typeof category].samplePayload);
        break;
      }
    }
  };

  const executeTest = async () => {
    if (!selectedEndpoint) return;
    
    setIsLoading(true);
    const startTime = Date.now();
    
    try {
      // Find endpoint details
      let endpointDetails = null;
      for (const category of Object.values(apiEndpoints)) {
        if (category[selectedEndpoint as keyof typeof category]) {
          endpointDetails = category[selectedEndpoint as keyof typeof category];
          break;
        }
      }
      
      if (!endpointDetails) throw new Error('Endpoint not found');
      
      const requestOptions: RequestInit = {
        method: endpointDetails.method,
        headers: { 'Content-Type': 'application/json' },
      };
      
      if (endpointDetails.method === 'POST' && requestPayload.trim()) {
        requestOptions.body = requestPayload;
      }
      
      const response = await fetch(`${API_BASE_URL}${selectedEndpoint}`, requestOptions);
      const data = await response.json();
      const processingTime = Date.now() - startTime;
      
      const result: TestResult = {
        endpoint: selectedEndpoint,
        status: response.ok ? 'success' : 'error',
        response: data,
        processing_time: processingTime,
        timestamp: new Date().toISOString()
      };
      
      setTestResults(prev => [result, ...prev.slice(0, 9)]); // Keep last 10 results
      
    } catch (error) {
      const result: TestResult = {
        endpoint: selectedEndpoint,
        status: 'error',
        response: { error: error instanceof Error ? error.message : 'Unknown error' },
        processing_time: Date.now() - startTime,
        timestamp: new Date().toISOString()
      };
      
      setTestResults(prev => [result, ...prev.slice(0, 9)]);
    } finally {
      setIsLoading(false);
    }
  };

  const loadSampleRequest = (type: string) => {
    const samples = {
      'good_content': JSON.stringify({
        "record_id": "sample_good_001",
        "content": "Comprehensive guide to microservices architecture covering service design patterns, inter-service communication, data management strategies, deployment automation, monitoring and observability, fault tolerance mechanisms, and security considerations for enterprise-scale distributed systems.",
        "tags": ["microservices", "architecture", "enterprise", "distributed-systems", "scalability"],
        "source_connector": "confluence",
        "metadata": {
          "author": "Architecture Team",
          "department": "Engineering",
          "document_type": "technical-guide"
        }
      }, null, 2),
      
      'problematic_content': JSON.stringify({
        "record_id": "sample_bad_001",
        "content": "document content information data file general misc",
        "tags": ["document", "content", "information", "data", "file", "general", "misc", "test"],
        "source_connector": "sharepoint"
      }, null, 2),
      
      'custom_analysis': JSON.stringify({
        "content": "Security incident response plan covering threat detection, containment procedures, forensic analysis, stakeholder communication, and recovery protocols.",
        "tags": ["security", "incident-response", "cybersecurity"],
        "custom_prompt": "Analyze this security plan for completeness, clarity, and operational readiness.",
        "constraints": [
          {
            "id": "completeness",
            "name": "Plan Completeness",
            "enabled": true,
            "weight": 0.4
          },
          {
            "id": "clarity",
            "name": "Operational Clarity",
            "enabled": true,
            "weight": 0.3
          }
        ]
      }, null, 2)
    };
    
    setRequestPayload(samples[type as keyof typeof samples] || '');
  };

  const clearResults = () => {
    setTestResults([]);
  };

  const renderTestResult = (result: TestResult) => {
    const statusIcon = result.status === 'success' ? 
      <CheckCircle2 className="h-4 w-4 text-green-500" /> :
      <XCircle className="h-4 w-4 text-red-500" />;
    
    const statusColor = result.status === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200';
    
    return (
      <Card key={`${result.endpoint}-${result.timestamp}`} className={`mb-3 ${statusColor}`}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {statusIcon}
              <span className="font-medium">{result.endpoint}</span>
              <Badge variant={result.status === 'success' ? 'default' : 'destructive'}>
                {result.status}
              </Badge>
            </div>
            <div className="flex items-center gap-2 text-sm text-black">
              <Clock className="h-3 w-3" />
              {result.processing_time}ms
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="text-xs text-black mb-2">
            {new Date(result.timestamp).toLocaleString()}
          </div>
          <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-40">
            {JSON.stringify(result.response, null, 2)}
          </pre>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Server Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5" />
                API Server Status
              </CardTitle>
              <CardDescription>Backend server connectivity and health</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={checkServerStatus} disabled={serverStatus === 'checking'}>
              <RefreshCw className={`h-4 w-4 mr-2 ${serverStatus === 'checking' ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${
              serverStatus === 'online' ? 'bg-green-500' : 
              serverStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500'
            }`} />
            <span className="capitalize font-medium text-black">{serverStatus}</span>
            <span className="text-sm text-black">
              {serverStatus === 'online' ? API_BASE_URL : 
               serverStatus === 'offline' ? 'Unable to connect to backend' :
               'Checking connection...'}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* API Testing Interface */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            API Testing Interface
          </CardTitle>
          <CardDescription>
            Test API endpoints directly with custom payloads. Perfect for Postman-style testing.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Endpoint Selection */}
          <div>
            <label className="block text-sm font-bold mb-2 text-black">Select API Endpoint</label>
            <Select value={selectedEndpoint} onValueChange={handleEndpointChange}>
              <SelectTrigger>
                <SelectValue placeholder="Choose an endpoint to test" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(apiEndpoints).map(([category, endpoints]) => (
                  <div key={category}>
                    <div className="px-2 py-1 text-sm font-semibold text-black">{category}</div>
                    {Object.entries(endpoints).map(([endpoint, details]) => (
                      <SelectItem key={endpoint} value={endpoint}>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            {details.method}
                          </Badge>
                          {endpoint}
                        </div>
                      </SelectItem>
                    ))}
                  </div>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Sample Request Buttons */}
          <div>
            <label className="block text-sm font-bold mb-2 text-black">Quick Load Sample</label>
            <div className="flex gap-2 flex-wrap">
              <button className="px-3 py-2 text-sm font-medium text-black bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors">
                Good Content
              </button>
              <button className="px-3 py-2 text-sm font-medium text-black bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors">
                Problematic Content
              </button>
              <button className="px-3 py-2 text-sm font-medium text-black bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors">
                Custom Analysis
              </button>
            </div>
          </div>

          {/* Request Payload */}
          <div>
            <label className="block text-sm font-bold mb-2 text-black">Request Payload (JSON)</label>
            <Textarea
              value={requestPayload}
              onChange={(e) => setRequestPayload(e.target.value)}
              placeholder="Enter your JSON payload here..."
              className="min-h-32 font-mono text-sm"
            />
          </div>

          {/* Execute Button */}
          <div className="flex gap-2">
            <button 
              onClick={executeTest} 
              disabled={!selectedEndpoint || isLoading || serverStatus !== 'online'}
              className="px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                  Testing...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4" />
                  Execute Test
                </>
              )}
            </button>
            
            {testResults.length > 0 && (
              <button className="px-4 py-2 text-black bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors" onClick={clearResults}>
                Clear Results
              </button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Test Results */}
      {testResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Test Results ({testResults.length})
            </CardTitle>
            <CardDescription>
              Real-time API responses and performance metrics
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {testResults.map(renderTestResult)}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 