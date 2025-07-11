#!/usr/bin/env python3
"""
Improved Tags Evaluation Pipeline Design
As designed by OpenAI Engineer approach

Key Principles:
1. Binary automated decision: APPROVED or FLAGGED
2. Separate interfaces for different workflows
3. Clear human-in-the-loop process
4. Logical separation of concerns
"""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime, UTC
from dataclasses import dataclass
import json

class RecordStatus(str, Enum):
    """Clear binary status from automated pipeline"""
    APPROVED = "approved"      # Ready for production
    FLAGGED = "flagged"        # Needs human review
    REJECTED = "rejected"      # Permanently rejected
    PENDING_REVIEW = "pending_review"  # In human review process

class IssueSeverity(str, Enum):
    """Issue severity for prioritization"""
    CRITICAL = "critical"      # Blocks production completely
    HIGH = "high"             # Significant quality issues
    MEDIUM = "medium"         # Minor improvements needed
    LOW = "low"               # Cosmetic/optional fixes

class ReviewAction(str, Enum):
    """Available reviewer actions"""
    APPROVE = "approve"        # Move to production
    REJECT = "reject"          # Permanently reject
    REQUEST_CHANGES = "request_changes"  # Send back for fixes
    ESCALATE = "escalate"      # Flag for senior review

@dataclass
class QualityDecision:
    """Result of automated quality pipeline"""
    status: RecordStatus
    quality_score: float
    confidence: float
    issues: List[Dict]
    auto_fix_suggestions: List[str]
    reasoning: str
    severity: IssueSeverity

@dataclass
class ReviewDecision:
    """Human reviewer decision"""
    action: ReviewAction
    reviewer_id: str
    comments: Optional[str]
    reviewed_at: datetime
    estimated_fix_time: Optional[int]  # minutes

class ImprovedQualityPipeline:
    """Redesigned quality evaluation pipeline"""
    
    def __init__(self):
        self.quality_thresholds = {
            'approval_score': 80,      # Minimum score for auto-approval
            'critical_threshold': 50,   # Below this = critical severity
            'high_threshold': 70,       # Below this = high severity
        }
    
    def evaluate_content(self, content: str, tags: List[str], 
                        source_connector: str) -> QualityDecision:
        """
        Core evaluation logic - makes binary APPROVED/FLAGGED decision
        """
        # Run all quality checks
        rules_result = self._run_rules_engine(content, tags, source_connector)
        llm_result = self._run_llm_judge(content, tags)
        
        # Calculate composite score
        quality_score = (rules_result['score'] * 0.6 + llm_result['score'] * 0.4)
        
        # Collect all issues
        all_issues = rules_result['issues'] + llm_result['issues']
        critical_issues = [i for i in all_issues if i.get('severity') == 'critical']
        
        # Binary decision logic
        if quality_score >= self.quality_thresholds['approval_score'] and not critical_issues:
            status = RecordStatus.APPROVED
            severity = IssueSeverity.LOW
        else:
            status = RecordStatus.FLAGGED
            # Determine severity for flagged records
            if quality_score < self.quality_thresholds['critical_threshold'] or critical_issues:
                severity = IssueSeverity.CRITICAL
            elif quality_score < self.quality_thresholds['high_threshold']:
                severity = IssueSeverity.HIGH
            else:
                severity = IssueSeverity.MEDIUM
        
        return QualityDecision(
            status=status,
            quality_score=quality_score,
            confidence=min(rules_result['confidence'], llm_result['confidence']),
            issues=all_issues,
            auto_fix_suggestions=self._generate_auto_fixes(all_issues),
            reasoning=self._generate_reasoning(rules_result, llm_result, status),
            severity=severity
        )
    
    def _run_rules_engine(self, content: str, tags: List[str], source: str) -> Dict:
        """Fast, deterministic quality checks"""
        issues = []
        score = 100
        
        # Tag count validation
        if len(tags) < 3:
            issues.append({
                'type': 'insufficient_tags',
                'severity': 'high',
                'description': f'Only {len(tags)} tags provided, need at least 3',
                'auto_fixable': True
            })
            score -= 20
        
        # Generic tag detection
        generic_tags = ['misc', 'document', 'text', 'info', 'general', 'file']
        generic_count = sum(1 for tag in tags if tag.lower() in generic_tags)
        if generic_count > len(tags) * 0.5:
            issues.append({
                'type': 'generic_tags',
                'severity': 'medium',
                'description': f'{generic_count} out of {len(tags)} tags are generic',
                'auto_fixable': True
            })
            score -= 15
        
        # Content length validation
        if len(content) < 100:
            issues.append({
                'type': 'content_too_short',
                'severity': 'critical',
                'description': f'Content only {len(content)} characters',
                'auto_fixable': False
            })
            score -= 30
        
        return {
            'score': max(0, score),
            'confidence': 0.9,
            'issues': issues
        }
    
    def _run_llm_judge(self, content: str, tags: List[str]) -> Dict:
        """LLM-based semantic validation"""
        issues = []
        score = 100
        
        # Simulate LLM evaluation
        # Tag-content relevance
        content_words = set(content.lower().split())
        tag_words = set(' '.join(tags).lower().split())
        overlap = len(content_words & tag_words) / max(len(tag_words), 1)
        
        if overlap < 0.3:
            issues.append({
                'type': 'tag_content_mismatch',
                'severity': 'high',
                'description': f'Low tag-content overlap ({overlap:.1%})',
                'auto_fixable': True
            })
            score -= 25
        
        return {
            'score': max(0, score),
            'confidence': 0.8,
            'issues': issues
        }
    
    def _generate_auto_fixes(self, issues: List[Dict]) -> List[str]:
        """Generate actionable auto-fix suggestions"""
        suggestions = []
        
        for issue in issues:
            if issue.get('auto_fixable'):
                if issue['type'] == 'insufficient_tags':
                    suggestions.append("Add more specific, descriptive tags related to content topics")
                elif issue['type'] == 'generic_tags':
                    suggestions.append("Replace generic tags (misc, document, text) with specific terms")
                elif issue['type'] == 'tag_content_mismatch':
                    suggestions.append("Review tags to ensure they accurately reflect content themes")
        
        return suggestions
    
    def _generate_reasoning(self, rules_result: Dict, llm_result: Dict, status: RecordStatus) -> str:
        """Generate human-readable reasoning for the decision"""
        if status == RecordStatus.APPROVED:
            return f"High quality content (Rules: {rules_result['score']}/100, LLM: {llm_result['score']}/100). No critical issues detected."
        else:
            issue_count = len(rules_result['issues']) + len(llm_result['issues'])
            return f"Quality concerns detected ({issue_count} issues). Rules score: {rules_result['score']}/100, LLM score: {llm_result['score']}/100."

class ReviewQueue:
    """Manages flagged records for human review"""
    
    def __init__(self):
        self.queue = []
        self.reviewers = {}
    
    def add_flagged_record(self, record_id: str, decision: QualityDecision):
        """Add flagged record to review queue"""
        queue_item = {
            'record_id': record_id,
            'decision': decision,
            'added_at': datetime.now(UTC),
            'priority': self._calculate_priority(decision.severity),
            'estimated_review_time': self._estimate_review_time(decision),
            'status': 'pending_assignment'
        }
        self.queue.append(queue_item)
        self._sort_queue_by_priority()
    
    def assign_reviewer(self, record_id: str, reviewer_id: str):
        """Assign flagged record to human reviewer"""
        for item in self.queue:
            if item['record_id'] == record_id:
                item['assigned_to'] = reviewer_id
                item['assigned_at'] = datetime.now(UTC)
                item['status'] = 'in_review'
                break
    
    def process_review(self, record_id: str, review_decision: ReviewDecision) -> RecordStatus:
        """Process human review decision"""
        for item in self.queue:
            if item['record_id'] == record_id:
                item['review_decision'] = review_decision
                item['completed_at'] = datetime.now(UTC)
                
                # Determine final status
                if review_decision.action == ReviewAction.APPROVE:
                    final_status = RecordStatus.APPROVED
                elif review_decision.action == ReviewAction.REJECT:
                    final_status = RecordStatus.REJECTED
                else:
                    final_status = RecordStatus.PENDING_REVIEW
                
                item['final_status'] = final_status
                return final_status
    
    def get_queue_by_priority(self) -> List[Dict]:
        """Get review queue sorted by priority"""
        return sorted([item for item in self.queue if item['status'] != 'completed'], 
                     key=lambda x: x['priority'])
    
    def _calculate_priority(self, severity: IssueSeverity) -> int:
        """Calculate priority score (lower = higher priority)"""
        priority_map = {
            IssueSeverity.CRITICAL: 1,
            IssueSeverity.HIGH: 2,
            IssueSeverity.MEDIUM: 3,
            IssueSeverity.LOW: 4
        }
        return priority_map.get(severity, 5)
    
    def _estimate_review_time(self, decision: QualityDecision) -> int:
        """Estimate review time in minutes"""
        base_time = 5  # Base 5 minutes
        if decision.severity == IssueSeverity.CRITICAL:
            return base_time + 10
        elif decision.severity == IssueSeverity.HIGH:
            return base_time + 5
        else:
            return base_time
    
    def _sort_queue_by_priority(self):
        """Sort queue by priority and age"""
        self.queue.sort(key=lambda x: (x['priority'], x['added_at']))

class ProductionDashboard:
    """Interface for approved, production-ready content"""
    
    def get_approved_records(self, filters: Dict = None, page: int = 1, page_size: int = 25):
        """Get only approved records for production use"""
        # This would query only records with status = 'approved'
        pass
    
    def get_quality_metrics(self):
        """Get quality metrics for approved content"""
        # Average quality scores, tag distribution, etc.
        pass

class QualityControlCenter:
    """Analytics and management interface"""
    
    def get_status_distribution(self):
        """Get distribution of record statuses"""
        pass
    
    def get_reviewer_performance(self):
        """Get reviewer performance metrics"""
        pass
    
    def get_quality_trends(self):
        """Get quality trends over time"""
        pass

# Example usage
def example_improved_workflow():
    """Example of how the improved pipeline works"""
    
    pipeline = ImprovedQualityPipeline()
    review_queue = ReviewQueue()
    
    # 1. Content comes in
    content = "Machine learning best practices for production deployment"
    tags = ["ml", "production", "deployment", "best-practices"]
    
    # 2. Automated evaluation
    decision = pipeline.evaluate_content(content, tags, "sharepoint")
    
    # 3. Route based on decision
    if decision.status == RecordStatus.APPROVED:
        print(f"✅ AUTO-APPROVED: Quality score {decision.quality_score}/100")
        # → Goes directly to Production Dashboard
    
    elif decision.status == RecordStatus.FLAGGED:
        print(f"🚩 FLAGGED: {len(decision.issues)} issues found")
        # → Goes to Review Queue
        review_queue.add_flagged_record("record-123", decision)
        
        # 4. Human review process
        review_queue.assign_reviewer("record-123", "reviewer-alice")
        
        # 5. Reviewer makes decision
        review_decision = ReviewDecision(
            action=ReviewAction.APPROVE,
            reviewer_id="reviewer-alice",
            comments="Fixed tag relevance, now ready for production",
            reviewed_at=datetime.now(UTC)
        )
        
        final_status = review_queue.process_review("record-123", review_decision)
        print(f"👤 HUMAN DECISION: {final_status}")

if __name__ == "__main__":
    example_improved_workflow() 