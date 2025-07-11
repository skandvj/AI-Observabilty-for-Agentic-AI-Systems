#!/usr/bin/env python3
"""
Simple implementation of improved pipeline endpoints
"""

from fastapi import FastAPI, HTTPException
from typing import Optional, List, Dict
import sqlite3
import json
from datetime import datetime, UTC
from collections import defaultdict

# Simple endpoints that can be added to the main server

def get_approved_records_simple(page: int = 1, page_size: int = 25):
    """Get production-ready approved records"""
    try:
        conn = sqlite3.connect('indexing_qa.db')
        cursor = conn.cursor()
        
        # Simple query for high-quality records (score >= 80)
        offset = (page - 1) * page_size
        
        cursor.execute("""
            SELECT id, record_id, content, tags, source_connector, 
                   quality_score, created_at, content_metadata
            FROM processed_records 
            WHERE quality_score >= 80
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """, (page_size, offset))
        
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            records.append({
                'id': row[0],
                'recordId': row[1],
                'content': row[2][:200] + '...' if len(row[2]) > 200 else row[2],
                'tags': json.loads(row[3]) if row[3] else [],
                'sourceConnector': row[4],
                'qualityScore': row[5],
                'createdAt': row[6],
                'status': 'approved'
            })
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM processed_records WHERE quality_score >= 80")
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'records': records,
            'pagination': {
                'page': page,
                'pageSize': page_size,
                'total': total,
                'totalPages': (total + page_size - 1) // page_size
            },
            'summary': {
                'totalApproved': total,
                'avgQualityScore': sum(r['qualityScore'] for r in records) / len(records) if records else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

def get_review_queue_simple():
    """Get records needing review (score < 80)"""
    try:
        conn = sqlite3.connect('indexing_qa.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, record_id, content, tags, source_connector, 
                   quality_score, quality_checks, created_at
            FROM processed_records 
            WHERE quality_score < 80
            ORDER BY quality_score ASC, created_at DESC
        """)
        
        rows = cursor.fetchall()
        
        review_items = []
        for row in rows:
            # Extract issues from quality_checks
            quality_checks = json.loads(row[6]) if row[6] else []
            issues = []
            
            for check in quality_checks:
                if check.get('status') == 'fail':
                    issues.append({
                        'type': check.get('check_name', 'unknown'),
                        'description': check.get('failure_reason', 'Quality check failed')
                    })
            
            # Determine severity
            severity = 'critical' if row[5] < 50 else ('high' if row[5] < 70 else 'medium')
            
            review_items.append({
                'id': row[0],
                'recordId': row[1],
                'content': row[2][:300] + '...' if len(row[2]) > 300 else row[2],
                'tags': json.loads(row[3]) if row[3] else [],
                'sourceConnector': row[4],
                'qualityScore': row[5],
                'severity': severity,
                'issues': issues,
                'issueCount': len(issues),
                'createdAt': row[7],
                'status': 'flagged'
            })
        
        conn.close()
        
        # Group by severity
        summary = {
            'totalFlagged': len(review_items),
            'critical': len([item for item in review_items if item['severity'] == 'critical']),
            'high': len([item for item in review_items if item['severity'] == 'high']),
            'medium': len([item for item in review_items if item['severity'] == 'medium'])
        }
        
        return {
            'reviewQueue': review_items,
            'summary': summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

def get_quality_control_dashboard_simple():
    """Get quality control overview"""
    try:
        conn = sqlite3.connect('indexing_qa.db')
        cursor = conn.cursor()
        
        # Status distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN quality_score >= 80 THEN 'approved'
                    WHEN quality_score < 80 THEN 'flagged'
                    ELSE 'unknown'
                END as status,
                COUNT(*) as count
            FROM processed_records
            GROUP BY status
        """)
        
        status_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Quality trends (last 7 days)
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                AVG(quality_score) as avg_quality,
                COUNT(*) as total_records
            FROM processed_records 
            WHERE DATE(created_at) >= DATE('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        
        quality_trends = []
        for row in cursor.fetchall():
            quality_trends.append({
                'date': row[0],
                'avgQuality': round(row[1], 1) if row[1] else 0,
                'totalRecords': row[2]
            })
        
        # Top failure reasons
        cursor.execute("""
            SELECT quality_checks 
            FROM processed_records 
            WHERE quality_checks IS NOT NULL AND quality_score < 80
        """)
        
        failure_reasons = defaultdict(int)
        for row in cursor.fetchall():
            try:
                checks = json.loads(row[0])
                for check in checks:
                    if check.get('status') == 'fail':
                        check_name = check.get('check_name', 'unknown')
                        # Make names more user-friendly
                        friendly_names = {
                            'empty_tags': 'Missing Tags',
                            'tag_count_validation': 'Tag Count Issues',
                            'text_quality': 'Text Quality Issues',
                            'stopwords_detection': 'Generic Tags',
                            'spam_pattern_detection': 'Spam/Test Content',
                            'duplicate_content_detection': 'Duplicate Content',
                            'tag_text_relevance': 'Tag-Content Mismatch'
                        }
                        friendly_name = friendly_names.get(check_name, check_name.replace('_', ' ').title())
                        failure_reasons[friendly_name] += 1
            except:
                continue
        
        top_failures = sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True)[:10]
        top_failures = [{'reason': reason, 'count': count} for reason, count in top_failures]
        
        # System performance
        total_records = sum(status_distribution.values())
        approval_rate = (status_distribution.get('approved', 0) / total_records * 100) if total_records > 0 else 0
        
        conn.close()
        
        return {
            'statusDistribution': status_distribution,
            'qualityTrends': quality_trends,
            'topFailureReasons': top_failures,
            'systemPerformance': {
                'totalRecords': total_records,
                'approvalRate': round(approval_rate, 1),
                'recordsNeedingReview': status_distribution.get('flagged', 0)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Test the functions
if __name__ == "__main__":
    print("Testing approved records...")
    result1 = get_approved_records_simple()
    print(f"Found {len(result1['records'])} approved records")
    
    print("\nTesting review queue...")
    result2 = get_review_queue_simple()
    print(f"Found {len(result2['reviewQueue'])} flagged records")
    
    print("\nTesting quality control dashboard...")
    result3 = get_quality_control_dashboard_simple()
    print(f"Status distribution: {result3['statusDistribution']}") 