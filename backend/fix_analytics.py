#!/usr/bin/env python3
"""Fix for analytics dashboard 500 error"""

import re

# Read the current file
with open('run_local.py', 'r') as f:
    content = f.read()

# Replace the problematic SQL query
old_query = '''cursor.execute('''
            SELECT 
                CASE 
                    WHEN quality_level = 'low' THEN 'Content Quality Issues'
                    WHEN quality_level = 'medium' THEN 'Minor Issues'
                    WHEN overall_status = 'flagged' THEN 'Flagged Records'
                    WHEN overall_status = 'under_review' THEN 'Under Review'
                    ELSE 'Other Issues'
                END as issue_type,
                COUNT(*) as count
            FROM processed_records
            WHERE DATE(created_at) >= ? AND (quality_level = 'low' OR overall_status IN ('flagged', 'under_review'))
            GROUP BY issue_type
            ORDER BY count DESC
        ''', (week_ago,))'''

new_query = '''cursor.execute('''
            SELECT 
                CASE 
                    WHEN quality_level = 'low' THEN 'Content Quality Issues'
                    WHEN quality_level = 'medium' THEN 'Minor Issues'
                    WHEN quality_score < 60 THEN 'Low Quality Records'
                    WHEN quality_score < 80 THEN 'Medium Quality Records'
                    ELSE 'Other Issues'
                END as issue_type,
                COUNT(*) as count
            FROM processed_records
            WHERE DATE(created_at) >= ? AND quality_level IN ('low', 'medium')
            GROUP BY issue_type
            ORDER BY count DESC
        ''', (week_ago,))'''

# Replace the content
content = content.replace(old_query, new_query)

# Write back the fixed content
with open('run_local.py', 'w') as f:
    f.write(content)

print("Fixed analytics SQL query - removed overall_status references") 