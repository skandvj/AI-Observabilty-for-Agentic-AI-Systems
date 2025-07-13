"""
LLM Semantic Judge for Indexing QA Observability Tool
Provides intelligent semantic validation of tags vs content
Optimized for cost control and reliability with fallback mechanisms
"""

import asyncio
import time
import json
import re
from typing import List, Dict, Optional, Any
from datetime import datetime, UTC
import logging

# LLM API imports with graceful fallback for local development
try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    AsyncOpenAI = None
    OPENAI_AVAILABLE = False

try:
    import anthropic  # type: ignore
    from anthropic import AsyncAnthropic  # type: ignore
    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None
    AsyncAnthropic = None
    ANTHROPIC_AVAILABLE = False

from ..models.models import QualityCheckResult, FlagStatus, mask_pii_text
from ..core.config import get_settings


class LLMJudge:
    """
    Semantic validation engine using LLM to assess tag-content alignment
    Includes PII masking, cost optimization, and fallback strategies
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM clients
        self._init_llm_clients()
        
        # Performance and cost tracking
        self.request_count = 0
        self.total_tokens_used = 0
        self.total_cost_usd = 0.0
        self.response_times = []
        
        # Circuit breaker for LLM failures
        self.failure_count = 0
        self.max_failures = 5
        self.circuit_breaker_timeout = 300  # 5 minutes
        self.last_failure_time = None
        
        # Fallback mechanism
        self.use_fallback = False
        
    def _init_llm_clients(self):
        """Initialize LLM provider clients"""
        try:
            # Check if LLM validation is enabled
            if not getattr(self.settings, 'enable_llm_validation', True):
                self.logger.info("LLM validation disabled in settings")
                self.use_fallback = True
                self.provider = "fallback"
                return
            
            # Try OpenAI first
            if OPENAI_AVAILABLE and AsyncOpenAI and self.settings.openai_api_key and self.settings.openai_api_key != "your-openai-api-key-here":
                self.openai_client = AsyncOpenAI(api_key=self.settings.openai_api_key)
                self.provider = "openai"
                self.logger.info("OpenAI client initialized successfully")
                
            # Try Anthropic if OpenAI not available
            elif ANTHROPIC_AVAILABLE and AsyncAnthropic and self.settings.anthropic_api_key and self.settings.anthropic_api_key != "your-anthropic-api-key-here":
                self.anthropic_client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)
                self.provider = "anthropic"
                self.logger.info("Anthropic client initialized successfully")
                
            else:
                # Fallback mode
                self.use_fallback = True
                self.provider = "fallback"
                if not OPENAI_AVAILABLE and not ANTHROPIC_AVAILABLE:
                    self.logger.warning("No LLM libraries available. Install 'openai' and/or 'anthropic' packages.")
                else:
                    self.logger.warning("No valid API keys configured. Using fallback mode.")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM client: {e}")
            self.use_fallback = True
            self.provider = "fallback"
    
    async def check_chunk(self, text: str, tags: List[str]) -> QualityCheckResult:
        """
        Main entry point for LLM semantic validation
        Includes PII masking and fallback logic
        """
        start_time = time.time()
        
        # Check circuit breaker
        if self._is_circuit_open():
            return self._fallback_check(text, tags, "Circuit breaker open")
        
        try:
            # Mask PII before sending to LLM
            masked_text = mask_pii_text(text)
            
            # Check if content is too long/short for meaningful analysis
            if len(masked_text.strip()) < self.settings.llm_fallback_min_text_length:
                return QualityCheckResult(
                    check_name="llm_semantic_validation",
                    status=FlagStatus.PASS,
                    confidence_score=self.settings.llm_fallback_confidence_low,
                    failure_reason="Text too short for semantic analysis",
                    check_metadata={"skipped_reason": "text_too_short", "text_length": len(text)}
                )
            
            # Run LLM validation with proper model selection
            if self.provider == "openai":
                result = await self._check_with_openai(masked_text, tags)
            elif self.provider == "anthropic":
                result = await self._check_with_anthropic(masked_text, tags)
            else:
                return self._fallback_check(text, tags, "No LLM provider available")
            
            # Reset failure count on success
            self.failure_count = 0
            
            # Track performance
            processing_time = (time.time() - start_time) * 1000
            self.response_times.append(processing_time)
            if result.check_metadata is None:
                result.check_metadata = {}
            result.check_metadata["processing_time_ms"] = processing_time
            
            return result
            
        except Exception as e:
            self.logger.error(f"LLM validation failed: {e}")
            self._record_failure()
            return self._fallback_check(text, tags, f"LLM error: {str(e)}")
    
    async def _check_with_openai(self, masked_text: str, tags: List[str]) -> QualityCheckResult:
        """OpenAI GPT-based semantic validation"""
        
        prompt = self._create_optimized_prompt(masked_text, tags)
        
        try:
            # Use a more compatible model and remove response_format for better compatibility
            model = "gpt-3.5-turbo" if "gpt-4" in getattr(self.settings, 'openai_model', 'gpt-3.5-turbo') else getattr(self.settings, 'openai_model', 'gpt-3.5-turbo')
            
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.settings.openai_max_tokens,
                temperature=self.settings.openai_temperature
                # Removed response_format for better compatibility
            )
            
            # Track token usage and cost
            usage = response.usage
            if usage:
                self.total_tokens_used += usage.total_tokens
                self.request_count += 1
                
                # Estimate cost (GPT-3.5 pricing as of 2024)
                input_cost = usage.prompt_tokens * 0.0000015  # $0.0015/1K tokens
                output_cost = usage.completion_tokens * 0.000002  # $0.002/1K tokens
                request_cost = input_cost + output_cost
                self.total_cost_usd += request_cost
            else:
                request_cost = 0.0
            
            # Parse response
            content = response.choices[0].message.content
            if content:
                result_data = json.loads(content)
            else:
                raise Exception("Empty response from OpenAI")
            
            return self._parse_llm_response(result_data, {
                "model": model,
                "tokens_used": usage.total_tokens if usage else 0,
                "cost_usd": request_cost,
                "provider": "openai"
            })
            
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from OpenAI: {e}")
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")
    
    async def _check_with_anthropic(self, masked_text: str, tags: List[str]) -> QualityCheckResult:
        """Anthropic Claude-based semantic validation"""
        
        prompt = self._create_optimized_prompt(masked_text, tags)
        
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",  # Fastest, cheapest model
                max_tokens=self.settings.anthropic_max_tokens,
                temperature=getattr(self.settings, 'anthropic_temperature', 0.1),
                system=self._get_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Track usage
            self.request_count += 1
            
            # Estimate cost (Claude pricing)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            request_cost = (input_tokens * 0.00025) + (output_tokens * 0.00125)  # Claude Haiku pricing
            self.total_cost_usd += request_cost
            
            # Parse response
            content = response.content[0].text
            if content:
                result_data = json.loads(content)
            else:
                raise Exception("Empty response from Anthropic")
            
            return self._parse_llm_response(result_data, {
                "model": "claude-3-haiku",
                "tokens_used": input_tokens + output_tokens,
                "cost_usd": request_cost,
                "provider": "anthropic"
            })
            
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from Anthropic: {e}")
        except Exception as e:
            raise Exception(f"Anthropic API error: {e}")
    
    def _create_optimized_prompt(self, masked_text: str, tags: List[str]) -> str:
        """
        Create cost-optimized prompt for tag validation
        Designed to minimize token usage while maximizing accuracy
        """
        
        # Truncate text if too long to control costs
        max_text_length = 2000
        if len(masked_text) > max_text_length:
            masked_text = masked_text[:max_text_length] + "... [TRUNCATED]"
        
        tags_str = ", ".join(f'"{tag}"' for tag in tags)
        
        return f"""Analyze if these tags accurately describe the content:

CONTENT:
{masked_text}

TAGS: {tags_str}

Evaluate each tag and respond with JSON:
{{
  "overall_assessment": "ACCURATE" or "INACCURATE", 
  "confidence": 0.0-1.0,
  "issues": [
    {{"tag": "tag_name", "problem": "brief_issue_description"}}
  ],
  "reasoning": "brief explanation"
}}

Focus on:
1. Do tags match the actual content topics?
2. Are tags too generic/vague for this specific content?
3. Are there obvious mismatches between tags and content?
4. Are critical topics missing from tags?

Be strict - only mark ACCURATE if tags genuinely represent the content well."""
    
    def _get_system_prompt(self) -> str:
        """System prompt optimized for tag validation task"""
        return """You are a content quality analyst for an enterprise knowledge base. Your job is to validate whether content tags accurately represent the document content.

Key principles:
- Be precise and objective
- Focus on semantic accuracy, not perfect matches
- Consider business context (documents, policies, procedures)
- Flag obvious mismatches or overly generic tags
- Always respond with valid JSON
- Keep responses concise to minimize cost

Quality standards:
- Tags should reflect the main topics/themes
- Avoid overly generic tags like "document", "information"
- Tags should help users find relevant content
- Missing important topics is a quality issue"""
    
    def _parse_llm_response(self, response_data: Dict[str, Any], check_metadata: Dict[str, Any]) -> QualityCheckResult:
        """Parse LLM response into standardized QualityCheckResult"""
        
        try:
            overall = response_data.get("overall_assessment", "").upper()
            confidence = float(response_data.get("confidence", self.settings.llm_default_confidence))
            issues = response_data.get("issues", [])
            reasoning = response_data.get("reasoning", "")
            
            # Determine status
            if overall == "ACCURATE":
                status = FlagStatus.PASS
            elif overall == "INACCURATE":
                status = FlagStatus.FAIL
            else:
                # Ambiguous response, use dynamic confidence threshold
                # Try to get dynamic threshold, fallback to settings
                try:
                    from run_local import get_threshold_value
                    dynamic_threshold = get_threshold_value("llm_confidence_threshold")
                    threshold_value = dynamic_threshold if dynamic_threshold is not None else self.settings.llm_confidence_threshold
                except:
                    threshold_value = self.settings.llm_confidence_threshold
                
                status = FlagStatus.FAIL if confidence < threshold_value else FlagStatus.PASS
            
            # Build failure reason if needed
            failure_reason = None
            if status == FlagStatus.FAIL:
                if issues:
                    issue_descriptions = [f"{issue.get('tag', 'unknown')}: {issue.get('problem', 'issue')}" for issue in issues[:3]]
                    failure_reason = f"Tag issues: {'; '.join(issue_descriptions)}"
                else:
                    failure_reason = reasoning or "Tags do not accurately represent content"
            
            # Determine severity based on confidence and issues
            if status == FlagStatus.FAIL:
                if confidence < 0.3 or len(issues) > 3:
                    severity = "critical"
                elif confidence < 0.6 or len(issues) > 1:
                    severity = "high"
                else:
                    severity = "medium"
            else:
                severity = "low"
            
            # Generate suggestions based on issues
            suggestion = None
            if status == FlagStatus.FAIL and issues:
                if len(issues) == 1:
                    issue = issues[0]
                    suggestion = f"Review tag '{issue.get('tag', 'unknown')}': {issue.get('problem', 'issue')}"
                else:
                    suggestion = f"Review {len(issues)} tag issues for better content representation"
            
            # Determine if auto-fixable
            autoFixable = False
            if status == FlagStatus.FAIL:
                # Check if issues are auto-fixable (e.g., generic tags, missing tags)
                autoFixable = any(
                    issue.get('problem', '').lower() in ['generic', 'missing', 'vague', 'too broad']
                    for issue in issues
                )
            
            # Combine check_metadata
            combined_check_metadata = {
                **check_metadata,
                "llm_assessment": overall,
                "llm_reasoning": reasoning,
                "issues_found": len(issues),
                "issues": issues[:5]  # Limit to 5 issues to save space
            }
            
            return QualityCheckResult(
                check_name="llm_semantic_validation",
                status=status,
                confidence_score=confidence,
                failure_reason=failure_reason,
                check_metadata=combined_check_metadata,
                type="llm_semantic_validation",
                severity=severity,
                description="LLM-powered semantic validation of tag relevance to content",
                suggestion=suggestion,
                autoFixable=autoFixable,
                category="llm",
                reasoning=reasoning,
                issues=issues[:5],  # Limit to 5 issues
                llm_assessment=overall,
                llm_reasoning=reasoning,
                issues_found=len(issues),
                processing_time_ms=check_metadata.get("processing_time_ms", 0)
            )
            
        except Exception as e:
            # Fallback if response parsing fails
            return QualityCheckResult(
                check_name="llm_semantic_validation",
                status=FlagStatus.FAIL,
                confidence_score=0.1,
                failure_reason=f"Failed to parse LLM response: {e}",
                check_metadata={**check_metadata, "parse_error": str(e)},
                type="llm_semantic_validation",
                severity="critical",
                description="LLM-powered semantic validation of tag relevance to content",
                suggestion="Check LLM service configuration and try again",
                autoFixable=False,
                category="llm",
                reasoning=f"Parse error: {e}",
                issues=[],
                llm_assessment="ERROR",
                llm_reasoning=f"Failed to parse response: {e}",
                issues_found=0,
                processing_time_ms=check_metadata.get("processing_time_ms", 0)
            )
    
    def _fallback_check(self, text: str, tags: List[str], reason: str) -> QualityCheckResult:
        """
        Fallback validation when LLM is unavailable
        Uses simple heuristics for basic validation
        """
        
        # Simple keyword matching fallback
        text_lower = text.lower()
        text_words = set(re.findall(r'\b\w+\b', text_lower))
        
        matched_tags = 0
        for tag in tags:
            tag_words = set(re.findall(r'\b\w+\b', tag.lower()))
            if tag_words & text_words:  # Any word match
                matched_tags += 1
        
        # Simple scoring
        match_ratio = matched_tags / len(tags) if tags else 0
        
        # Use configurable thresholds for fallback
        if match_ratio < self.settings.llm_fallback_match_ratio_threshold and len(tags) > 1:
            status = FlagStatus.FAIL
            confidence = self.settings.llm_fallback_confidence_high
            failure_reason = f"Fallback check: Low tag-text overlap ({match_ratio:.1%}). Consider improving tag relevance."
        elif match_ratio < self.settings.llm_fallback_moderate_threshold and len(tags) > 2:
            status = FlagStatus.FAIL
            confidence = self.settings.llm_fallback_confidence_moderate
            failure_reason = f"Fallback check: Moderate tag-text overlap ({match_ratio:.1%}). Tags could be more specific."
        else:
            status = FlagStatus.PASS
            confidence = self.settings.llm_fallback_confidence_low
            failure_reason = None
        
        return QualityCheckResult(
            check_name="llm_semantic_validation",
            status=status,
            confidence_score=confidence,
            failure_reason=failure_reason,
            check_metadata={
                "fallback_used": True,
                "fallback_reason": reason,
                "tag_match_ratio": match_ratio,
                "provider": "fallback_heuristic",
                "suggestion": "Improve tag relevance to content topics" if match_ratio < 0.2 else None
            }
        )
    
    def _record_failure(self):
        """Record LLM failure for circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = datetime.now(UTC)
        
        if self.failure_count >= self.max_failures:
            self.logger.warning(f"LLM circuit breaker triggered after {self.failure_count} failures")
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.failure_count < self.max_failures:
            return False
        
        if self.last_failure_time:
            time_since_failure = (datetime.now(UTC) - self.last_failure_time).total_seconds()
            if time_since_failure > self.circuit_breaker_timeout:
                # Reset circuit breaker
                self.failure_count = 0
                self.last_failure_time = None
                return False
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for LLM service"""
        try:
            # Simple test request
            test_result = await self.check_chunk(
                "This is a test document about company policies.",
                ["test", "policies"]
            )
            
            return {
                "status": "healthy",
                "provider": self.provider,
                "circuit_breaker_open": self._is_circuit_open(),
                "total_requests": self.request_count,
                "total_cost_usd": round(self.total_cost_usd, 4),
                "avg_response_time_ms": sum(self.response_times[-10:]) / len(self.response_times[-10:]) if self.response_times else 0
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "provider": self.provider,
                "circuit_breaker_open": self._is_circuit_open()
            }
    
    def get_cost_metrics(self) -> Dict[str, Any]:
        """Get detailed cost and performance metrics"""
        return {
            "total_requests": self.request_count,
            "total_tokens_used": self.total_tokens_used,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "avg_cost_per_request": round(self.total_cost_usd / max(1, self.request_count), 4),
            "avg_tokens_per_request": self.total_tokens_used / max(1, self.request_count),
            "avg_response_time_ms": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            "circuit_breaker_failures": self.failure_count,
            "fallback_mode": self.use_fallback,
            "provider": self.provider
        }
    
    def reset_metrics(self):
        """Reset cost and performance tracking"""
        self.request_count = 0
        self.total_tokens_used = 0
        self.total_cost_usd = 0.0
        self.response_times = []
        self.failure_count = 0
        self.last_failure_time = None
    
    async def generate_tag_suggestions(self, content: str, current_tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate tag suggestions using real OpenAI API
        Filters out stopwords and existing tags
        """
        if current_tags is None:
            current_tags = []
        
        try:
            # Load stopwords
            stopwords = set()
            try:
                with open("stopwords.txt", "r") as f:
                    stopwords = set(line.strip().lower() for line in f if line.strip())
            except FileNotFoundError:
                # Default stopwords if file not found
                stopwords = {
                    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
                    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
                    "will", "would", "could", "should", "may", "might", "can", "this", "that", "these", "those",
                    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
                    "my", "your", "his", "her", "its", "our", "their", "mine", "yours", "hers", "ours", "theirs",
                    "document", "content", "information", "data", "text", "file", "page", "section", "part", "piece"
                }
            
            # Check if OpenAI is available
            if not OPENAI_AVAILABLE or not hasattr(self, 'openai_client'):
                raise Exception("OpenAI not available")
            
            # Create optimized prompt for tag generation
            prompt = f"""Analyze the following content and suggest 5-8 relevant, specific tags that would help users find this content.

CONTENT:
{content[:2000]}  # Limit content length

CURRENT TAGS: {', '.join(current_tags) if current_tags else 'None'}

Requirements:
1. Generate tags that are specific and relevant to the content
2. Avoid generic words like "document", "information", "content"
3. Avoid stopwords and common words
4. Do not suggest tags that already exist in current tags
5. Focus on topics, themes, document types, departments, or specific concepts
6. Use 2-4 word phrases when appropriate for clarity
7. Make tags actionable and searchable

Respond with JSON format:
{{
  "suggestions": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "reasoning": "brief explanation of why these tags are relevant",
  "confidence": 0.0-1.0
}}

Example good tags: "HR policies", "employee handbook", "safety procedures", "training materials", "compliance guidelines"
Example bad tags: "document", "information", "content", "the", "and"
"""

            # Call OpenAI API
            try:
                # Try with JSON response format first
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a content tagging expert. Generate specific, relevant tags that help users find content."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
            except Exception as json_error:
                # Fallback without response_format if not supported
                try:
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a content tagging expert. Generate specific, relevant tags that help users find content."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=500,
                        temperature=0.3
                    )
                except Exception as fallback_error:
                    raise Exception(f"OpenAI API failed: {str(fallback_error)}")
            
            # Parse response
            content_response = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to text parsing if needed
            try:
                if content_response:
                    result_data = json.loads(content_response)
                else:
                    raise Exception("Empty response from OpenAI")
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract suggestions from text
                if content_response:
                    result_data = self._parse_tag_suggestions_from_text(content_response)
                else:
                    raise Exception("Empty response from OpenAI")
            
            # Extract suggestions and filter them
            raw_suggestions = result_data.get("suggestions", [])
            reasoning = result_data.get("reasoning", "")
            confidence = result_data.get("confidence", self.settings.llm_default_confidence)
            
            # Filter suggestions to avoid stopwords and existing tags
            filtered_suggestions = []
            current_tags_lower = [tag.lower().strip() for tag in current_tags]
            
            for suggestion in raw_suggestions:
                suggestion_clean = suggestion.strip()
                suggestion_lower = suggestion_clean.lower()
                
                # Skip if already in current tags
                if suggestion_lower in current_tags_lower:
                    continue
                
                # Skip if contains stopwords
                words = suggestion_lower.split()
                if any(word in stopwords for word in words):
                    continue
                
                # Skip if too generic
                if len(suggestion_clean) < 3 or suggestion_clean in ["document", "content", "information", "data"]:
                    continue
                
                # Skip if too long
                if len(suggestion_clean) > 50:
                    continue
                
                filtered_suggestions.append(suggestion_clean)
            
            # Limit to 5 suggestions
            final_suggestions = filtered_suggestions[:5]
            
            return {
                "success": True,
                "suggestions": final_suggestions,
                "confidence_score": confidence,
                "reasoning": reasoning,
                "provider": "openai"
            }
            
        except Exception as e:
            self.logger.error(f"OpenAI tag suggestions error: {e}")
            # Fallback to basic suggestions
            content_lower = content.lower()
            basic_suggestions = []
            
            # Extract meaningful keywords
            import re
            words = re.findall(r'\b\w{4,}\b', content_lower)
            word_freq = {}
            for word in words:
                if word not in stopwords and len(word) > 3:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top keywords
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Generate basic suggestions
            for keyword, freq in top_keywords:
                if keyword not in current_tags and freq > 1:
                    basic_suggestions.append(keyword)
            
            # Add document type suggestions
            if any(word in content_lower for word in ["policy", "procedure", "guideline"]):
                basic_suggestions.append("policy")
            if any(word in content_lower for word in ["training", "guide", "manual"]):
                basic_suggestions.append("training")
            if any(word in content_lower for word in ["report", "analysis", "study"]):
                basic_suggestions.append("report")
            
            return {
                "success": True,
                "suggestions": basic_suggestions[:5],
                "confidence_score": 0.6,
                "reasoning": f"OpenAI unavailable - using basic keyword extraction. Error: {str(e)}",
                "provider": "fallback"
            }
    
    def _parse_tag_suggestions_from_text(self, text_response: str) -> Dict[str, Any]:
        """
        Parse tag suggestions from text response when JSON parsing fails
        """
        import re
        
        # Try to extract suggestions from various formats
        suggestions = []
        
        # Look for patterns like "suggestions: tag1, tag2, tag3"
        suggestion_patterns = [
            r'suggestions?[:\s]+\[?([^\]]+)\]?',
            r'tags?[:\s]+\[?([^\]]+)\]?',
            r'recommended[:\s]+\[?([^\]]+)\]?'
        ]
        
        for pattern in suggestion_patterns:
            matches = re.findall(pattern, text_response, re.IGNORECASE)
            for match in matches:
                # Split by commas and clean up
                tags = [tag.strip().strip('"\'') for tag in match.split(',')]
                suggestions.extend(tags)
        
        # If no structured suggestions found, extract keywords
        if not suggestions:
            # Extract words that look like tags (capitalized, 3+ chars)
            words = re.findall(r'\b[A-Z][a-z]{2,}\b', text_response)
            suggestions = words[:5]
        
        # Extract reasoning from the text
        reasoning = "Tag suggestions extracted from text response"
        if "reasoning" in text_response.lower():
            reasoning_match = re.search(r'reasoning[:\s]+(.+?)(?:\n|$)', text_response, re.IGNORECASE)
            if reasoning_match:
                reasoning = reasoning_match.group(1).strip()
        
        # Extract confidence if present
        confidence = 0.7  # default
        confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', text_response, re.IGNORECASE)
        if confidence_match:
            try:
                confidence = float(confidence_match.group(1))
            except ValueError:
                pass
        
        return {
            "suggestions": suggestions,
            "reasoning": reasoning,
            "confidence": confidence
        }


# Utility function for batch processing
async def batch_llm_validation(chunks: List[Dict], llm_judge: LLMJudge, max_concurrent: int = 5) -> List[QualityCheckResult]:
    """
    Process multiple chunks concurrently with rate limiting
    Useful for batch processing scenarios
    """
    
    async def process_chunk(chunk_data):
        return await llm_judge.check_chunk(
            chunk_data["text"], 
            chunk_data["tags"]
        )
    
    # Use semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_process(chunk_data):
        async with semaphore:
            return await process_chunk(chunk_data)
    
    # Process all chunks concurrently with limits
    tasks = [limited_process(chunk) for chunk in chunks]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # Create fallback result for failed chunks
            processed_results.append(QualityCheckResult(
                check_name="llm_semantic_validation",
                status=FlagStatus.FAIL,
                confidence_score=0.1,
                failure_reason=f"Batch processing error: {str(result)}",
                check_metadata={"batch_error": True, "chunk_index": i}
            ))
        else:
            processed_results.append(result)
    
    return processed_results 