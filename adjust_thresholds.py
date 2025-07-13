#!/usr/bin/env python3
"""
Simple script to adjust the main approval threshold
This shows you how to change the threshold that controls approval/flagging
"""

import os
import sys

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.config import get_settings

def show_current_thresholds():
    """Show current threshold values"""
    settings = get_settings()
    
    print("🔧 CURRENT THRESHOLD VALUES")
    print("=" * 50)
    print(f"Main Approval Threshold: {settings.approval_quality_score_threshold}")
    print(f"LLM Confidence Threshold: {settings.llm_confidence_threshold}")
    print(f"Stopword Threshold: {settings.stopword_threshold}")
    print(f"Min Tag Count: {settings.min_tag_count}")
    print(f"Max Tag Count: {settings.max_tag_count}")
    print(f"Semantic Relevance Threshold: {settings.semantic_relevance_threshold}")
    print(f"Domain Relevance Threshold: {settings.domain_relevance_threshold}")
    print(f"Tag Specificity Threshold: {settings.tag_specificity_threshold}")
    print(f"Context Coherence Threshold: {settings.context_coherence_threshold}")
    print()

def adjust_main_threshold(new_value: float):
    """Show how to adjust the main approval threshold"""
    print(f"🎯 TO ADJUST MAIN APPROVAL THRESHOLD TO {new_value}:")
    print("=" * 60)
    print("1. Open file: backend/app/core/config.py")
    print("2. Find line with: approval_quality_score_threshold: float = 70.0")
    print(f"3. Change to: approval_quality_score_threshold: float = {new_value}")
    print("4. Restart the backend server")
    print()
    print("📝 WHAT THIS MEANS:")
    if new_value > 70:
        print(f"   • Records need quality_score >= {new_value} to be approved")
        print(f"   • System becomes MORE STRICT (fewer approvals)")
    else:
        print(f"   • Records need quality_score >= {new_value} to be approved")
        print(f"   • System becomes MORE LENIENT (more approvals)")
    print()

def show_quality_score_formula():
    """Show how quality score is calculated"""
    print("🧮 QUALITY SCORE FORMULA:")
    print("=" * 30)
    print("quality_score = (rules_engine_confidence * 0.6 + llm_confidence * 0.4) * 100")
    print()
    print("📊 COMPONENTS:")
    print("   • Rules Engine Confidence (60% weight)")
    print("   • LLM Confidence (40% weight)")
    print()
    print("🎯 APPROVAL LOGIC:")
    print("   • quality_score >= threshold → APPROVED")
    print("   • quality_score < threshold → FLAGGED")
    print()

if __name__ == "__main__":
    print("🚀 INDEXING QA THRESHOLD ADJUSTMENT TOOL")
    print("=" * 50)
    print()
    
    show_current_thresholds()
    show_quality_score_formula()
    
    # Show examples
    print("💡 EXAMPLE ADJUSTMENTS:")
    print("=" * 30)
    adjust_main_threshold(60)  # More lenient
    adjust_main_threshold(80)  # More strict
    
    print("✅ DONE! You can now adjust thresholds from one central location.")
    print("   All thresholds are in: backend/app/core/config.py") 