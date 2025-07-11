# Indexing QA API Testing Guide

## Quick Start

1. **Start Backend Server:**
   ```bash
   cd backend
   python run_local.py
   ```
   Server runs on: `http://localhost:8000`

2. **Start Frontend Dashboard:**
   ```bash
   cd frontend
   npm run dev
   ```
   Dashboard runs on: `http://localhost:3000`

## API Endpoints

### System Health
- **GET** `/health` - Check server status
- **GET** `/metrics` - Performance metrics

### Content Analysis
- **POST** `/ingest` - Full content ingestion with both rules + LLM
- **POST** `/rules/check` - Fast rules engine validation only  
- **POST** `/llm/analyze` - LLM-based quality analysis
- **POST** `/llm/analyze-custom` - Custom prompts and constraints
- **POST** `/llm/analyze-cot` - Chain-of-thought analysis
- **POST** `/llm/analyze-self-consistency` - Self-consistency validation

## Testing with Postman

### Import Collection
1. Import `Indexing_QA_Postman_Collection.json`
2. Set base URL variable: `http://localhost:8000`
3. Run any request to test

### Test Scenarios

#### ✅ **Good Content Test**
```bash
curl -X POST http://localhost:8000/rules/check \
  -H "Content-Type: application/json" \
  -d '{
    "document_text": "Enterprise software development requires careful consideration of scalability, maintainability, and security best practices. This comprehensive guide covers architectural patterns, code review processes, deployment strategies, monitoring solutions, and performance optimization techniques used by leading technology companies.",
    "tags": ["software-development", "enterprise", "architecture", "best-practices", "scalability"],
    "source_connector": "confluence"
  }'
```

#### ❌ **Problematic Content Test**
```bash
curl -X POST http://localhost:8000/rules/check \
  -H "Content-Type: application/json" \
  -d '{
    "document_text": "document content information data file general misc",
    "tags": ["document", "content", "information", "data", "file", "general", "misc", "test"],
    "source_connector": "sharepoint"
  }'
```

#### 🧠 **LLM Analysis Test**
```bash
curl -X POST http://localhost:8000/llm/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "content": "API documentation for the user authentication service. This service handles user login, registration, password reset, and session management. It supports OAuth 2.0, JWT tokens, and multi-factor authentication.",
    "tags": ["api", "authentication", "security", "documentation"],
    "context": {
      "source": "confluence",
      "author": "Backend Team",
      "department": "Engineering"
    }
  }'
```

## Expected Results

### Rules Engine Response (Good Content)
```json
{
  "record_id": "auto-generated",
  "rules_results": [
    {
      "check_name": "empty_tags",
      "status": "PASS",
      "confidence_score": 1.0,
      "processing_time_ms": 2.1
    },
    {
      "check_name": "tag_count_validation", 
      "status": "PASS",
      "confidence_score": 1.0
    },
    {
      "check_name": "text_quality",
      "status": "PASS",
      "confidence_score": 1.0
    }
  ],
  "overall_quality_score": 0.95,
  "processing_time_ms": 15.4
}
```

### Rules Engine Response (Problematic Content)
```json
{
  "record_id": "auto-generated",
  "rules_results": [
    {
      "check_name": "stopwords_detection",
      "status": "FAIL",
      "confidence_score": 0.875,
      "failure_reason": "Too many generic tags: 87.5% are stopwords"
    },
    {
      "check_name": "tag_text_relevance",
      "status": "FAIL",
      "confidence_score": 0.7,
      "failure_reason": "Low tag-text relevance: 12.5%"
    }
  ],
  "overall_quality_score": 0.23,
  "flagged_for_review": true
}
```

### LLM Analysis Response
```json
{
  "record_id": "auto-generated",
  "llm_analysis": {
    "quality_score": 0.88,
    "reasoning": "This API documentation demonstrates good technical depth and structure...",
    "recommendations": [
      "Add more implementation examples",
      "Include error handling scenarios"
    ],
    "confidence": 0.92
  },
  "processing_time_ms": 487
}
```

## Red Team Testing

Test the system's ability to detect poor quality content:

1. **Generic Tags Attack** - Content with meaningless tags
2. **Content-Tag Mismatch** - Cooking recipe tagged as AI/ML
3. **Minimal Content** - Short text with excessive tags  
4. **Spam Detection** - Lorem ipsum and repeated words
5. **Over-Tagging** - Simple content with 15+ tags

## Performance Expectations

- **Rules Engine**: ~15ms per check (7 validations)
- **LLM Analysis**: ~500ms per analysis (simulated)
- **Combined Analysis**: ~515ms total
- **Throughput**: ~60 requests/second (rules only)

## Testing with Frontend Dashboard

1. Open `http://localhost:3000`
2. Navigate to API Testing tab
3. Select endpoint and load sample payloads
4. Execute tests and view real-time results
5. Monitor server status and performance metrics

## Troubleshooting

### Server Won't Start
- Check Python version (3.8+)
- Install requirements: `pip install -r requirements.txt`
- Verify port 8000 is available

### CORS Issues
- Frontend must run on localhost:3000
- Backend configured for local development
- Check browser console for errors

### Import Errors
- Run from backend directory: `cd backend && python run_local.py`
- Check relative imports in Python files 