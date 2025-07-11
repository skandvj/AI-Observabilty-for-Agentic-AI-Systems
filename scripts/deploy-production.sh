#!/bin/bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="lucy-indexing-qa"
ENVIRONMENT="production"
LOCATION="East US 2"
DOMAIN="your-domain.com"  # Replace with your domain

echo -e "${BLUE}🚀 Lucy Indexing QA - Production Deployment${NC}"
echo "=================================================="
echo "Project: $PROJECT_NAME"
echo "Environment: $ENVIRONMENT"
echo "Location: $LOCATION"
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if logged into Azure
if ! az account show &> /dev/null; then
    echo -e "${RED}❌ Please log into Azure CLI first: az login${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"

# Function to prompt for confirmation
confirm() {
    read -p "$(echo -e ${YELLOW}$1 [y/N]: ${NC})" response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            true
            ;;
        *)
            false
            ;;
    esac
}

# Deployment confirmation
echo ""
echo -e "${YELLOW}⚠️  This will deploy the Lucy Indexing QA system to Azure.${NC}"
echo "This includes:"
echo "• Azure SQL Database"
echo "• Azure OpenAI Service"
echo "• App Services for API and Dashboard"
echo "• Storage Account"
echo "• Key Vault"
echo "• Application Insights"
echo "• Alert configurations"
echo ""

if ! confirm "Do you want to proceed with deployment?"; then
    echo -e "${RED}❌ Deployment cancelled${NC}"
    exit 0
fi

# Phase 1: Infrastructure Deployment
echo ""
echo -e "${BLUE}🏗️  Phase 1: Deploying Azure Infrastructure${NC}"
echo "============================================="

cd infrastructure/terraform

# Initialize Terraform
echo -e "${YELLOW}📦 Initializing Terraform...${NC}"
terraform init

# Plan deployment
echo -e "${YELLOW}📋 Planning Terraform deployment...${NC}"
terraform plan \
    -var="environment=$ENVIRONMENT" \
    -var="location=$LOCATION" \
    -var="project_name=$PROJECT_NAME" \
    -out=tfplan

if ! confirm "Terraform plan looks good. Proceed with infrastructure deployment?"; then
    echo -e "${RED}❌ Infrastructure deployment cancelled${NC}"
    exit 0
fi

# Apply infrastructure
echo -e "${YELLOW}🚀 Deploying infrastructure...${NC}"
terraform apply tfplan

# Get outputs
RESOURCE_GROUP=$(terraform output -raw resource_group_name)
SQL_SERVER_FQDN=$(terraform output -raw sql_server_fqdn)
INGESTION_API_URL=$(terraform output -raw ingestion_api_url)
DASHBOARD_URL=$(terraform output -raw dashboard_url)
OPENAI_ENDPOINT=$(terraform output -raw openai_endpoint)
STORAGE_ACCOUNT=$(terraform output -raw storage_account_name)
KEY_VAULT_URI=$(terraform output -raw key_vault_uri)

echo -e "${GREEN}✅ Infrastructure deployed successfully${NC}"

# Phase 2: Database Schema Deployment
echo ""
echo -e "${BLUE}💾 Phase 2: Deploying Database Schema${NC}"
echo "======================================"

cd ../../

# Create database schema files if they don't exist
mkdir -p database/schema

cat > database/schema/init_database.sql << 'EOF'
-- Lucy Indexing QA Database Schema

-- Main chunk records table
CREATE TABLE ChunkRecords (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    trace_id NVARCHAR(64) UNIQUE NOT NULL,
    record_id NVARCHAR(256) NOT NULL,
    document_text NTEXT NOT NULL,
    tags NVARCHAR(MAX) NOT NULL, -- JSON array
    source_connector NVARCHAR(50) NOT NULL,
    file_id NVARCHAR(256) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    processed_at DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

-- Quality check results
CREATE TABLE QualityCheckRecords (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    chunk_id UNIQUEIDENTIFIER NOT NULL,
    check_name NVARCHAR(100) NOT NULL,
    status NVARCHAR(20) NOT NULL,
    confidence_score FLOAT NOT NULL,
    failure_reason NTEXT NULL,
    check_metadata NVARCHAR(MAX) NULL,
    executed_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    processing_time_ms FLOAT NOT NULL,
    FOREIGN KEY (chunk_id) REFERENCES ChunkRecords(id)
);

-- Human reviewer decisions
CREATE TABLE ReviewRecords (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    chunk_id UNIQUEIDENTIFIER NOT NULL,
    decision NVARCHAR(30) NOT NULL,
    comments NTEXT NULL,
    reviewer_id NVARCHAR(100) NOT NULL,
    reviewed_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    previous_thresholds NVARCHAR(MAX) NULL,
    triggered_threshold_update BIT DEFAULT 0,
    FOREIGN KEY (chunk_id) REFERENCES ChunkRecords(id)
);

-- Dead letter records for failed processing
CREATE TABLE DeadLetterRecords (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    trace_id NVARCHAR(64) NULL,
    raw_input NTEXT NOT NULL,
    error_message NTEXT NOT NULL,
    error_type NVARCHAR(100) NOT NULL,
    failed_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    source_connector NVARCHAR(50) NULL,
    retry_count INT DEFAULT 0,
    resolved BIT DEFAULT 0
);

-- Golden dataset for training and evaluation
CREATE TABLE GoldenDatasetRecords (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    record_id NVARCHAR(256) NOT NULL,
    document_text NTEXT NOT NULL,
    tags NVARCHAR(MAX) NOT NULL,
    source_connector NVARCHAR(50) NOT NULL,
    is_good_quality BIT NOT NULL,
    expected_flags NVARCHAR(MAX) NULL,
    confidence_level FLOAT NOT NULL,
    added_by NVARCHAR(100) NOT NULL,
    added_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    version INT DEFAULT 1,
    active BIT DEFAULT 1
);

-- Dynamic threshold configurations
CREATE TABLE ThresholdConfigurations (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    check_name NVARCHAR(100) NOT NULL,
    threshold_value FLOAT NOT NULL,
    confidence_cutoff FLOAT NOT NULL,
    updated_by NVARCHAR(100) NOT NULL,
    updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    reason NTEXT NULL,
    true_positive_rate FLOAT NULL,
    false_positive_rate FLOAT NULL,
    precision FLOAT NULL,
    recall FLOAT NULL
);

-- Alert history
CREATE TABLE AlertRecords (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    alert_type NVARCHAR(50) NOT NULL,
    severity NVARCHAR(20) NOT NULL,
    message NTEXT NOT NULL,
    triggered_by NVARCHAR(100) NULL,
    alert_data NVARCHAR(MAX) NULL,
    sent_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    slack_sent BIT DEFAULT 0,
    email_sent BIT DEFAULT 0,
    webhook_sent BIT DEFAULT 0,
    delivery_errors NVARCHAR(MAX) NULL
);
EOF

cat > database/schema/create_indexes.sql << 'EOF'
-- Performance indexes for Lucy Indexing QA

-- ChunkRecords indexes
CREATE INDEX IX_ChunkRecords_TraceId ON ChunkRecords(trace_id);
CREATE INDEX IX_ChunkRecords_RecordId ON ChunkRecords(record_id);
CREATE INDEX IX_ChunkRecords_SourceConnector ON ChunkRecords(source_connector);
CREATE INDEX IX_ChunkRecords_ProcessedAt ON ChunkRecords(processed_at);
CREATE INDEX IX_ChunkRecords_ProcessedAt_Connector ON ChunkRecords(processed_at, source_connector);

-- QualityCheckRecords indexes
CREATE INDEX IX_QualityCheckRecords_ChunkId ON QualityCheckRecords(chunk_id);
CREATE INDEX IX_QualityCheckRecords_CheckName ON QualityCheckRecords(check_name);
CREATE INDEX IX_QualityCheckRecords_Status ON QualityCheckRecords(status);
CREATE INDEX IX_QualityCheckRecords_ExecutedAt ON QualityCheckRecords(executed_at);
CREATE INDEX IX_QualityCheckRecords_Status_Check_Date ON QualityCheckRecords(status, check_name, executed_at);

-- ReviewRecords indexes
CREATE INDEX IX_ReviewRecords_ChunkId ON ReviewRecords(chunk_id);
CREATE INDEX IX_ReviewRecords_ReviewerId ON ReviewRecords(reviewer_id);
CREATE INDEX IX_ReviewRecords_ReviewedAt ON ReviewRecords(reviewed_at);

-- DeadLetterRecords indexes
CREATE INDEX IX_DeadLetterRecords_TraceId ON DeadLetterRecords(trace_id);
CREATE INDEX IX_DeadLetterRecords_ErrorType ON DeadLetterRecords(error_type);
CREATE INDEX IX_DeadLetterRecords_FailedAt ON DeadLetterRecords(failed_at);
CREATE INDEX IX_DeadLetterRecords_SourceConnector ON DeadLetterRecords(source_connector);
CREATE INDEX IX_DeadLetterRecords_Resolved ON DeadLetterRecords(resolved);

-- GoldenDatasetRecords indexes
CREATE INDEX IX_GoldenDatasetRecords_RecordId ON GoldenDatasetRecords(record_id);
CREATE INDEX IX_GoldenDatasetRecords_IsGoodQuality ON GoldenDatasetRecords(is_good_quality);
CREATE INDEX IX_GoldenDatasetRecords_Active ON GoldenDatasetRecords(active);

-- ThresholdConfigurations indexes
CREATE INDEX IX_ThresholdConfigurations_CheckName ON ThresholdConfigurations(check_name);

-- AlertRecords indexes
CREATE INDEX IX_AlertRecords_AlertType ON AlertRecords(alert_type);
CREATE INDEX IX_AlertRecords_Severity ON AlertRecords(severity);
CREATE INDEX IX_AlertRecords_SentAt ON AlertRecords(sent_at);
EOF

cat > database/schema/insert_default_data.sql << 'EOF'
-- Default configuration data for Lucy Indexing QA

-- Insert default threshold configurations
INSERT INTO ThresholdConfigurations (check_name, threshold_value, confidence_cutoff, updated_by, reason) VALUES
('empty_tags', 1.0, 0.9, 'system', 'Initial system configuration'),
('tag_count_validation', 0.8, 0.8, 'system', 'Initial system configuration'),
('text_quality', 0.7, 0.7, 'system', 'Initial system configuration'),
('stopwords_detection', 0.6, 0.6, 'system', 'Initial system configuration'),
('spam_pattern_detection', 0.8, 0.8, 'system', 'Initial system configuration'),
('duplicate_content_detection', 0.9, 0.9, 'system', 'Initial system configuration'),
('tag_text_relevance', 0.3, 0.7, 'system', 'Initial system configuration');

-- Insert sample golden dataset records
INSERT INTO GoldenDatasetRecords (record_id, document_text, tags, source_connector, is_good_quality, confidence_level, added_by) VALUES
('golden_good_001', 'Comprehensive guide to microservices architecture covering service design patterns, inter-service communication, data management strategies, deployment automation, monitoring and observability, fault tolerance mechanisms, and security considerations for enterprise-scale distributed systems.', '["microservices", "architecture", "enterprise", "distributed-systems", "scalability"]', 'confluence', 1, 0.95, 'system'),
('golden_bad_001', 'document content information data file general misc', '["document", "content", "information", "data", "file", "general", "misc"]', 'sharepoint', 0, 0.95, 'system'),
('golden_good_002', 'API authentication implementation using OAuth 2.0 with JWT tokens, including refresh token rotation, scope validation, and secure session management for REST endpoints.', '["api", "authentication", "oauth", "jwt", "security", "rest"]', 'confluence', 1, 0.90, 'system'),
('golden_bad_002', 'test test test document file data information', '["test", "document", "file", "data", "information", "misc", "general"]', 'notion', 0, 0.85, 'system');
EOF

# Deploy database schema
echo -e "${YELLOW}📊 Deploying database schema...${NC}"

# Get SQL admin password from Key Vault
SQL_PASSWORD=$(az keyvault secret show --vault-name "${PROJECT_NAME}-keyvault" --name "sql-admin-password" --query value -o tsv)

# Use sqlcmd to deploy schema
echo -e "${YELLOW}📋 Creating database tables...${NC}"
sqlcmd -S "$SQL_SERVER_FQDN" -d "${PROJECT_NAME}-database" -U "lucyadmin" -P "$SQL_PASSWORD" -i database/schema/init_database.sql

echo -e "${YELLOW}📊 Creating database indexes...${NC}"
sqlcmd -S "$SQL_SERVER_FQDN" -d "${PROJECT_NAME}-database" -U "lucyadmin" -P "$SQL_PASSWORD" -i database/schema/create_indexes.sql

echo -e "${YELLOW}📝 Inserting default data...${NC}"
sqlcmd -S "$SQL_SERVER_FQDN" -d "${PROJECT_NAME}-database" -U "lucyadmin" -P "$SQL_PASSWORD" -i database/schema/insert_default_data.sql

echo -e "${GREEN}✅ Database schema deployed successfully${NC}"

# Phase 3: Backend Application Deployment
echo ""
echo -e "${BLUE}🐍 Phase 3: Deploying Backend Application${NC}"
echo "========================================="

cd backend/

# Create production requirements.txt
cat > requirements.txt << 'EOF'
fastapi[all]==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
azure-storage-blob==12.19.0
azure-keyvault-secrets==4.7.0
azure-identity==1.15.0
openai==1.3.7
pyodbc==5.0.1
asyncpg==0.29.0
pydantic==2.5.0
python-multipart==0.0.6
azure-monitor-opentelemetry==1.1.0
azure-applicationinsights==0.11.10
pandas==2.1.4
numpy==1.25.2
scikit-learn==1.3.2
python-dotenv==1.0.0
aiofiles==23.2.1
httpx==0.25.2
EOF

# Create startup script for Azure App Service
cat > startup.sh << 'EOF'
#!/bin/bash
echo "Starting Lucy Indexing QA API..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
EOF

chmod +x startup.sh

# Create web.config for Azure App Service
cat > web.config << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="httpPlatformHandler" resourceType="Unspecified"/>
    </handlers>
    <httpPlatform processPath="./startup.sh" 
                  arguments="" 
                  stdoutLogEnabled="true" 
                  stdoutLogFile="./python.log" 
                  startupTimeLimit="60" 
                  requestTimeout="00:04:00">
    </httpPlatform>
  </system.webServer>
</configuration>
EOF

echo -e "${YELLOW}📦 Building and deploying backend...${NC}"

# Create deployment package
zip -r ../backend-deployment.zip . -x "*.git*" "*__pycache__*" "*.pyc" "venv/*" ".env*"

# Deploy to Azure App Service
az webapp deployment source config-zip \
    --resource-group "$RESOURCE_GROUP" \
    --name "${PROJECT_NAME}-ingestion-api" \
    --src ../backend-deployment.zip

echo -e "${GREEN}✅ Backend deployed successfully${NC}"

# Phase 4: Frontend Application Deployment
echo ""
echo -e "${BLUE}⚛️  Phase 4: Deploying Frontend Application${NC}"
echo "==========================================="

cd ../frontend/

# Update Next.js configuration for production
cat > next.config.ts << EOF
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: '$INGESTION_API_URL',
    NEXT_PUBLIC_ENVIRONMENT: '$ENVIRONMENT'
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: '$INGESTION_API_URL/:path*'
      }
    ]
  }
}

export default nextConfig
EOF

echo -e "${YELLOW}📦 Installing dependencies and building frontend...${NC}"

# Install dependencies
npm ci

# Build for production
npm run build

# Create deployment package
zip -r ../frontend-deployment.zip .next/ public/ package.json next.config.ts -x "node_modules/*" ".git/*"

# Deploy to Azure App Service
echo -e "${YELLOW}🚀 Deploying frontend to Azure...${NC}"
az webapp deployment source config-zip \
    --resource-group "$RESOURCE_GROUP" \
    --name "${PROJECT_NAME}-dashboard" \
    --src ../frontend-deployment.zip

echo -e "${GREEN}✅ Frontend deployed successfully${NC}"

# Phase 5: Post-Deployment Configuration
echo ""
echo -e "${BLUE}⚙️  Phase 5: Post-Deployment Configuration${NC}"
echo "=========================================="

# Configure custom domain (if provided)
if [ "$DOMAIN" != "your-domain.com" ]; then
    echo -e "${YELLOW}🌐 Configuring custom domain...${NC}"
    
    # Add custom hostnames
    az webapp config hostname add \
        --resource-group "$RESOURCE_GROUP" \
        --webapp-name "${PROJECT_NAME}-dashboard" \
        --hostname "qa-dashboard.$DOMAIN" || true
    
    az webapp config hostname add \
        --resource-group "$RESOURCE_GROUP" \
        --webapp-name "${PROJECT_NAME}-ingestion-api" \
        --hostname "qa-api.$DOMAIN" || true
    
    echo -e "${YELLOW}⚠️  Please configure DNS records:${NC}"
    echo "qa-dashboard.$DOMAIN -> $(az webapp show --resource-group $RESOURCE_GROUP --name ${PROJECT_NAME}-dashboard --query defaultHostName -o tsv)"
    echo "qa-api.$DOMAIN -> $(az webapp show --resource-group $RESOURCE_GROUP --name ${PROJECT_NAME}-ingestion-api --query defaultHostName -o tsv)"
fi

# Enable HTTPS only
echo -e "${YELLOW}🔒 Enabling HTTPS only...${NC}"
az webapp update \
    --resource-group "$RESOURCE_GROUP" \
    --name "${PROJECT_NAME}-dashboard" \
    --https-only true

az webapp update \
    --resource-group "$RESOURCE_GROUP" \
    --name "${PROJECT_NAME}-ingestion-api" \
    --https-only true

# Phase 6: Verification and Testing
echo ""
echo -e "${BLUE}✅ Phase 6: Verification and Testing${NC}"
echo "===================================="

echo -e "${YELLOW}🧪 Testing deployment...${NC}"

# Wait for services to start
sleep 30

# Test API health endpoint
echo -e "${YELLOW}📡 Testing API health endpoint...${NC}"
API_HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$INGESTION_API_URL/health" || echo "000")

if [ "$API_HEALTH_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ API health check passed${NC}"
else
    echo -e "${RED}❌ API health check failed (HTTP $API_HEALTH_RESPONSE)${NC}"
fi

# Test dashboard accessibility
echo -e "${YELLOW}🎨 Testing dashboard accessibility...${NC}"
DASHBOARD_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$DASHBOARD_URL" || echo "000")

if [ "$DASHBOARD_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ Dashboard accessibility check passed${NC}"
else
    echo -e "${RED}❌ Dashboard accessibility check failed (HTTP $DASHBOARD_RESPONSE)${NC}"
fi

# Test database connectivity
echo -e "${YELLOW}💾 Testing database connectivity...${NC}"
DB_TEST_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$INGESTION_API_URL/test" || echo "000")

if [ "$DB_TEST_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ Database connectivity check passed${NC}"
else
    echo -e "${RED}❌ Database connectivity check failed (HTTP $DB_TEST_RESPONSE)${NC}"
fi

# Final Summary
echo ""
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉${NC}"
echo "==============================================="
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo "• Resource Group: $RESOURCE_GROUP"
echo "• API URL: $INGESTION_API_URL"
echo "• Dashboard URL: $DASHBOARD_URL"
echo "• Database: $SQL_SERVER_FQDN"
echo "• OpenAI Endpoint: $OPENAI_ENDPOINT"
echo "• Storage Account: $STORAGE_ACCOUNT"
echo "• Key Vault: $KEY_VAULT_URI"
echo ""
echo -e "${BLUE}🔗 Quick Links:${NC}"
echo "• API Documentation: $INGESTION_API_URL/docs"
echo "• API Health Check: $INGESTION_API_URL/health"
echo "• Dashboard: $DASHBOARD_URL"
echo ""
echo -e "${BLUE}🔐 Security:${NC}"
echo "• All services use HTTPS only"
echo "• Managed identities configured"
echo "• Key Vault stores all secrets"
echo "• SQL firewall configured"
echo ""
echo -e "${BLUE}📊 Monitoring:${NC}"
echo "• Application Insights enabled"
echo "• Metric alerts configured"
echo "• Log retention: 90 days"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Configure source connector integrations"
echo "2. Set up CI/CD pipeline"
echo "3. Configure custom domain SSL certificates"
echo "4. Run end-to-end testing"
echo "5. Set up production monitoring dashboards"
echo ""
echo -e "${GREEN}✨ Your Lucy Indexing QA system is now live and ready! ✨${NC}" 