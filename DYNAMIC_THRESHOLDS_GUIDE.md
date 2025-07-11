# Dynamic Threshold Management Guide

## 🎯 Overview

The Dynamic Threshold Management System allows you to update quality control thresholds in real-time without restarting the server. This solves the original issue where "LLM Quality Control settings" weren't working.

## 🚀 Quick Start

### 1. Access the Threshold Management Interface

1. **Open your dashboard**: Go to `http://localhost:3003`
2. **Navigate to Settings**: Click on "Settings" in the sidebar
3. **Select Dynamic Thresholds**: Click on the "Dynamic Thresholds" tab

### 2. View Current Thresholds

The interface shows all available thresholds with:
- **Current Value**: What the threshold is set to now
- **Default Value**: The original system default
- **Range**: Min/max allowed values
- **Category**: Quality, LLM, Rules, or Performance
- **Description**: What the threshold controls

### 3. Edit Thresholds

1. **Click "Edit"** next to any threshold
2. **Enter new value** within the allowed range
3. **Add a reason** for the change (optional but recommended)
4. **Click "Save"** to apply the change

### 4. Reset to Defaults

- **Individual Reset**: Click "Reset" next to any threshold
- **Bulk Reset**: Click "Reset to Defaults" button at the top

## 📊 Available Thresholds

### Quality Control Thresholds
- **quality_pass_rate_threshold**: Minimum percentage of quality checks that must pass (50-100%)
- **quality_confidence_threshold**: Minimum confidence score for quality checks (0-1.0)

### LLM Validation Thresholds
- **llm_confidence_threshold**: Minimum confidence for LLM semantic validation (0-1.0)

### Rules Engine Thresholds
- **spam_threshold**: Threshold for detecting spam content (0-1.0)
- **stopword_threshold**: Threshold for detecting excessive stopwords (0-1.0)
- **min_tag_count**: Minimum number of tags required (0-50)
- **max_tag_count**: Maximum number of tags allowed (1-100)

### Cost Management Thresholds
- **cost_budget_daily_limit**: Daily cost budget limit ($0-$10,000)
- **cost_alert_threshold_percentage**: Budget percentage for alerts (0-100%)

## 🔧 API Endpoints

The system provides RESTful API endpoints for programmatic access:

### Get All Thresholds
```bash
GET http://127.0.0.1:8000/thresholds
```

### Get Specific Threshold
```bash
GET http://127.0.0.1:8000/thresholds/{threshold_name}
```

### Update Threshold
```bash
PUT http://127.0.0.1:8000/thresholds/{threshold_name}
Content-Type: application/json

{
  "threshold_name": "llm_confidence_threshold",
  "new_value": 0.7,
  "reason": "Increasing sensitivity for better quality",
  "user_id": "admin"
}
```

### Reset Threshold
```bash
POST http://127.0.0.1:8000/thresholds/{threshold_name}/reset
```

### Get Threshold History
```bash
GET http://127.0.0.1:8000/thresholds/{threshold_name}/history
```

### Bulk Update
```bash
POST http://127.0.0.1:8000/thresholds/bulk-update
Content-Type: application/json

[
  {
    "threshold_name": "quality_pass_rate_threshold",
    "new_value": 90.0,
    "reason": "Adjusting quality standards",
    "user_id": "admin"
  },
  {
    "threshold_name": "spam_threshold",
    "new_value": 0.35,
    "reason": "Fine-tuning spam detection",
    "user_id": "admin"
  }
]
```

## 🎯 Use Cases

### 1. Adjusting Quality Standards
- **Increase quality_pass_rate_threshold** (e.g., 95% → 98%) for stricter quality requirements
- **Decrease quality_confidence_threshold** (e.g., 0.8 → 0.6) for more lenient confidence requirements

### 2. Fine-tuning LLM Validation
- **Increase llm_confidence_threshold** (e.g., 0.6 → 0.8) for more strict LLM validation
- **Decrease llm_confidence_threshold** (e.g., 0.6 → 0.4) for more lenient LLM validation

### 3. Adjusting Content Rules
- **Increase spam_threshold** (e.g., 0.3 → 0.5) to be more tolerant of potential spam
- **Decrease spam_threshold** (e.g., 0.3 → 0.2) to be more strict about spam detection
- **Adjust tag limits** based on your content requirements

### 4. Cost Management
- **Set cost_budget_daily_limit** based on your budget constraints
- **Configure cost_alert_threshold_percentage** for budget monitoring

## 🔍 Monitoring Changes

### View Change History
The interface shows a history table with:
- **Threshold Name**: Which threshold was changed
- **Old/New Values**: The before and after values
- **Changed By**: Who made the change
- **Reason**: Why the change was made
- **Date**: When the change occurred

### Real-time Updates
- Changes are applied immediately without server restart
- The interface refreshes automatically after changes
- All connected clients see updates in real-time

## 🛠️ Troubleshooting

### "Method Not Allowed" Error
- **Cause**: Using wrong HTTP method (GET instead of PUT)
- **Solution**: Use PUT for updates, GET for reading

### "Threshold Not Found" Error
- **Cause**: Incorrect threshold name
- **Solution**: Check the exact threshold name from the list

### "Invalid Value" Error
- **Cause**: Value outside allowed range
- **Solution**: Check min/max values and stay within range

### Frontend Not Loading Thresholds
- **Cause**: Backend not running or CORS issues
- **Solution**: Ensure backend is running on port 8000

## 🧪 Testing

Run the test script to verify everything is working:

```bash
cd backend
python test_dynamic_thresholds.py
```

This will test all endpoints and show current threshold values.

## 📈 Benefits

1. **Real-time Updates**: No server restart required
2. **Validation**: Values are checked against min/max ranges
3. **History Tracking**: All changes are logged with reasons
4. **Bulk Operations**: Update multiple thresholds at once
5. **User-friendly Interface**: Visual progress bars and status indicators
6. **API Access**: Programmatic control for automation
7. **Category Organization**: Thresholds grouped by function

## 🎉 Success!

You now have a fully functional dynamic threshold management system that solves the original problem of "LLM Quality Control settings not working." You can:

- ✅ Update thresholds in real-time
- ✅ View current values and defaults
- ✅ Track change history
- ✅ Reset to defaults
- ✅ Use the web interface or API
- ✅ Monitor changes without server restarts

The system is now ready for production use! 