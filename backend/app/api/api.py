"""
FastAPI application for Indexing QA Observability Tool
Handles chunk ingestion, validation, and reviewer feedback
Optimized for Azure App Service deployment
"""

import time
import json
import asyncio
from typing import List, Dict, Any
from datetime import datetime, UTC, timezone

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File, Body, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi import APIRouter
from sqlalchemy.inspection import inspect

from ..models.models import (
    ChunkIngestRequest, BatchIngestRequest, ChunkAnalysisResponse,
    ReviewerFeedback, QualityCheckResult, ChunkRecord, DeadLetterRecord,
    QualityCheckRecord, ReviewRecord, generate_trace_id, mask_pii_text, FlagStatus, Base, ThresholdConfiguration
)
from ..core.config import get_settings
from ..services.rules_engine import RulesEngine
from ..services.llm_judge import LLMJudge
from ..database.database import get_db, create_tables
from ..services.alerts import AlertManager, AlertType, AlertSeverity
from ..services.enhanced_quality_engine import EnhancedQualityEngine


app = FastAPI(
    title="Indexing QA Observability Tool",
    description="Production-ready quality assurance for Lucy's AI Knowledge Base",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for Azure App Service
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()

alert_manager = AlertManager()


@app.on_event("startup")
async def startup_event():
    """Initialize database and load configurations on startup"""
    print("🚀 Starting Indexing QA Observability Tool...")
    
    # Create database tables
    create_tables()
    
    # Initialize rules engine with current thresholds
    global rules_engine, enhanced_quality_engine, llm_judge
    rules_engine = RulesEngine()
    enhanced_quality_engine = EnhancedQualityEngine()
    llm_judge = LLMJudge() if settings.enable_llm_validation else None
    
    print("✅ Startup complete!")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Indexing QA Observability Tool",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": {
            "llm_validation": settings.enable_llm_validation,
            "async_processing": settings.enable_async_processing,
            "alerts": settings.enable_alerts
        }
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Detailed health check for Azure App Service"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Test LLM connection if enabled
    llm_status = "disabled"
    if settings.enable_llm_validation and llm_judge:
        try:
            await llm_judge.health_check()
            llm_status = "healthy"
        except Exception as e:
            llm_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "checks": {
            "database": db_status,
            "llm_service": llm_status,
            "redis": "not_implemented",  # TODO: Add Redis health check
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/ingest", response_model=ChunkAnalysisResponse)
async def ingest_chunk(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Ingest a single chunk for quality analysis
    
    Example curl command for Postman:
    ```bash
    curl -X POST "http://localhost:8000/ingest" \
         -H "Content-Type: application/json" \
         -d '{
           "record_id": "xyz-456",
           "document_text": "This is a snippet from the vendor contract about refund terms...",
           "tags": ["refunds", "terms & conditions"],
           "source_connector": "SharePoint",
           "file_id": "file-00987",
           "created_at": "2024-06-20T10:00:00Z"
         }'
    ```
    """
    start_time = time.time()
    # Parse JSON body
    data = await request.json()
    # Support both legacy and new field names
    record_id = data.get("record_id")
    trace_id = data.get("trace_id") or generate_trace_id()
    # Accept both 'content' and 'document_text'
    document_text = data.get("document_text") or data.get("content")
    tags = data.get("tags", [])
    # Accept both 'file_id' and from content_metadata
    file_id = data.get("file_id") or (data.get("content_metadata", {}) or {}).get("file_name") or "unknown_file"
    # Accept both 'source_connector' and capitalize for DB
    source_connector = data.get("source_connector", "Unknown")
    if isinstance(source_connector, str):
        source_connector = source_connector.capitalize()
    created_at = data.get("created_at")
    if created_at:
        try:
            created_at = datetime.fromisoformat(created_at)
        except Exception:
            created_at = datetime.now(timezone.utc)
    else:
        created_at = datetime.now(timezone.utc)
    content_metadata = data.get("content_metadata")
    # Build chunk for quality engine
    chunk = ChunkIngestRequest(
        record_id=record_id,
        document_text=document_text,
        tags=tags,
        source_connector=source_connector,
        file_id=file_id,
        created_at=created_at
    )
    # Store in DB
    chunk_record = ChunkRecord(
        trace_id=trace_id,
        record_id=record_id,
        document_text=document_text,
        tags=tags,
        source_connector=source_connector,
        file_id=file_id,
        created_at=created_at,
        content_metadata=content_metadata
    )
    db.add(chunk_record)
    db.flush()
    # Run enhanced quality engine
    quality_results = enhanced_quality_engine.check_chunk(chunk)
    for result in quality_results:
        quality_check = QualityCheckRecord(
            chunk_id=chunk_record.id,
            check_name=result.check_name,
            status=result.status.value,
            confidence_score=result.confidence_score,
            failure_reason=result.failure_reason or "",
            check_metadata=result.check_metadata,
            processing_time_ms=result.check_metadata.get('processing_time_ms', 0) if result.check_metadata else 0
        )
        db.add(quality_check)
        if result.status == FlagStatus.FAIL:
            try:
                asyncio.create_task(alert_manager.send_flagged_result_alert(
                    check_name=result.check_name,
                    failure_reason=result.failure_reason or "",
                    trace_id=trace_id,
                    record_id=record_id,
                    confidence_score=result.confidence_score,
                    check_metadata=result.check_metadata
                ))
            except Exception as e:
                print(f"[ALERT] Failed to send alert: {e}")
    db.commit()
    processing_time = (time.time() - request.state._start_time) * 1000 if hasattr(request.state, '_start_time') else 0
    return {
        "trace_id": trace_id,
        "record_id": record_id,
        "overall_status": FlagStatus.FAIL if any(r.status == FlagStatus.FAIL for r in quality_results) else FlagStatus.PASS,
        "quality_checks": quality_results,
        "processing_time_ms": processing_time,
        "created_at": created_at,
        "content_metadata": content_metadata
    }
        
    except Exception as e:
        db.rollback()
        
        # Log to dead letter queue
        dead_letter = DeadLetterRecord(
            trace_id=trace_id,
            raw_input=chunk.json(),
            error_message=str(e),
            error_type=type(e).__name__,
            source_connector=source_connector  # Already a string
        )
        db.add(dead_letter)
        db.commit()
        
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )


@app.post("/ingest/batch")
async def ingest_batch(
    batch: BatchIngestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Batch ingest multiple chunks for quality analysis
    
    Example curl command:
    ```bash
    curl -X POST "http://localhost:8000/ingest/batch" \
         -H "Content-Type: application/json" \
         -d '{
           "chunks": [
             {
               "record_id": "xyz-456",
               "document_text": "Contract snippet about refund terms...",
               "tags": ["refunds", "terms"],
               "source_connector": "SharePoint",
               "file_id": "file-00987"
             },
             {
               "record_id": "abc-123",
               "document_text": "Employee handbook section on vacation policy...",
               "tags": ["hr", "vacation", "policy"],
               "source_connector": "Confluence",
               "file_id": "file-00988"
             }
           ],
           "batch_metadata": {
             "uploaded_by": "admin",
             "batch_name": "daily_sync_2024-01-15"
           }
         }'
    ```
    """
    start_time = time.time()
    batch_trace_id = generate_trace_id()
    
    results = []
    successful_count = 0
    failed_count = 0
    
    for chunk in batch.chunks:
        try:
            # Process each chunk (reuse single chunk logic)
            result = await ingest_chunk(chunk, background_tasks, db)
            results.append({
                "record_id": chunk.record_id,
                "trace_id": result.trace_id,
                "status": "success",
                "overall_status": result.overall_status
            })
            successful_count += 1
            
        except Exception as e:
            results.append({
                "record_id": chunk.record_id,
                "status": "failed",
                "error": str(e)
            })
            failed_count += 1
    
    processing_time = (time.time() - start_time) * 1000
    
    return {
        "batch_trace_id": batch_trace_id,
        "batch_metadata": batch.batch_metadata,
        "summary": {
            "total_chunks": len(batch.chunks),
            "successful": successful_count,
            "failed": failed_count,
            "processing_time_ms": processing_time
        },
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Upload and process a JSON file containing chunks
    Supports both single chunk and array of chunks
    """
    try:
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
        
        # Handle both single chunk and array formats
        if isinstance(data, dict):
            # Single chunk
            chunk = ChunkIngestRequest(**data)
            result = await ingest_chunk(chunk, background_tasks, db)
            return {"file_name": file.filename, "result": result}
            
        elif isinstance(data, list):
            # Array of chunks
            batch = BatchIngestRequest(
                chunks=[ChunkIngestRequest(**chunk_data) for chunk_data in data],
                batch_metadata={"uploaded_file": file.filename}
            )
            result = await ingest_batch(batch, background_tasks, db)
            return result
            
        else:
            raise ValueError("Invalid JSON format. Expected object or array of objects.")
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File processing failed: {str(e)}")


@app.post("/feedback")
async def submit_reviewer_feedback(
    feedback: ReviewerFeedback,
    db: Session = Depends(get_db)
):
    """
    Submit reviewer feedback for a flagged chunk
    This feeds into the threshold auto-tuning system
    """
    try:
        # Find the chunk record
        chunk_record = db.query(ChunkRecord).filter(
            ChunkRecord.trace_id == feedback.trace_id
        ).first()
        
        if not chunk_record:
            raise HTTPException(status_code=404, detail="Chunk not found")
        
        # Create review record
        review = ReviewRecord(
            chunk_id=chunk_record.id,
            decision=feedback.decision.value,
            comments=feedback.comments,
            reviewer_id=feedback.reviewer_id,
            reviewed_at=feedback.reviewed_at
        )
        
        db.add(review)
        db.commit()
        
        # TODO: Trigger threshold adjustment if needed
        # This would be handled by the feedback loop system
        
        return {
            "trace_id": feedback.trace_id,
            "status": "feedback_recorded",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")


@app.get("/chunks/{trace_id}")
async def get_chunk_analysis(trace_id: str, db: Session = Depends(get_db)):
    """Get detailed analysis results for a specific chunk"""
    chunk_record = db.query(ChunkRecord).filter(
        ChunkRecord.trace_id == trace_id
    ).first()
    
    if not chunk_record:
        raise HTTPException(status_code=404, detail="Chunk not found")
    
    # Get all quality checks
    quality_checks = []
    for check in chunk_record.quality_checks:
        quality_checks.append(QualityCheckResult(
            check_name=check.check_name,
            status=FlagStatus(check.status),
            confidence_score=check.confidence_score,
            failure_reason=check.failure_reason,
            check_metadata=check.check_metadata or {}
        ))
    
    # Determine overall status
    failed_checks = [c for c in quality_checks if c.status == FlagStatus.FAIL]
    overall_status = FlagStatus.FAIL if failed_checks else FlagStatus.PASS
    
    return ChunkAnalysisResponse(
        trace_id=chunk_record.trace_id,
        record_id=chunk_record.record_id,
        overall_status=overall_status,
        quality_checks=quality_checks,
        processing_time_ms=0,  # Historical record
        created_at=chunk_record.created_at
    )


@app.post("/llm/analyze", response_model=QualityCheckResult)
async def llm_analyze(
    chunk: ChunkIngestRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Run LLM semantic validation on a chunk (tags vs content).
    Returns a QualityCheckResult with confidence, status, and reasoning.
    """
    if not settings.enable_llm_validation or llm_judge is None:
        raise HTTPException(status_code=503, detail="LLM Judge is not available.")
    try:
        if llm_judge is not None:
            result = await llm_judge.check_chunk(chunk.document_text, chunk.tags)
            # Optionally, store result in DB if needed
            return result
        else:
            raise HTTPException(status_code=503, detail="LLM Judge is not initialized.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Judge failed: {str(e)}")


async def run_llm_validation(trace_id: str, record_id: str, text: str, tags: List[str]):
    """Background task for async LLM validation"""
    try:
        result = await llm_judge.check_chunk(text, tags)
        
        # Store LLM result in database
        db = next(get_db())
        chunk_record = db.query(ChunkRecord).filter(
            ChunkRecord.trace_id == trace_id
        ).first()
        
        if chunk_record:
            llm_check = QualityCheckRecord(
                chunk_id=chunk_record.id,
                check_name="llm_semantic_validation",
                status=result.status.value,
                confidence_score=result.confidence_score,
                failure_reason=result.failure_reason,
                check_metadata=result.check_metadata,
                processing_time_ms=result.check_metadata.get('processing_time_ms', 0) if result.check_metadata else 0
            )
            db.add(llm_check)
            db.commit()
            
            # TODO: Send alert if LLM flags the chunk
            
    except Exception as e:
        print(f"LLM validation failed for {trace_id}: {e}")


@app.get("/alerts/emails")
def get_alert_emails():
    """Get current alert email recipients (To/CC)"""
    to_list, cc_list = alert_manager.get_email_recipients()
    return {"to": to_list, "cc": cc_list}

@app.post("/alerts/emails")
def add_alert_email(email: str = Query(...), typ: str = Query('to')):
    """Add an alert email recipient (To/CC)"""
    if typ not in ['to', 'cc']:
        raise HTTPException(status_code=400, detail="Type must be 'to' or 'cc'")
    alert_manager.add_email_recipient(email, typ)
    return {"status": "added", "email": email, "type": typ}

@app.delete("/alerts/emails")
def remove_alert_email(email: str = Query(...), typ: str = Query('to')):
    """Remove an alert email recipient (To/CC)"""
    if typ not in ['to', 'cc']:
        raise HTTPException(status_code=400, detail="Type must be 'to' or 'cc'")
    alert_manager.remove_email_recipient(email, typ)
    return {"status": "removed", "email": email, "type": typ}

@app.put("/alerts/emails")
def set_alert_emails(to_list: List[str] = Query(...), cc_list: List[str] = Query(...)):
    """Set all alert email recipients (To/CC)"""
    alert_manager.set_email_recipients(to_list, cc_list)
    return {"status": "updated", "to": to_list, "cc": cc_list}

@app.get("/alerts/template")
def get_alert_template():
    """Get current alert email template"""
    template = alert_manager.get_alert_template()
    return template

@app.put("/alerts/template")
def set_alert_template(subject: str = Query(...), body: str = Query(...)):
    """Set alert email template"""
    alert_manager.set_alert_template(subject, body)
    return {"status": "updated", "subject": subject, "body": body}

@app.post("/alerts/test")
async def test_alert():
    """Send a test alert to verify configuration"""
    try:
        await alert_manager.send_alert(
            alert_type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.MEDIUM,
            message="This is a test alert to verify your alert configuration",
            details={"test": True, "timestamp": datetime.now(timezone.utc).isoformat()},
            trace_id="test-trace-id",
            record_id="test-record-id"
        )
        return {"status": "test_alert_sent", "message": "Test alert sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test alert: {str(e)}")


quality_rules_router = APIRouter()

@quality_rules_router.get("/quality-rules")
async def get_quality_rules(db: Session = Depends(get_db)):
    """Get current quality thresholds for all rules"""
    configs = db.query(ThresholdConfiguration).all()
    return {
        "rules": [
            {
                "check_name": getattr(c, 'check_name', None),
                "threshold_value": float(getattr(c, 'threshold_value', 0)),
                "confidence_cutoff": float(getattr(c, 'confidence_cutoff', 0)),
                "updated_by": getattr(c, 'updated_by', None),
                "updated_at": str(getattr(c, 'updated_at', '')),
                "reason": getattr(c, 'reason', None)
            } for c in configs
        ]
    }

@quality_rules_router.post("/quality-rules")
async def update_quality_rules(
    updates: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """Update quality thresholds for rules in real time"""
    updated = []
    for upd in updates:
        check_name = upd.get("check_name")
        threshold_value = upd.get("threshold_value")
        confidence_cutoff = upd.get("confidence_cutoff")
        reason = upd.get("reason", "Manual update via API")
        if check_name is None or threshold_value is None or confidence_cutoff is None:
            continue
        config = db.query(ThresholdConfiguration).filter(ThresholdConfiguration.check_name == check_name).first()
        if config:
            setattr(config, 'threshold_value', float(threshold_value))
            setattr(config, 'confidence_cutoff', float(confidence_cutoff))
            setattr(config, 'updated_by', "api")
            setattr(config, 'updated_at', datetime.now(timezone.utc))
            setattr(config, 'reason', reason)
            updated.append(check_name)
        else:
            new_config = ThresholdConfiguration(
                check_name=check_name,
                threshold_value=float(threshold_value),
                confidence_cutoff=float(confidence_cutoff),
                updated_by="api",
                updated_at=datetime.now(timezone.utc),
                reason=reason
            )
            db.add(new_config)
            updated.append(check_name)
    db.commit()
    # Update in-memory rules engine thresholds if needed
    if 'rules_engine' in globals():
        rules_engine.update_thresholds({u['check_name']: float(u['threshold_value']) for u in updates if u.get('check_name') and u.get('threshold_value') is not None}, reason="API update")
    return {"updated": updated}

# Register the router
app.include_router(quality_rules_router)


@app.post("/records/approve/{record_id}")
async def approve_flagged_record(record_id: str, request: Request, db: Session = Depends(get_db)):
    """
    Approve a flagged record by record_id. Sets its status to 'approved'.
    """
    data = await request.json()
    user_id = data.get('user_id')
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    try:
        # Find the chunk record by record_id
        chunk_record = db.query(ChunkRecord).filter(ChunkRecord.record_id == record_id).first()
        if not chunk_record:
            raise HTTPException(status_code=404, detail="Record not found")
        # Check if already approved
        if getattr(chunk_record, 'status', None) == 'approved':
            return {"status": "already_approved"}
        # Set status to approved (add status if not present)
        setattr(chunk_record, 'status', 'approved')
        db.commit()
        return {"status": "approved", "record_id": record_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to approve record: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    ) 