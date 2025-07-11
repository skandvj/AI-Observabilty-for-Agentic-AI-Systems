"""
Azure Functions for Indexing QA Observability Tool
Provides scheduled processing, monitoring, and reporting capabilities
Designed for Azure Functions runtime with timer and HTTP triggers
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Any, Optional

# Azure imports with graceful fallback for local development
try:
    import azure.functions as func
    from azure.storage.blob import BlobServiceClient
    from azure.monitor.opentelemetry import configure_azure_monitor
    AZURE_AVAILABLE = True
except ImportError:
    func = None
    BlobServiceClient = None
    configure_azure_monitor = None
    AZURE_AVAILABLE = False

from models import (
    ChunkRecord, QualityCheckRecord, ReviewRecord, DeadLetterRecord,
    AlertRecord, FlagStatus, ReviewerDecision
)
from database import get_db_context, check_database_health
from feedback_loop import ContinuousLearningEngine, export_golden_dataset
from alerts import QualityMonitor, CostMonitor, alert_system_health_degraded
from llm_judge import LLMJudge
from rules_engine import RulesEngine
from config import get_settings


# Configure logging for Azure Functions
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Azure Monitor (Application Insights) if available
if AZURE_AVAILABLE and configure_azure_monitor:
    try:
        configure_azure_monitor(
            connection_string="InstrumentationKey=your-instrumentation-key"  # TODO: Configure from settings
        )
    except Exception as e:
        logger.warning(f"Failed to configure Azure Monitor: {e}")

settings = get_settings()


# Timer Triggers for Scheduled Tasks

@func.FunctionApp()
def function_app():
    """Azure Functions app configuration"""
    pass


@function_app.schedule(
    schedule="0 0 * * * *",  # Every hour
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def hourly_quality_monitoring(timer: func.TimerRequest) -> None:
    """
    Hourly quality monitoring and alerting
    Checks quality metrics and triggers alerts if thresholds exceeded
    """
    
    logger.info("Starting hourly quality monitoring")
    
    try:
        # Run quality monitoring
        quality_monitor = QualityMonitor()
        asyncio.run(quality_monitor.check_quality_thresholds())
        
        # Check system health
        health_status = check_database_health()
        if health_status["status"] != "healthy":
            asyncio.run(alert_system_health_degraded(health_status))
        
        # Log success
        logger.info("Hourly quality monitoring completed successfully")
        
    except Exception as e:
        logger.error(f"Hourly quality monitoring failed: {e}")
        raise


@function_app.schedule(
    schedule="0 0 8 * * *",  # Daily at 8 AM UTC
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def daily_learning_cycle(timer: func.TimerRequest) -> None:
    """
    Daily continuous learning cycle
    Updates thresholds and builds golden dataset from reviewer feedback
    """
    
    logger.info("Starting daily learning cycle")
    
    try:
        learning_engine = ContinuousLearningEngine()
        results = learning_engine.run_learning_cycle()
        
        # Log results
        logger.info(f"Learning cycle results: {results['summary']}")
        
        # Store results in blob storage for analysis
        if results['threshold_adjustments'] or results['golden_dataset_updates']:
            _store_learning_results(results)
        
    except Exception as e:
        logger.error(f"Daily learning cycle failed: {e}")
        raise


@function_app.schedule(
    schedule="0 0 9 * * 1",  # Weekly on Monday at 9 AM UTC
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def weekly_root_cause_report(timer: func.TimerRequest) -> None:
    """
    Generate weekly root cause analysis report
    Creates comprehensive reports for stakeholders
    """
    
    logger.info("Starting weekly root cause report generation")
    
    try:
        report_data = _generate_root_cause_report()
        
        # Store report in blob storage
        report_url = _store_report_to_blob(report_data, "weekly_root_cause_report")
        
        # Send report notification
        asyncio.run(_send_report_notification(report_url, "weekly"))
        
        logger.info(f"Weekly report generated and stored: {report_url}")
        
    except Exception as e:
        logger.error(f"Weekly root cause report failed: {e}")
        raise


@function_app.schedule(
    schedule="0 */6 * * * *",  # Every 6 hours
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def cost_monitoring(timer: func.TimerRequest) -> None:
    """
    Monitor LLM costs and trigger alerts if budgets exceeded
    """
    
    logger.info("Starting cost monitoring")
    
    try:
        # Get cost metrics from LLM judge
        llm_judge = LLMJudge()
        cost_metrics = llm_judge.get_cost_metrics()
        
        # Calculate daily and monthly costs
        daily_cost = _calculate_daily_cost(cost_metrics)
        monthly_cost = _calculate_monthly_cost(cost_metrics)
        
        # Check against budgets
        cost_monitor = CostMonitor()
        asyncio.run(cost_monitor.check_cost_thresholds(daily_cost, monthly_cost))
        
        # Log cost metrics
        logger.info(f"Cost monitoring - Daily: ${daily_cost:.2f}, Monthly: ${monthly_cost:.2f}")
        
    except Exception as e:
        logger.error(f"Cost monitoring failed: {e}")
        raise


@function_app.schedule(
    schedule="0 0 2 * * *",  # Daily at 2 AM UTC
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def database_maintenance(timer: func.TimerRequest) -> None:
    """
    Daily database maintenance tasks
    Cleanup old records, optimize performance, backup data
    """
    
    logger.info("Starting database maintenance")
    
    try:
        from database import cleanup_old_records, backup_database
        
        # Clean up old records (90 day retention)
        cleanup_old_records(days_to_keep=90)
        
        # Backup database if SQLite (for development)
        if "sqlite" in settings.database_url:
            backup_path = backup_database()
            logger.info(f"Database backed up to: {backup_path}")
        
        # Update database statistics (Azure SQL)
        _update_database_statistics()
        
        logger.info("Database maintenance completed")
        
    except Exception as e:
        logger.error(f"Database maintenance failed: {e}")
        raise


# HTTP Triggers for On-Demand Operations

@function_app.route(
    route="reports/generate",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION
)
def generate_report_on_demand(req: func.HttpRequest) -> func.HttpResponse:
    """
    Generate quality report on demand
    Accepts JSON payload with report parameters
    """
    
    try:
        req_body = req.get_json()
        report_type = req_body.get("report_type", "quality_summary")
        date_range = req_body.get("date_range", 7)  # days
        
        logger.info(f"Generating on-demand report: {report_type}")
        
        if report_type == "quality_summary":
            report_data = _generate_quality_summary_report(date_range)
        elif report_type == "root_cause":
            report_data = _generate_root_cause_report(date_range)
        elif report_type == "cost_analysis":
            report_data = _generate_cost_analysis_report(date_range)
        else:
            return func.HttpResponse(
                json.dumps({"error": f"Unknown report type: {report_type}"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Store report and return URL
        report_url = _store_report_to_blob(report_data, f"{report_type}_on_demand")
        
        return func.HttpResponse(
            json.dumps({
                "report_url": report_url,
                "generated_at": datetime.now(datetime.UTC).isoformat(),
                "report_type": report_type
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"On-demand report generation failed: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@function_app.route(
    route="health",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS
)
def system_health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Comprehensive system health check endpoint
    Returns detailed health status for monitoring
    """
    
    try:
        health_status = {
            "timestamp": datetime.now(datetime.UTC).isoformat(),
            "overall_status": "healthy",
            "components": {}
        }
        
        # Database health
        db_health = check_database_health()
        health_status["components"]["database"] = db_health
        
        # LLM service health
        try:
            llm_judge = LLMJudge()
            llm_health = asyncio.run(llm_judge.health_check())
            health_status["components"]["llm_service"] = llm_health
        except Exception as e:
            health_status["components"]["llm_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Rules engine health
        try:
            rules_engine = RulesEngine()
            rules_metrics = rules_engine.get_performance_metrics()
            health_status["components"]["rules_engine"] = {
                "status": "healthy",
                "metrics": rules_metrics
            }
        except Exception as e:
            health_status["components"]["rules_engine"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
        
        # Determine overall status
        component_statuses = [comp.get("status", "unknown") for comp in health_status["components"].values()]
        if any(status == "unhealthy" for status in component_statuses):
            health_status["overall_status"] = "degraded"
        elif any(status == "unknown" for status in component_statuses):
            health_status["overall_status"] = "unknown"
        
        status_code = 200 if health_status["overall_status"] == "healthy" else 503
        
        return func.HttpResponse(
            json.dumps(health_status),
            status_code=status_code,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return func.HttpResponse(
            json.dumps({
                "overall_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(datetime.UTC).isoformat()
            }),
            status_code=500,
            mimetype="application/json"
        )


@function_app.route(
    route="golden-dataset/export",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION
)
def export_golden_dataset_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Export golden dataset for external use
    Supports JSON and CSV formats
    """
    
    try:
        req_body = req.get_json()
        format_type = req_body.get("format", "json")
        
        logger.info(f"Exporting golden dataset in {format_type} format")
        
        # Export dataset
        filename = export_golden_dataset(format_type)
        
        # Upload to blob storage
        blob_url = _upload_file_to_blob(filename, "golden-datasets")
        
        return func.HttpResponse(
            json.dumps({
                "export_url": blob_url,
                "filename": filename,
                "format": format_type,
                "exported_at": datetime.now(datetime.UTC).isoformat()
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Golden dataset export failed: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# Utility Functions

def _generate_root_cause_report(days_back: int = 7) -> Dict[str, Any]:
    """Generate comprehensive root cause analysis report"""
    
    cutoff_date = datetime.now(datetime.UTC) - timedelta(days=days_back)
    
    with get_db_context() as db:
        # Get flagged records summary
        flagged_summary = db.execute("""
            SELECT 
                qc.check_name,
                COUNT(*) as failure_count,
                AVG(qc.confidence_score) as avg_confidence,
                cr.source_connector,
                COUNT(DISTINCT cr.record_id) as unique_records
            FROM quality_check_records qc
            JOIN chunk_records cr ON qc.chunk_id = cr.id
            WHERE qc.status = 'fail' AND qc.executed_at >= :cutoff
            GROUP BY qc.check_name, cr.source_connector
            ORDER BY failure_count DESC
        """, {"cutoff": cutoff_date}).fetchall()
        
        # Get reviewer feedback summary
        reviewer_summary = db.execute("""
            SELECT 
                rr.decision,
                COUNT(*) as count,
                AVG(qc.confidence_score) as avg_confidence
            FROM review_records rr
            JOIN quality_check_records qc ON rr.chunk_id = qc.chunk_id
            WHERE rr.reviewed_at >= :cutoff AND qc.status = 'fail'
            GROUP BY rr.decision
        """, {"cutoff": cutoff_date}).fetchall()
        
        # Get dead letter analysis
        dead_letter_analysis = db.execute("""
            SELECT 
                error_type,
                source_connector,
                COUNT(*) as count,
                MIN(failed_at) as first_occurrence,
                MAX(failed_at) as last_occurrence
            FROM dead_letter_records
            WHERE failed_at >= :cutoff AND resolved = 0
            GROUP BY error_type, source_connector
            ORDER BY count DESC
        """, {"cutoff": cutoff_date}).fetchall()
    
    report = {
        "report_type": "root_cause_analysis",
        "period_start": cutoff_date.isoformat(),
        "period_end": datetime.now(datetime.UTC).isoformat(),
        "generated_at": datetime.now(datetime.UTC).isoformat(),
        "summary": {
            "total_failures": sum(row[1] for row in flagged_summary),
            "unique_failed_records": sum(row[4] for row in flagged_summary),
            "top_failing_check": flagged_summary[0][0] if flagged_summary else None,
            "total_dead_letters": sum(row[2] for row in dead_letter_analysis)
        },
        "quality_check_breakdown": [
            {
                "check_name": row[0],
                "failure_count": row[1],
                "avg_confidence": row[2],
                "source_connector": row[3],
                "unique_records": row[4]
            } for row in flagged_summary
        ],
        "reviewer_feedback": [
            {
                "decision": row[0],
                "count": row[1], 
                "avg_confidence": row[2]
            } for row in reviewer_summary
        ],
        "dead_letter_analysis": [
            {
                "error_type": row[0],
                "source_connector": row[1],
                "count": row[2],
                "first_occurrence": row[3].isoformat() if row[3] else None,
                "last_occurrence": row[4].isoformat() if row[4] else None
            } for row in dead_letter_analysis
        ]
    }
    
    return report


def _generate_quality_summary_report(days_back: int = 7) -> Dict[str, Any]:
    """Generate quality metrics summary report"""
    
    cutoff_date = datetime.now(datetime.UTC) - timedelta(days=days_back)
    
    with get_db_context() as db:
        # Basic metrics
        total_chunks = db.query(ChunkRecord).filter(
            ChunkRecord.processed_at >= cutoff_date
        ).count()
        
        total_checks = db.query(QualityCheckRecord).filter(
            QualityCheckRecord.executed_at >= cutoff_date
        ).count()
        
        failed_checks = db.query(QualityCheckRecord).filter(
            QualityCheckRecord.executed_at >= cutoff_date,
            QualityCheckRecord.status == FlagStatus.FAIL.value
        ).count()
        
        # Daily trends
        daily_trends = db.execute("""
            SELECT 
                DATE(processed_at) as date,
                COUNT(*) as chunks_processed,
                COUNT(CASE WHEN qc.status = 'fail' THEN 1 END) as chunks_flagged
            FROM chunk_records cr
            LEFT JOIN quality_check_records qc ON cr.id = qc.chunk_id
            WHERE cr.processed_at >= :cutoff
            GROUP BY DATE(processed_at)
            ORDER BY date
        """, {"cutoff": cutoff_date}).fetchall()
    
    return {
        "report_type": "quality_summary",
        "period_start": cutoff_date.isoformat(),
        "period_end": datetime.now(datetime.UTC).isoformat(),
        "generated_at": datetime.now(datetime.UTC).isoformat(),
        "metrics": {
            "total_chunks_processed": total_chunks,
            "total_quality_checks": total_checks,
            "failed_checks": failed_checks,
            "pass_rate": ((total_checks - failed_checks) / total_checks * 100) if total_checks > 0 else 0
        },
        "daily_trends": [
            {
                "date": row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                "chunks_processed": row[1],
                "chunks_flagged": row[2] or 0
            } for row in daily_trends
        ]
    }


def _generate_cost_analysis_report(days_back: int = 30) -> Dict[str, Any]:
    """Generate LLM cost analysis report"""
    
    # This would integrate with actual LLM cost tracking
    # For now, return placeholder structure
    
    return {
        "report_type": "cost_analysis",
        "period_start": (datetime.now(datetime.UTC) - timedelta(days=days_back)).isoformat(),
        "period_end": datetime.now(datetime.UTC).isoformat(),
        "generated_at": datetime.now(datetime.UTC).isoformat(),
        "cost_metrics": {
            "total_llm_requests": 0,  # TODO: Get from LLM judge
            "total_tokens_used": 0,
            "total_cost_usd": 0.0,
            "avg_cost_per_request": 0.0,
            "cost_by_model": {},
            "daily_costs": []
        },
        "budget_analysis": {
            "monthly_budget": 2000.0,
            "current_month_spend": 0.0,
            "projected_month_end": 0.0,
            "budget_utilization": 0.0
        }
    }


def _store_report_to_blob(report_data: Dict[str, Any], report_type: str) -> str:
    """Store report data to Azure Blob Storage"""
    
    try:
        # TODO: Configure blob storage connection
        blob_service_client = BlobServiceClient.from_connection_string(
            "DefaultEndpointsProtocol=https;AccountName=yourstorageaccount;AccountKey=yourkey"
        )
        
        # Generate filename
        timestamp = datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_{timestamp}.json"
        
        # Upload to blob
        blob_client = blob_service_client.get_blob_client(
            container="reports",
            blob=filename
        )
        
        blob_client.upload_blob(
            json.dumps(report_data, indent=2),
            overwrite=True
        )
        
        return f"https://yourstorageaccount.blob.core.windows.net/reports/{filename}"
        
    except Exception as e:
        logger.error(f"Failed to store report to blob: {e}")
        return ""


def _upload_file_to_blob(local_filename: str, container: str) -> str:
    """Upload local file to blob storage"""
    
    try:
        # TODO: Configure blob storage connection
        blob_service_client = BlobServiceClient.from_connection_string(
            "DefaultEndpointsProtocol=https;AccountName=yourstorageaccount;AccountKey=yourkey"
        )
        
        with open(local_filename, 'rb') as data:
            blob_client = blob_service_client.get_blob_client(
                container=container,
                blob=local_filename
            )
            blob_client.upload_blob(data, overwrite=True)
        
        return f"https://yourstorageaccount.blob.core.windows.net/{container}/{local_filename}"
        
    except Exception as e:
        logger.error(f"Failed to upload file to blob: {e}")
        return ""


def _store_learning_results(results: Dict[str, Any]) -> None:
    """Store learning cycle results for analysis"""
    
    try:
        timestamp = datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"learning_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Upload to blob storage
        _upload_file_to_blob(filename, "learning-results")
        
    except Exception as e:
        logger.error(f"Failed to store learning results: {e}")


async def _send_report_notification(report_url: str, report_type: str) -> None:
    """Send notification about generated report"""
    
    try:
        from alerts import AlertManager, AlertType, AlertSeverity
        
        alert_manager = AlertManager()
        await alert_manager.trigger_alert(
            AlertType.SYSTEM_HEALTH_DEGRADED,
            AlertSeverity.LOW,
            f"Weekly {report_type} report generated and available",
            {"report_url": report_url}
        )
        
    except Exception as e:
        logger.error(f"Failed to send report notification: {e}")


def _calculate_daily_cost(cost_metrics: Dict[str, Any]) -> float:
    """Calculate daily LLM cost from metrics"""
    # TODO: Implement actual daily cost calculation
    return cost_metrics.get("total_cost_usd", 0.0)


def _calculate_monthly_cost(cost_metrics: Dict[str, Any]) -> float:
    """Calculate monthly LLM cost from metrics"""
    # TODO: Implement actual monthly cost calculation
    return cost_metrics.get("total_cost_usd", 0.0)


def _update_database_statistics() -> None:
    """Update database statistics for Azure SQL"""
    
    try:
        if "azure" in settings.database_url.lower():
            with get_db_context() as db:
                # Update statistics for better query performance
                db.execute("UPDATE STATISTICS chunk_records")
                db.execute("UPDATE STATISTICS quality_check_records")
                db.execute("UPDATE STATISTICS review_records")
                
    except Exception as e:
        logger.warning(f"Failed to update database statistics: {e}")


# Event Grid Trigger (for external system integration)

@function_app.event_grid_trigger(arg_name="event")
def process_external_event(event: func.EventGridEvent) -> None:
    """
    Process events from external systems (e.g., Lucy AI updates)
    Triggers quality checks on external content updates
    """
    
    try:
        logger.info(f"Processing external event: {event.event_type}")
        
        event_data = event.get_json()
        
        if event.event_type == "Lucy.ContentUpdated":
            # Process content update from Lucy
            _process_lucy_content_update(event_data)
        elif event.event_type == "Connector.BulkUpdate":
            # Process bulk updates from connectors
            _process_connector_bulk_update(event_data)
        else:
            logger.warning(f"Unknown event type: {event.event_type}")
            
    except Exception as e:
        logger.error(f"External event processing failed: {e}")
        raise


def _process_lucy_content_update(event_data: Dict[str, Any]) -> None:
    """Process content update from Lucy AI system"""
    
    # TODO: Implement Lucy integration
    logger.info(f"Processing Lucy content update: {event_data}")


def _process_connector_bulk_update(event_data: Dict[str, Any]) -> None:
    """Process bulk update from connector systems"""
    
    # TODO: Implement connector bulk processing
    logger.info(f"Processing connector bulk update: {event_data}")
