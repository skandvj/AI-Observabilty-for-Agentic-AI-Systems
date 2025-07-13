# LLM Judge Threshold Fixes

## Issues Found

The LLM Judge file (`backend/app/services/llm_judge.py`) has several hardcoded thresholds that should be configurable:

### 1. Text Length Threshold (Line 121)
```python
# HARDCODED
if len(masked_text.strip()) < 50:
    confidence_score=0.5,
```

**Should be:**
```python
# CONFIGURABLE
if len(masked_text.strip()) < self.settings.llm_fallback_min_text_length:
    confidence_score=self.settings.llm_fallback_confidence_low,
```

### 2. Fallback Check Thresholds (Lines 430-438)
```python
# HARDCODED
if match_ratio < 0.05 and len(tags) > 1:
    confidence = 0.7
elif match_ratio < 0.2 and len(tags) > 2:
    confidence = 0.6
else:
    confidence = 0.5
```

**Should be:**
```python
# CONFIGURABLE
if match_ratio < self.settings.llm_fallback_match_ratio_threshold and len(tags) > 1:
    confidence = self.settings.llm_fallback_confidence_high
elif match_ratio < self.settings.llm_fallback_moderate_threshold and len(tags) > 2:
    confidence = self.settings.llm_fallback_confidence_moderate
else:
    confidence = self.settings.llm_fallback_confidence_low
```

### 3. Default Confidence Values (Lines 298, 625, 740)
```python
# HARDCODED
confidence = float(response_data.get("confidence", 0.5))
confidence = result_data.get("confidence", 0.7)
confidence = 0.7  # default
```

**Should be:**
```python
# CONFIGURABLE
confidence = float(response_data.get("confidence", self.settings.llm_default_confidence))
confidence = result_data.get("confidence", self.settings.llm_default_confidence)
confidence = self.settings.llm_default_confidence
```

## Config Thresholds Added

Added to `backend/app/core/config.py`:
```python
# LLM Judge Fallback Thresholds
llm_fallback_min_text_length: int = 50
llm_fallback_match_ratio_threshold: float = 0.05
llm_fallback_moderate_threshold: float = 0.2
llm_fallback_confidence_high: float = 0.7
llm_fallback_confidence_moderate: float = 0.6
llm_fallback_confidence_low: float = 0.5
llm_default_confidence: float = 0.7
```

## Benefits

1. **Centralized Control** - All LLM Judge thresholds in one place
2. **Easy Adjustment** - Change config values to adjust behavior
3. **Environment Specific** - Different thresholds for dev/staging/prod
4. **Consistent Behavior** - All LLM components use same thresholds
5. **Production Ready** - Environment variables can override defaults

## Next Steps

1. Update the LLM Judge file to use configurable thresholds
2. Test with different threshold values
3. Document the new configurable parameters
4. Update deployment scripts to include new config options 