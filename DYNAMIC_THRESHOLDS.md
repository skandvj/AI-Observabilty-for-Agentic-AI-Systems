# Dynamic Threshold Management System

## Overview

The Dynamic Threshold Management System allows you to update quality control thresholds in real-time without restarting the server. This addresses the issue where LLM Quality Control settings weren't working properly.

## 🎯 Key Features

### 1. **Real-time Updates**
- Change thresholds instantly without server restart
- Immediate impact on quality checks
- No downtime required

### 2. **Comprehensive Threshold Categories**
- **Quality**: Overall quality control thresholds
- **LLM**: LLM validation thresholds  
- **Rules**: Rules engine thresholds
- **Cost**: Cost management thresholds

### 3. **Available Thresholds**

| Threshold Name | Category | Default | Min | Max | Unit | Description |
|----------------|----------|---------|-----|-----|------|-------------|
| `quality_pass_rate_threshold` | quality | 95.0 | 50.0 | 100.0 | percentage | Minimum percentage of quality checks that must pass |
| `quality_confidence_threshold` | quality | 0.8 | 0.1 | 1.0 | score | Minimum confidence score for quality checks |
| `llm_confidence_threshold` | llm | 0.6 | 0.1 | 1.0 | score | Minimum confidence for LLM semantic validation |
| `spam_threshold` | rules | 0.3 | 0.1 | 1.0 | score | Threshold for detecting spam content |
| `stopword_threshold` | rules | 0.5 | 0.1 | 1.0 | score | Threshold for detecting excessive stopwords |
| `min_tag_count` | rules | 1.0 | 1.0 | 10.0 | count | Minimum number of tags required |
| `max_tag_count` | rules | 20.0 | 5.0 | 50.0 | count | Maximum number of tags allowed |
| `cost_budget_daily_limit` | cost | 100.0 | 10.0 | 1000.0 | dollars | Daily cost budget limit |
| `cost_alert_threshold_percentage` | cost | 80.0 | 50.0 | 95.0 | percentage | Budget alert threshold |

## 🔧 API Endpoints

### Get All Thresholds
```http
GET /thresholds
```

### Get Specific Threshold
```http
GET /thresholds/{threshold_name}
```

### Update Threshold
```http
PUT /thresholds/{threshold_name}
Content-Type: application/json

{
  "threshold_name": "llm_confidence_threshold",
  "new_value": 0.7,
  "reason": "Increasing sensitivity for better quality",
  "user_id": "admin"
}
```

### Bulk Update
```http
POST /thresholds/bulk-update
Content-Type: application/json

[
  {
    "threshold_name": "spam_threshold",
    "new_value": 0.4,
    "reason": "Increasing spam sensitivity",
    "user_id": "admin"
  },
  {
    "threshold_name": "stopword_threshold", 
    "new_value": 0.6,
    "reason": "Increasing stopword tolerance",
    "user_id": "admin"
  }
]
```

### Get Threshold History
```http
GET /thresholds/{threshold_name}/history
```

### Reset to Default
```http
POST /thresholds/{threshold_name}/reset?user_id=admin
```

### Get by Category
```http
GET /thresholds/categories/{category}
```

## 🎨 Frontend Interface

A new settings page has been created at `/settings/thresholds` with:

- **Visual threshold management** with progress bars
- **Category filtering** (quality, llm, rules, cost)
- **Real-time updates** with validation
- **Change history** tracking
- **Reset to default** functionality
- **Bulk operations** support

## 🔄 How It Works

### 1. **Dynamic Threshold Storage**
```python
# Global threshold storage
dynamic_thresholds = {
    "llm_confidence_threshold": {
        "current_value": 0.6,
        "default_value": 0.6,
        "min_value": 0.1,
        "max_value": 1.0,
        "description": "Minimum confidence score required for LLM semantic validation to pass",
        "category": "llm",
        "unit": "score"
    }
}
```

### 2. **Real-time Updates**
When a threshold is updated:
1. Value is validated against min/max bounds
2. Change is recorded in history
3. All services immediately use the new value
4. No server restart required

### 3. **Service Integration**
Both the LLM Judge and Rules Engine now use dynamic thresholds:

```python
# In LLM Judge
try:
    from run_local import get_threshold_value
    dynamic_threshold = get_threshold_value("llm_confidence_threshold")
    threshold_value = dynamic_threshold if dynamic_threshold is not None else self.settings.llm_confidence_threshold
except:
    threshold_value = self.settings.llm_confidence_threshold

status = FlagStatus.FAIL if confidence < threshold_value else FlagStatus.PASS
```

## 🧪 Testing

Run the test script to see the system in action:

```bash
cd backend
python test_dynamic_thresholds.py
```

This demonstrates:
- ✅ Real-time threshold updates
- ✅ Validation and error handling
- ✅ Change history tracking
- ✅ Bulk operations
- ✅ Category filtering
- ✅ Reset functionality

## 🚀 Usage Examples

### Fixing LLM Semantic Validation Issues

If you're seeing "LLM Semantic Validation MEDIUM" with low confidence:

1. **Lower the threshold temporarily**:
   ```bash
   curl -X PUT http://127.0.0.1:8000/thresholds/llm_confidence_threshold \
     -H "Content-Type: application/json" \
     -d '{"threshold_name": "llm_confidence_threshold", "new_value": 0.4, "reason": "Temporarily lowering for testing"}'
   ```

2. **Improve tag quality** and then raise the threshold back:
   ```bash
   curl -X PUT http://127.0.0.1:8000/thresholds/llm_confidence_threshold \
     -H "Content-Type: application/json" \
     -d '{"threshold_name": "llm_confidence_threshold", "new_value": 0.7, "reason": "Raising after improving tag quality"}'
   ```

### Adjusting Quality Control Strictness

For more lenient quality checks:
```bash
curl -X PUT http://127.0.0.1:8000/thresholds/quality_pass_rate_threshold \
  -H "Content-Type: application/json" \
  -d '{"threshold_name": "quality_pass_rate_threshold", "new_value": 80.0, "reason": "More lenient quality control"}'
```

For stricter quality checks:
```bash
curl -X PUT http://127.0.0.1:8000/thresholds/quality_pass_rate_threshold \
  -H "Content-Type: application/json" \
  -d '{"threshold_name": "quality_pass_rate_threshold", "new_value": 98.0, "reason": "Stricter quality control"}'
```

## 🔍 Monitoring

### View Current Thresholds
```bash
curl http://127.0.0.1:8000/thresholds
```

### Check Threshold History
```bash
curl http://127.0.0.1:8000/thresholds/llm_confidence_threshold/history
```

### Monitor by Category
```bash
curl http://127.0.0.1:8000/thresholds/categories/llm
```

## 🛡️ Safety Features

1. **Validation**: All values are validated against min/max bounds
2. **History**: All changes are tracked with timestamps and reasons
3. **Fallback**: Services fall back to config defaults if dynamic thresholds fail
4. **Reset**: Easy reset to default values
5. **Audit Trail**: Complete change history for compliance

## 🎯 Benefits

1. **No Downtime**: Updates without server restart
2. **Immediate Impact**: Changes take effect instantly
3. **Flexible Control**: Adjust quality control based on needs
4. **Better Debugging**: Fine-tune thresholds for specific issues
5. **Cost Control**: Adjust LLM usage thresholds dynamically
6. **Quality Optimization**: Balance between quality and throughput

This system solves the original issue where LLM Quality Control settings weren't working by providing a dynamic, real-time threshold management system that integrates seamlessly with the existing quality control pipeline. 