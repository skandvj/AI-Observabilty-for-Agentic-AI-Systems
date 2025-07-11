terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
  required_version = ">= 1.1"
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# Variables
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "Central US"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "lucy-indexing-qa"
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "${var.project_name}-${var.environment}"
  location = var.location

  tags = {
    Environment = var.environment
    Project     = var.project_name
    CreatedBy   = "terraform"
  }
}

# Storage Account for Dead Letter Queue
resource "azurerm_storage_account" "dead_letter" {
  name                     = "${replace(var.project_name, "-", "")}dlq"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  access_tier              = "Hot"

  blob_properties {
    versioning_enabled = true
    delete_retention_policy {
      days = 7
    }
  }

  tags = {
    Environment = var.environment
    Purpose     = "dead-letter-queue"
  }
}

resource "azurerm_storage_container" "dead_letter_container" {
  name                  = "failed-chunks"
  storage_account_name  = azurerm_storage_account.dead_letter.name
  container_access_type = "private"
}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                = "${replace(var.project_name, "-", "")}kv"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  enabled_for_deployment          = true
  enabled_for_template_deployment = true
  purge_protection_enabled        = false

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Recover", "Backup", "Restore"
    ]
  }

  tags = {
    Environment = var.environment
  }
}

data "azurerm_client_config" "current" {}

# SQL Server and Database
resource "azurerm_mssql_server" "main" {
  name                         = "${var.project_name}-sql-server"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  version                      = "12.0"
  administrator_login          = "lucyadmin"
  administrator_login_password = random_password.sql_admin.result

  azuread_administrator {
    login_username = "lucy-qa-admin"
    object_id      = data.azurerm_client_config.current.object_id
  }

  tags = {
    Environment = var.environment
  }
}

resource "random_password" "sql_admin" {
  length  = 16
  special = true
}

resource "azurerm_key_vault_secret" "sql_admin_password" {
  name         = "sql-admin-password"
  value        = random_password.sql_admin.result
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_mssql_database" "main" {
  name           = "${var.project_name}-database"
  server_id      = azurerm_mssql_server.main.id
  collation      = "SQL_Latin1_General_CP1_CI_AS"
  max_size_gb    = 100
  sku_name       = "S2"
  zone_redundant = false

  short_term_retention_policy {
    retention_days = 7
  }

  long_term_retention_policy {
    weekly_retention  = "P4W"
    monthly_retention = "P12M"
    yearly_retention  = "P5Y"
  }

  tags = {
    Environment = var.environment
  }
}

# Firewall rule for Azure services
resource "azurerm_mssql_firewall_rule" "azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# Azure OpenAI (Commented out due to quota limitations)
# resource "azurerm_cognitive_account" "openai" {
#   name                = "${var.project_name}-openai"
#   location            = azurerm_resource_group.main.location
#   resource_group_name = azurerm_resource_group.main.name
#   kind                = "OpenAI"
#   sku_name            = "S0"
#
#   custom_subdomain_name = "${var.project_name}-openai"
#
#   tags = {
#     Environment = var.environment
#   }
# }
#
# resource "azurerm_cognitive_deployment" "gpt4_turbo" {
#   name                 = "gpt-4-turbo"
#   cognitive_account_id = azurerm_cognitive_account.openai.id
#
#   model {
#     format  = "OpenAI"
#     name    = "gpt-4"
#     version = "turbo-2024-04-09"
#   }
#
#   scale {
#     type     = "Standard"
#     capacity = 10
#   }
# }

# Application Insights
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project_name}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 90

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_application_insights" "main" {
  name                = "${var.project_name}-insights"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  retention_in_days   = 90

  tags = {
    Environment = var.environment
  }
}

# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = "${var.project_name}-dev"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "B1"

  tags = {
    Environment = var.environment
  }
}

# Ingestion API App Service
resource "azurerm_linux_web_app" "ingestion_api" {
  name                = "${var.project_name}-ingestion-api"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_service_plan.main.location
  service_plan_id     = azurerm_service_plan.main.id

  site_config {
    application_stack {
      python_version = "3.11"
    }
    always_on = true
  }

  app_settings = {
    "DATABASE_URL"                        = "mssql+pyodbc://${azurerm_mssql_server.main.administrator_login}:${random_password.sql_admin.result}@${azurerm_mssql_server.main.fully_qualified_domain_name}:1433/${azurerm_mssql_database.main.name}?driver=ODBC+Driver+18+for+SQL+Server"
    "AZURE_STORAGE_CONNECTION_STRING"    = azurerm_storage_account.dead_letter.primary_connection_string
    "APPINSIGHTS_INSTRUMENTATIONKEY"     = azurerm_application_insights.main.instrumentation_key
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = azurerm_application_insights.main.connection_string
    "ENVIRONMENT"                        = var.environment
    "LOG_LEVEL"                          = "INFO"
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
    "SCM_DO_BUILD_DURING_DEPLOYMENT"     = "true"
  }

  identity {
    type = "SystemAssigned"
  }

  logs {
    detailed_error_messages = true
    failed_request_tracing  = true

    application_logs {
      file_system_level = "Information"
    }

    http_logs {
      file_system {
        retention_in_days = 7
        retention_in_mb   = 35
      }
    }
  }

  tags = {
    Environment = var.environment
    Component   = "ingestion-api"
  }
}

# Dashboard App Service
resource "azurerm_linux_web_app" "dashboard" {
  name                = "${var.project_name}-dashboard"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_service_plan.main.location
  service_plan_id     = azurerm_service_plan.main.id

  site_config {
    application_stack {
      node_version = "18-lts"
    }
    always_on = true
  }

  app_settings = {
    "NEXT_PUBLIC_API_URL"                = "https://${azurerm_linux_web_app.ingestion_api.default_hostname}"
    "APPINSIGHTS_INSTRUMENTATIONKEY"     = azurerm_application_insights.main.instrumentation_key
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = azurerm_application_insights.main.connection_string
    "ENVIRONMENT"                        = var.environment
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
    "SCM_DO_BUILD_DURING_DEPLOYMENT"     = "true"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Environment = var.environment
    Component   = "dashboard"
  }
}

# Key Vault access for App Services
resource "azurerm_key_vault_access_policy" "ingestion_api" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = azurerm_linux_web_app.ingestion_api.identity[0].tenant_id
  object_id    = azurerm_linux_web_app.ingestion_api.identity[0].principal_id

  secret_permissions = ["Get", "List"]
}

resource "azurerm_key_vault_access_policy" "dashboard" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = azurerm_linux_web_app.dashboard.identity[0].tenant_id
  object_id    = azurerm_linux_web_app.dashboard.identity[0].principal_id

  secret_permissions = ["Get", "List"]
}

# Action Group for Alerts
resource "azurerm_monitor_action_group" "main" {
  name                = "${var.project_name}-alerts"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "lucyqa"

  email_receiver {
    name          = "admin"
    email_address = "admin@company.com"
  }

  webhook_receiver {
    name        = "slack"
    service_uri = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
  }

  tags = {
    Environment = var.environment
  }
}

# Metric Alerts
resource "azurerm_monitor_metric_alert" "high_error_rate" {
  name                = "${var.project_name}-high-error-rate"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.ingestion_api.id]
  description         = "High error rate detected in ingestion API"

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "Http5xx"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 10
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_monitor_metric_alert" "response_time" {
  name                = "${var.project_name}-slow-response"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.ingestion_api.id]
  description         = "Slow response time detected"

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "AverageResponseTime"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 5
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }

  tags = {
    Environment = var.environment
  }
}

# Outputs
output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "sql_server_fqdn" {
  value = azurerm_mssql_server.main.fully_qualified_domain_name
}

output "ingestion_api_url" {
  value = "https://${azurerm_linux_web_app.ingestion_api.default_hostname}"
}

output "dashboard_url" {
  value = "https://${azurerm_linux_web_app.dashboard.default_hostname}"
}

# output "openai_endpoint" {
#   value = azurerm_cognitive_account.openai.endpoint
# }

output "storage_account_name" {
  value = azurerm_storage_account.dead_letter.name
}

output "key_vault_uri" {
  value = azurerm_key_vault.main.vault_uri
} 