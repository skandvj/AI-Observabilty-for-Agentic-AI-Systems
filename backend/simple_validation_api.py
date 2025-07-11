"""
Simplified Indexing QA API - Focused on JSON Validation and Flagging Decisions
"""

import time
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from sqlalchemy import create_engine, Column, String, Text, DateTime, Float, Boolean, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./validation_qa.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Pydantic Models
class FlagStatus(str, Enum):
    """Quality check flag statuses"""
    PASS = "pass"
    FAIL = "fail"
    PENDING_REVIEW = "pending_review"

class ValidationRequest(BaseModel):
    """Input schema for JSON validation"""
    record_id: str = Field(..., description="Unique identifier for the record")
    document_text: str = Field(..., min_length=10, description="The actual text content")
    tags: List[str] = Field(..., description="Associated tags/metadata")
    source_type: str = Field(..., description="Source type (e.g., 'json', 'api', 'file')")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('document_text')
    def validate_text(cls, v):
        """Ensure document text meets minimum requirements"""
        if len(v.strip()) < 10:
            raise ValueError("Document text must be at least 10 characters")
        return v.strip()

class ValidationResult(BaseModel):
    """Quality check results for a record"""
    check_name: str
    status: FlagStatus
    confidence_score: float = Field(ge=0.0, le=1.0)
    failure_reason: Optional[str] = None
    check_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ValidationResponse(BaseModel):
    """API response for validation analysis"""
    trace_id: str
    record_id: str
    overall_status: FlagStatus
    quality_checks: List[ValidationResult]
    processing_time_ms: float
    created_at: datetime

# SQLAlchemy Models
class ValidationRecord(Base):
    """Main validation record table"""
    __tablename__ = "validation_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(String(64), unique=True, nullable=False, index=True)
    record_id = Column(String(256), nullable=False, index=True)
    document_text = Column(Text, nullable=False)
    tags = Column(JSON, nullable=False)
    source_type = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    overall_status = Column(String(20), nullable=False, index=True)

class QualityCheckRecord(Base):
    """Individual quality check results"""
    __tablename__ = "quality_check_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    validation_id = Column(String(36), nullable=False, index=True)
    check_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)
    failure_reason = Column(Text, nullable=True)
    check_metadata_json = Column(JSON, nullable=True)
    executed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processing_time_ms = Column(Float, nullable=False)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI(
    title="Indexing QA Validation Tool",
    description="JSON validation and quality flagging system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Validation Engine
class ValidationEngine:
    """Simple validation engine for JSON content"""
    
    def __init__(self):
        self.checks = [
            self._check_empty_tags,
            self._check_tag_count,
            self._check_text_quality,
            self._check_generic_stopwords,
            self._check_spam_patterns,
            self._check_tag_text_relevance
        ]
    
    def validate_record(self, record: ValidationRequest) -> List[ValidationResult]:
        """Run all validation checks on a record"""
        results = []
        
        for check_func in self.checks:
            try:
                result = check_func(record)
                results.append(result)
            except Exception as e:
                # If check fails, create a failed result
                results.append(ValidationResult(
                    check_name=check_func.__name__,
                    status=FlagStatus.FAIL,
                    confidence_score=0.0,
                    failure_reason=f"Check failed: {str(e)}"
                ))
        
        return results
    
    def _check_empty_tags(self, record: ValidationRequest) -> ValidationResult:
        """Check for empty or missing tags"""
        if not record.tags or len(record.tags) == 0:
            return ValidationResult(
                check_name="empty_tags",
                status=FlagStatus.FAIL,
                confidence_score=1.0,
                failure_reason="No tags provided"
            )
        
        empty_tags = [tag for tag in record.tags if not tag.strip()]
        if empty_tags:
            return ValidationResult(
                check_name="empty_tags",
                status=FlagStatus.FAIL,
                confidence_score=0.9,
                failure_reason=f"Found {len(empty_tags)} empty tags"
            )
        
        return ValidationResult(
            check_name="empty_tags",
            status=FlagStatus.PASS,
            confidence_score=1.0
        )
    
    def _check_tag_count(self, record: ValidationRequest) -> ValidationResult:
        """Check if tag count is within reasonable bounds"""
        tag_count = len(record.tags)
        
        if tag_count < 1:
            return ValidationResult(
                check_name="tag_count_validation",
                status=FlagStatus.FAIL,
                confidence_score=0.8,
                failure_reason=f"Too few tags: {tag_count} < 1"
            )
        
        if tag_count > 20:
            return ValidationResult(
                check_name="tag_count_validation",
                status=FlagStatus.FAIL,
                confidence_score=0.9,
                failure_reason=f"Too many tags: {tag_count} > 20"
            )
        
        return ValidationResult(
            check_name="tag_count_validation",
            status=FlagStatus.PASS,
            confidence_score=1.0
        )
    
    def _check_text_quality(self, record: ValidationRequest) -> ValidationResult:
        """Basic text quality and length validation"""
        text = record.document_text.strip()
        text_length = len(text)
        
        if text_length < 10:
            return ValidationResult(
                check_name="text_quality",
                status=FlagStatus.FAIL,
                confidence_score=1.0,
                failure_reason=f"Text too short: {text_length} characters"
            )
        
        if text_length > 50000:
            return ValidationResult(
                check_name="text_quality",
                status=FlagStatus.FAIL,
                confidence_score=0.7,
                failure_reason=f"Text too long: {text_length} characters"
            )
        
        return ValidationResult(
            check_name="text_quality",
            status=FlagStatus.PASS,
            confidence_score=1.0
        )
    
    def _check_generic_stopwords(self, record: ValidationRequest) -> ValidationResult:
        """Check if tags contain too many generic terms"""
        generic_stopwords = {
            'document', 'file', 'content', 'text', 'information', 'data',
            'report', 'summary', 'overview', 'details', 'description',
            'general', 'misc', 'miscellaneous', 'other', 'various',
            'important', 'urgent', 'critical', 'high', 'low', 'medium',
            'new', 'old', 'recent', 'current', 'updated', 'latest'
        }
        
        if not record.tags:
            return ValidationResult(
                check_name="stopwords_detection",
                status=FlagStatus.PASS,
                confidence_score=1.0
            )
        
        normalized_tags = [tag.lower().strip() for tag in record.tags]
        stopword_matches = [tag for tag in normalized_tags if tag in generic_stopwords]
        stopword_ratio = len(stopword_matches) / len(record.tags)
        
        if stopword_ratio > 0.5:
            return ValidationResult(
                check_name="stopwords_detection",
                status=FlagStatus.FAIL,
                confidence_score=min(0.9, stopword_ratio),
                failure_reason=f"Too many generic tags: {stopword_ratio:.1%} are stopwords"
            )
        
        return ValidationResult(
            check_name="stopwords_detection",
            status=FlagStatus.PASS,
            confidence_score=1.0 - stopword_ratio
        )
    
    def _check_spam_patterns(self, record: ValidationRequest) -> ValidationResult:
        """Detect spam/test content using pattern matching"""
        import re
        
        text = record.document_text.lower()
        
        spam_patterns = [
            r'lorem ipsum',
            r'test\s*(document|content|text|data)',
            r'sample\s*(document|content|text|data)',
            r'placeholder\s*(text|content)',
            r'dummy\s*(text|content|data)',
            r'(\w+)\1{3,}',  # Repeated words
            r'asdf|qwerty|123456|abcdef',  # Keyboard mashing
        ]
        
        spam_matches = []
        for pattern in spam_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                spam_matches.append(pattern)
        
        if spam_matches:
            return ValidationResult(
                check_name="spam_pattern_detection",
                status=FlagStatus.FAIL,
                confidence_score=0.9,
                failure_reason=f"Detected spam patterns: {len(spam_matches)} matches"
            )
        
        return ValidationResult(
            check_name="spam_pattern_detection",
            status=FlagStatus.PASS,
            confidence_score=1.0
        )
    
    def _check_tag_text_relevance(self, record: ValidationRequest) -> ValidationResult:
        """Basic tag-text relevance check"""
        import re
        
        if not record.tags:
            return ValidationResult(
                check_name="tag_text_relevance",
                status=FlagStatus.PASS,
                confidence_score=1.0
            )
        
        text_lower = record.document_text.lower()
        text_words = set(re.findall(r'\b\w+\b', text_lower))
        
        relevant_tags = 0
        total_tags = len(record.tags)
        
        for tag in record.tags:
            tag_words = set(re.findall(r'\b\w+\b', tag.lower()))
            if tag_words & text_words:  # Set intersection
                relevant_tags += 1
            elif any(tag_word in text_lower for tag_word in tag_words if len(tag_word) > 3):
                relevant_tags += 0.5
        
        relevance_score = relevant_tags / total_tags if total_tags > 0 else 0
        
        if relevance_score < 0.3:
            return ValidationResult(
                check_name="tag_text_relevance",
                status=FlagStatus.FAIL,
                confidence_score=0.7,
                failure_reason=f"Low tag-text relevance: {relevance_score:.1%}"
            )
        
        return ValidationResult(
            check_name="tag_text_relevance",
            status=FlagStatus.PASS,
            confidence_score=relevance_score
        )

# Initialize validation engine
validation_engine = ValidationEngine()

# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Indexing QA Validation Tool",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": {
            "json_validation": True,
            "quality_flagging": True,
            "real_time_analytics": True
        }
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Detailed health check"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "checks": {
            "database": db_status,
            "validation_engine": "healthy"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/validate", response_model=ValidationResponse)
async def validate_record(
    record: ValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate a JSON record and return quality analysis
    
    Example:
    ```json
    {
      "record_id": "doc-123",
      "document_text": "This is a sample document about API documentation standards...",
      "tags": ["api", "documentation", "standards"],
      "source_type": "json"
    }
    ```
    """
    start_time = time.time()
    trace_id = f"val-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    try:
        # Run validation checks
        validation_results = validation_engine.validate_record(record)
        
        # Determine overall status
        failed_checks = [r for r in validation_results if r.status == FlagStatus.FAIL]
        overall_status = FlagStatus.FAIL if failed_checks else FlagStatus.PASS
        
        # Store in database
        validation_record = ValidationRecord(
            trace_id=trace_id,
            record_id=record.record_id,
            document_text=record.document_text,
            tags=record.tags,
            source_type=record.source_type,
            created_at=record.created_at,
            overall_status=overall_status.value
        )
        
        db.add(validation_record)
        db.flush()  # Get the ID without committing
        
        # Store quality check results
        for result in validation_results:
            quality_check = QualityCheckRecord(
                validation_id=validation_record.id,
                check_name=result.check_name,
                status=result.status.value,
                confidence_score=result.confidence_score,
                failure_reason=result.failure_reason,
                check_metadata_json=result.check_metadata,
                processing_time_ms=0.0
            )
            db.add(quality_check)
        
        db.commit()
        
        processing_time = (time.time() - start_time) * 1000
        
        return ValidationResponse(
            trace_id=trace_id,
            record_id=record.record_id,
            overall_status=overall_status,
            quality_checks=validation_results,
            processing_time_ms=processing_time,
            created_at=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.get("/records")
async def get_records(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get validation records with optional filtering"""
    query = db.query(ValidationRecord)
    
    if status:
        query = query.filter(ValidationRecord.overall_status == status)
    
    records = query.order_by(ValidationRecord.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "records": [
            {
                "trace_id": record.trace_id,
                "record_id": record.record_id,
                "source_type": record.source_type,
                "overall_status": record.overall_status,
                "created_at": record.created_at.isoformat(),
                "processed_at": record.processed_at.isoformat()
            }
            for record in records
        ],
        "total": len(records),
        "limit": limit,
        "offset": offset
    }

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get real-time statistics"""
    total_records = db.query(ValidationRecord).count()
    passed_records = db.query(ValidationRecord).filter(ValidationRecord.overall_status == "pass").count()
    failed_records = db.query(ValidationRecord).filter(ValidationRecord.overall_status == "fail").count()
    
    # Get recent activity (last 24 hours)
    from datetime import timedelta
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    recent_records = db.query(ValidationRecord).filter(ValidationRecord.created_at >= yesterday).count()
    
    return {
        "total_records": total_records,
        "passed_records": passed_records,
        "failed_records": failed_records,
        "pass_rate": (passed_records / total_records * 100) if total_records > 0 else 0,
        "recent_activity_24h": recent_records,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint for quick validation"""
    test_record = ValidationRequest(
        record_id="test-123",
        document_text="This is a test document with meaningful content about API documentation standards and best practices.",
        tags=["api", "documentation", "standards"],
        source_type="test"
    )
    
    validation_results = validation_engine.validate_record(test_record)
    overall_status = FlagStatus.PASS if all(r.status == FlagStatus.PASS for r in validation_results) else FlagStatus.FAIL
    
    return {
        "test_record": test_record.dict(),
        "validation_results": [result.dict() for result in validation_results],
        "overall_status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simplified Indexing QA Validation Tool...")
    print("📡 Available endpoints:")
    print("  🏠 Home:           http://127.0.0.1:8000/")
    print("  📋 API Docs:       http://127.0.0.1:8000/docs")
    print("  ❤️  Health Check:   http://127.0.0.1:8000/health")
    print("  📊 Statistics:     http://127.0.0.1:8000/stats")
    print("  📥 Validate:       POST http://127.0.0.1:8000/validate")
    print("  📋 Records:        GET  http://127.0.0.1:8000/records")
    print("  🧪 Test:           GET  http://127.0.0.1:8000/test")
    print("✨ Features:")
    print("  • JSON validation and quality checks")
    print("  • Real-time flagging decisions")
    print("  • In-memory storage for testing")
    print("  • CORS enabled for frontend integration")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True) 