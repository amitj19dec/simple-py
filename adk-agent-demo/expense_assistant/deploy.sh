#!/bin/bash

# Azure deployment script for Expense Assistant
set -e

# Configuration
RESOURCE_GROUP="expense-assistant-rg"
LOCATION="eastus"
ACR_NAME="expenseassistantacr"
APP_NAME="expense-assistant-app"
PLAN_NAME="expense-assistant-plan"

echo "🚀 Deploying Expense Assistant to Azure..."

# Create resource group
echo "Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
echo "Creating Azure Container Registry..."
az acr create --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true

# Build and push Docker image
echo "Building and pushing Docker image..."
az acr build --registry $ACR_NAME \
    --image expense-assistant:latest .

# Create App Service Plan
echo "Creating App Service Plan..."
az appservice plan create --name $PLAN_NAME \
    --resource-group $RESOURCE_GROUP \
    --sku B1 \
    --is-linux

# Create Web App
echo "Creating Web App..."
az webapp create --resource-group $RESOURCE_GROUP \
    --plan $PLAN_NAME \
    --name $APP_NAME \
    --deployment-container-image-name $ACR_NAME.azurecr.io/expense-assistant:latest

# Configure Web App settings
echo "Configuring Web App settings..."
az webapp config appsettings set --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --settings \
    AZURE_AI_SEARCH_ENDPOINT="$AZURE_AI_SEARCH_ENDPOINT" \
    AZURE_AI_SEARCH_KEY="$AZURE_AI_SEARCH_KEY" \
    AZURE_AI_SEARCH_INDEX="$AZURE_AI_SEARCH_INDEX" \
    GOOGLE_API_KEY="$GOOGLE_API_KEY" \
    PORT=8000

# Configure container settings
az webapp config container set --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --docker-custom-image-name $ACR_NAME.azurecr.io/expense-assistant:latest \
    --docker-registry-server-url https://$ACR_NAME.azurecr.io

echo "✅ Deployment complete!"
echo "🌐 Access your app at: https://$APP_NAME.azurewebsites.net"
