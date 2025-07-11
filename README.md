# Indexing QA Observability Tool

A comprehensive quality assurance system for document indexing with real-time validation, LLM-powered semantic analysis, and advanced quality scoring.

## 🚀 Quick Start (For Managers)

### Prerequisites
- **Python 3.8+** and **Node.js 16+**
- **Git** for cloning the repository
- **OpenAI API Key** (optional, for enhanced LLM validation)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd "Indexing QA"
```

### 2. Backend Setup (Python/FastAPI)
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements/requirements.txt

# Start backend server
python run_local.py
```

**Backend will be available at:** http://localhost:8000

### 3. Frontend Setup (Next.js/React)
```bash
# Open new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start frontend server
npm run dev
```

**Frontend will be available at:** http://localhost:3001 (or 3002 if 3001 is busy)

### 4. Test the System
1. Open http://localhost:3001 in your browser
2. Navigate to "API Test" page
3. Test the ingest endpoint with sample data
4. View quality records in the dashboard

## 📊 System Overview

### Architecture
- **Backend**: FastAPI with SQLite database
- **Frontend**: Next.js with React dashboard
- **Quality Engine**: Rules-based + LLM semantic validation
- **Real-time Processing**: Immediate quality assessment

### Key Features
- ✅ **Real-time Quality Validation**
- ✅ **LLM-powered Semantic Analysis**
- ✅ **Advanced Rules Engine**
- ✅ **Trace ID Tracking**
- ✅ **Quality Score Calculation**
- ✅ **Issue Detection & Suggestions**
- ✅ **Dashboard Analytics**

## 🔧 API Endpoints

### Core Endpoints
- `POST /ingest` - Ingest new documents with quality validation
- `GET /records` - Retrieve quality records
- `POST /rules/check` - Test content against rules engine
- `POST /llm/analyze` - LLM semantic validation
- `GET /stats` - System statistics
- `GET /health` - Health check

### Sample API Request
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "record_id": "test-001",
    "content": "This is a comprehensive guide about machine learning algorithms.",
    "tags": ["machine learning", "algorithms", "AI"],
    "source_connector": "sharepoint",
    "content_metadata": {
      "author": "AI Expert",
      "department": "Data Science"
    }
  }'
```

## 📈 Quality Assessment

### Rules Engine Checks
1. **Empty/Missing Tags** - Ensures content has proper categorization
2. **Tag Count Validation** - Validates appropriate number of tags
3. **Text Quality** - Checks content length and meaningfulness
4. **Stopwords Detection** - Identifies generic/non-specific tags
5. **Spam Detection** - Detects test/placeholder content
6. **Duplicate Content** - Prevents redundant entries
7. **Semantic Relevance** - Advanced NLP similarity analysis
8. **Domain Relevance** - Domain-specific knowledge validation
9. **Tag Specificity** - Ensures specific vs generic tags
10. **Context Coherence** - Validates tag consistency

### LLM Judge Features
- **Semantic Validation** - Deep content understanding
- **Quality Scoring** - Confidence-based assessment
- **Issue Detection** - Detailed problem identification
- **AI Suggestions** - Automated improvement recommendations

## 🎯 Quality Metrics

### Scoring Formula
```
Quality Score = (Rules Engine Confidence × 0.6 + LLM Confidence × 0.4) × 100
```

### Thresholds
- **Min Tag Count**: 1
- **Max Tag Count**: 20
- **Spam Threshold**: 0.3
- **Stopword Threshold**: 0.5
- **Semantic Relevance**: 0.4
- **Domain Relevance**: 0.4
- **Tag Specificity**: 0.5
- **Context Coherence**: 0.3

## 🔍 Dashboard Features

### Main Dashboard
- **Quality Records Table** - View all processed records
- **Trace ID Tracking** - Unique identifier for each record
- **Status Indicators** - Approved/Flagged/Under Review
- **Quality Scores** - Real-time scoring display
- **Filtering & Sorting** - Advanced data exploration

### Record Details
- **Quality Checks Table** - Detailed validation results
- **AI Suggestions** - LLM-generated improvements
- **Issues Detected** - Specific problems identified
- **Processing Metrics** - Performance and timing data

### Analytics
- **System Statistics** - Overall quality metrics
- **Performance Monitoring** - Processing times and throughput
- **Trend Analysis** - Quality improvement tracking

## 🛠️ Configuration

### Environment Variables
Create `.env.local` in the frontend directory:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend Configuration
Key settings in `backend/app/core/config.py`:
- Database URL
- LLM API keys
- Quality thresholds
- Performance settings

## 🧪 Testing

### Manual Testing
1. **API Test Interface** - Built-in testing tool
2. **Sample Data** - Use provided examples
3. **Quality Validation** - Test various content types

### Automated Testing
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

## 📊 Monitoring

### Health Checks
- Backend: http://localhost:8000/health
- Frontend: Built-in Next.js health monitoring

### Logs
- Backend logs in terminal
- Frontend logs in browser console
- Quality assessment details in API responses

## 🚨 Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check Python version
python --version

# Reinstall dependencies
pip install -r requirements/requirements.txt

# Check port availability
lsof -i :8000
```

**Frontend won't start:**
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

**API connection issues:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Verify frontend environment
cat frontend/.env.local
```

### Performance Issues
- **High processing times**: Check LLM API rate limits
- **Memory usage**: Monitor Python process memory
- **Database size**: SQLite file location in backend/

## 📚 Documentation

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Code Structure**: See individual component READMEs
- **Deployment Guide**: See `README_PRODUCTION.md`

## 🤝 Support

For technical issues or questions:
1. Check the logs in terminal
2. Review API documentation
3. Test individual components
4. Check configuration files

## 📈 Performance Metrics

### Expected Performance
- **Rules Engine**: <10ms per record
- **LLM Judge**: 500-2000ms per record
- **Throughput**: 100+ records/minute
- **Accuracy**: 95%+ quality detection

### Monitoring
- Real-time quality scores
- Processing time tracking
- Error rate monitoring
- System health checks

---

**Last Updated**: July 2024  
**Version**: 1.0.0  
**Status**: Production Ready 