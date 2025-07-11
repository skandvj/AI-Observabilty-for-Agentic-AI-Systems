# Quick Start Guide

## 🚀 5-Minute Setup

### 1. Run Setup Script
```bash
./setup.sh
```

### 2. Start Backend
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python run_local.py
```

### 3. Start Frontend (New Terminal)
```bash
cd frontend
npm run dev
```

### 4. Test the System
1. Open http://localhost:3001
2. Go to "API Test" page
3. Click "Test Ingest" with sample data
4. View results in "Records" page

## 🧪 Sample Test Data

### Basic Test
```json
{
  "record_id": "test-001",
  "content": "This is a comprehensive guide about machine learning algorithms including supervised learning, unsupervised learning, and deep learning techniques.",
  "tags": ["machine learning", "algorithms", "supervised learning", "deep learning"],
  "source_connector": "sharepoint",
  "content_metadata": {
    "author": "AI Expert",
    "department": "Data Science"
  }
}
```

### Quality Test (Should Flag)
```json
{
  "record_id": "test-002",
  "content": "This is a test document with generic content.",
  "tags": ["document", "test", "general"],
  "source_connector": "sharepoint"
}
```

## 📊 Expected Results

### Good Quality Record
- **Quality Score**: 85-95
- **Status**: Approved
- **Issues**: 0-2 minor issues
- **Trace ID**: Generated automatically

### Poor Quality Record
- **Quality Score**: 20-40
- **Status**: Flagged
- **Issues**: 5-8 issues detected
- **Suggestions**: AI-generated improvements

## 🔍 What to Look For

### Dashboard Features
- ✅ Trace ID column (left of Record ID)
- ✅ Quality score display
- ✅ Status indicators
- ✅ Clickable rows for details
- ✅ Real-time data updates

### Quality Checks
- ✅ Rules engine validation
- ✅ LLM semantic analysis
- ✅ Issue detection
- ✅ AI suggestions
- ✅ Processing time metrics

## 🚨 Common Issues

### Backend Issues
- **Port 8000 in use**: Kill existing process or change port
- **Missing dependencies**: Run `pip install -r requirements/requirements.txt`
- **Database errors**: Delete `backend/indexing_qa.db` and restart

### Frontend Issues
- **Port 3001 in use**: Frontend will auto-switch to 3002
- **API connection**: Check `.env.local` file
- **Build errors**: Run `npm install` again

## 📞 Support

If you encounter issues:
1. Check terminal logs for errors
2. Verify both servers are running
3. Test API endpoints directly
4. Review README.md for detailed instructions

---

**Ready to test!** 🎯 