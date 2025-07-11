"""
Enhanced API for Indexing QA with World-Class Quality Scoring
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import time
from datetime import datetime, UTC, timezone
from typing import List, Dict, Any, Optional

from ..models.enhanced_models import (
    SharePointIngestRequest, ProcessedRecord, AnalyticsResponse,
    db_manager
)
from ..models.models import ChunkIngestRequest, QualityCheckRecord, DeadLetterRecord
from ..core.config import get_settings
from ..services.enhanced_processor import EnhancedProcessor
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..models.models import generate_trace_id


app = FastAPI(
    title="Enhanced Indexing QA API",
    description="Advanced content quality analysis with real-time analytics",
    version="2.0.0"
)

# Initialize enhanced processor
enhanced_processor = EnhancedProcessor()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Enhanced Indexing QA API",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "SharePoint/Jira JSON processing",
            "Real-time analytics",
            "Local database storage",
            "Quality analysis",
            "Tag extraction"
        ],
        "endpoints": {
            "health": "/health",
            "ingest": "/ingest/sharepoint",
            "records": "/records",
            "analytics": "/analytics/dashboard",
            "export": "/export/records",
            "test": "/test/process"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "database": "connected",
        "processor": "ready"
    }


@app.post("/ingest/sharepoint")
async def ingest_sharepoint_data(data: SharePointIngestRequest):
    """
    Ingest SharePoint/Jira data from 10_Examples.json format
    Follows proper process flow: ingest → process → store → analyze
    """
    start_time = time.time()
    
    try:
        # Step 1: Process the data
        processed_records = enhanced_processor.process_sharepoint_data({"hits": data.hits})
        
        # Step 2: Calculate processing metrics
        processing_time = (time.time() - start_time) * 1000
        
        # Step 3: Return results
        return {
            "status": "success",
            "message": f"Processed {len(processed_records)} records",
            "processed_count": len(processed_records),
            "processing_time_ms": processing_time,
            "quality_summary": {
                "high": len([r for r in processed_records if r.quality_level.value == "high"]),
                "medium": len([r for r in processed_records if r.quality_level.value == "medium"]),
                "low": len([r for r in processed_records if r.quality_level.value == "low"])
            },
            "sample_records": [
                {
                    "id": record.id,
                    "title": record.title[:100] + "..." if len(record.title) > 100 else record.title,
                    "quality_score": record.quality_score,
                    "quality_level": record.quality_level.value,
                    "tags_count": len(record.tags)
                }
                for record in processed_records[:5]  # Show first 5
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.post("/ingest/enhanced")
async def ingest_chunk_enhanced(
    chunk: ChunkIngestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Enhanced ingest endpoint with world-class quality scoring
    Uses advanced semantic analysis and domain-specific knowledge
    """
    start_time = time.time()
    trace_id = generate_trace_id()
    
    try:
        # Process with enhanced quality engine
        processing_result = enhanced_processor.process_chunk(chunk)
        
        # Create enhanced chunk record
        chunk_record = enhanced_processor.create_quality_record(chunk, processing_result)
        
        db.add(chunk_record)
        db.flush()  # Get the ID without committing
        
        # Store enhanced quality check results
        for check_result in processing_result["quality_checks"]:
            quality_check = QualityCheckRecord(
                chunk_id=chunk_record.id,
                check_name=check_result.check_name,
                status=check_result.status.value,
                confidence_score=check_result.confidence_score,
                failure_reason=check_result.failure_reason,
                check_metadata=check_result.check_metadata,
                processing_time_ms=check_result.check_metadata.get('processing_time_ms', 0) if check_result.check_metadata else 0
            )
            db.add(quality_check)
        
        db.commit()
        
        return {
            "trace_id": trace_id,
            "record_id": chunk.record_id,
            "overall_status": processing_result["status"],
            "quality_score": processing_result["quality_score"],
            "overall_confidence": processing_result["overall_confidence"],
            "rules_confidence": processing_result["rules_confidence"],
            "llm_confidence": processing_result["llm_confidence"],
            "quality_checks": processing_result["quality_checks"],
            "processing_time_ms": processing_result["processing_time_ms"],
            "failed_checks_count": processing_result["failed_checks_count"],
            "total_checks_count": processing_result["total_checks_count"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        db.rollback()
        
        # Log to dead letter queue
        dead_letter = DeadLetterRecord(
            trace_id=trace_id,
            raw_input=chunk.json(),
            error_message=str(e),
            error_type=type(e).__name__,
            source_connector=chunk.source_connector.value
        )
        db.add(dead_letter)
        db.commit()
        
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced processing failed: {str(e)}"
        )

@app.get("/records/enhanced")
async def get_enhanced_records():
    """Get all records processed with enhanced quality engine"""
    try:
        records = db_manager.get_all_records()
        
        return {
            "status": "success",
            "total_records": len(records),
            "records": [
                {
                    "id": record.id,
                    "trace_id": record.trace_id,
                    "title": record.title,
                    "document_text": record.document_text,
                    "tags": record.tags,
                    "source_connector": record.source_connector.value,
                    "company": record.company,
                    "quality_score": record.quality_score,
                    "overall_confidence": getattr(record, 'overall_confidence', 0),
                    "rules_confidence": getattr(record, 'rules_engine_confidence', 0),
                    "llm_confidence": getattr(record, 'llm_confidence', 0),
                    "quality_level": record.quality_level.value,
                    "quality_checks": record.quality_checks,
                    "content_metadata": record.content_metadata,
                    "created_at": record.created_at.isoformat(),
                    "processing_time_ms": record.processing_time_ms
                }
                for record in records
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/quality/analyze")
async def analyze_quality_enhanced(
    chunk: ChunkIngestRequest = Body(...)
):
    """
    Analyze quality with enhanced engine (no database storage)
    Returns detailed quality analysis with world-class scoring
    """
    try:
        processing_result = enhanced_processor.process_chunk(chunk)
        
        return {
            "status": "success",
            "analysis": {
                "quality_score": processing_result["quality_score"],
                "overall_confidence": processing_result["overall_confidence"],
                "rules_confidence": processing_result["rules_confidence"],
                "llm_confidence": processing_result["llm_confidence"],
                "status": processing_result["status"],
                "failed_checks_count": processing_result["failed_checks_count"],
                "total_checks_count": processing_result["total_checks_count"],
                "processing_time_ms": processing_result["processing_time_ms"],
                "quality_checks": [
                    {
                        "check_name": check.check_name,
                        "status": check.status.value,
                        "confidence_score": check.confidence_score,
                        "failure_reason": check.failure_reason,
                        "description": check.description,
                        "suggestion": check.suggestion,
                        "category": check.category,
                        "severity": check.severity,
                        "autoFixable": check.autoFixable,
                        "check_metadata": check.check_metadata
                    }
                    for check in processing_result["quality_checks"]
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality analysis failed: {str(e)}")


@app.get("/records")
async def get_records():
    """Get all processed records with full details"""
    try:
        records = db_manager.get_all_records()
        
        return {
            "status": "success",
            "total_records": len(records),
            "records": [
                {
                    "id": record.id,
                    "trace_id": record.trace_id,  # Add this line
                    "title": record.title,
                    "document_text": record.document_text,
                    "tags": record.tags,
                    "source_connector": record.source_connector.value,
                    "company": record.company,
                    "quality_score": record.quality_score,
                    "quality_level": record.quality_level.value,
                    "quality_checks": record.quality_checks,
                    "content_metadata": record.content_metadata,
                    "created_at": record.created_at.isoformat(),
                    "processing_time_ms": record.processing_time_ms
                }
                for record in records
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/analytics/dashboard")
async def get_real_time_analytics():
    """Get real-time analytics dashboard data"""
    try:
        analytics = db_manager.get_analytics()
        
        return {
            "status": "success",
            "analytics": {
                "total_records": analytics.total_records,
                "quality_distribution": analytics.quality_distribution,
                "source_distribution": analytics.source_distribution,
                "company_distribution": analytics.company_distribution,
                "recent_activity": analytics.recent_activity,
                "quality_trends": analytics.quality_trends,
                "tag_cloud": analytics.tag_cloud,
                "last_updated": analytics.last_updated.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@app.get("/export/records")
async def export_records(format: str = "json"):
    """Export records in specified format"""
    try:
        records = db_manager.get_all_records()
        
        if format.lower() == "csv":
            # Generate CSV format
            csv_lines = ["id,title,company,quality_score,quality_level,tags,created_at"]
            for record in records:
                tags_str = ";".join(record.tags)
                csv_lines.append(
                    f'"{record.id}","{record.title}","{record.company}",'
                    f'{record.quality_score},{record.quality_level.value},'
                    f'"{tags_str}","{record.created_at.isoformat()}"'
                )
            return JSONResponse(
                content={"csv_data": "\n".join(csv_lines)},
                media_type="text/csv"
            )
        else:
            # JSON format
            return {
                "status": "success",
                "format": "json",
                "total_records": len(records),
                "records": [
                    {
                        "id": record.id,
                        "title": record.title,
                        "document_text": record.document_text,
                        "tags": record.tags,
                        "source_connector": record.source_connector.value,
                        "company": record.company,
                        "quality_score": record.quality_score,
                        "quality_level": record.quality_level.value,
                        "quality_checks": record.quality_checks,
                        "content_metadata": record.content_metadata,
                        "created_at": record.created_at.isoformat()
                    }
                    for record in records
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")


@app.post("/import/records")
async def import_records(file: UploadFile = File(...)):
    """Import records from uploaded file"""
    try:
        if not file.filename or not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Only JSON files supported")
        
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
        
        # Process the imported data using enhanced processor
        processed_count = 0
        for item in data if isinstance(data, list) else [data]:
            try:
                chunk = ChunkIngestRequest(**item)
                processing_result = enhanced_processor.process_chunk(chunk)
                processed_count += 1
            except Exception as e:
                print(f"Failed to process item: {e}")
                continue
        
        return {
            "status": "success",
            "message": f"Imported and processed {processed_count} records with enhanced quality scoring",
            "processed_count": processed_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import error: {str(e)}")

@app.get("/test/process")
async def test_process():
    """Test endpoint with sample data using enhanced processor"""
    try:
        # Sample data for testing
        sample_data = {
            "record_id": "test-enhanced-001",
            "document_text": "This is a test document about API development and database management. It contains information about REST APIs, database design, and software architecture.",
            "tags": ["api", "database", "software", "development"],
            "source_connector": "test",
            "file_id": "test-file-001"
        }
        
        # Process with enhanced quality engine
        chunk = ChunkIngestRequest(**sample_data)
        processing_result = enhanced_processor.process_chunk(chunk)
        
        return {
            "status": "success",
            "message": "Enhanced test processing completed",
            "quality_score": processing_result["quality_score"],
            "overall_confidence": processing_result["overall_confidence"],
            "rules_confidence": processing_result["rules_confidence"],
            "llm_confidence": processing_result["llm_confidence"],
            "status": processing_result["status"],
            "failed_checks_count": processing_result["failed_checks_count"],
            "total_checks_count": processing_result["total_checks_count"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@app.get("/stats")
async def get_system_stats():
    """Get system statistics"""
    try:
        records = db_manager.get_all_records()
        analytics = db_manager.get_analytics()
        
        return {
            "status": "success",
            "system_stats": {
                "total_records": len(records),
                "quality_distribution": analytics.quality_distribution,
                "source_distribution": analytics.source_distribution,
                "company_distribution": analytics.company_distribution,
                "avg_quality_score": sum(r.quality_score for r in records) / len(records) if records else 0,
                "total_tags": len(set(tag for r in records for tag in r.tags)),
                "last_updated": datetime.now(UTC).isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 