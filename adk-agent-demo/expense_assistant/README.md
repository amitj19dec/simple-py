# Expense Report Assistant - ADK Agent

An intelligent AI agent built with Google's Agent Development Kit (ADK) that helps employees prepare and submit expense reports while ensuring compliance with company travel and expense policies.

## 🎯 Features

- **Policy Knowledge Integration** - Direct connection to Azure AI Search vector database
- **Smart Expense Categorization** - Automatic classification based on descriptions
- **Real-time Validation** - Policy compliance checking before submission
- **Document Requirements** - Identifies required receipts/approvals
- **Multi-expense Summaries** - Complete trip expense analysis
- **Azure Container Support** - Ready for containerized deployment

## 🏗️ Architecture

- **Agent Framework**: Google ADK v1.8.0
- **Knowledge Base**: Azure AI Search with semantic search
- **Session Storage**: PostgreSQL (Azure Database or local)
- **API Framework**: FastAPI with ADK integration
- **Deployment**: Docker containers on Azure

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Azure AI Search service with expense policy documents
- Google API key for Gemini models
- Azure PostgreSQL database (optional, for persistent sessions)

### 1. Environment Setup

```bash
# Clone or download the project
cd expense_assistant

# Run the setup script
python setup.py

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

### 2. Configuration

Update the `.env` file with your credentials:

```env
# Azure AI Search Configuration
AZURE_AI_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_AI_SEARCH_KEY=your-search-api-key
AZURE_AI_SEARCH_INDEX=expense-policy-index

# Google AI Configuration
GOOGLE_API_KEY=your-google-api-key

# Database Configuration
AZURE_POSTGRES_CONNECTION_STRING=postgresql://user:pass@host:5432/expense_sessions
```

### 3. Running the Agent

#### Option A: ADK Web Interface (Recommended for testing)
```bash
adk web
```
Access at: http://localhost:8000

#### Option B: FastAPI Server (Production-ready)
```bash
python main.py
```
Access at: http://localhost:8000
API docs at: http://localhost:8000/docs

#### Option C: Docker Compose (Full stack)
```bash
docker-compose up
```

## 🧪 Testing the Agent

### Example Conversations

**Policy Question:**
```
User: "What's the daily meal allowance for business travel?"
Agent: Searches policy database and provides specific limits with citations
```

**Expense Validation:**
```
User: "I stayed at a hotel for $420 per night. Is this okay?"
Agent: Validates against policy, identifies violation, suggests alternatives
```

**Expense Categorization:**
```
User: "I took an Uber from airport to hotel for $45"
Agent: Categorizes as transportation, validates compliance, identifies required docs
```

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# Agent interaction
curl -X POST http://localhost:8000/run_sse \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "expense_report_assistant",
    "user_id": "test_user",
    "session_id": "test_session",
    "new_message": {
      "role": "user",
      "parts": [{"text": "What are the meal expense limits?"}]
    }
  }'
```

## 🚀 Azure Deployment

### Using the Deployment Script

```bash
# Make the script executable
chmod +x deploy.sh

# Set your environment variables
export AZURE_AI_SEARCH_ENDPOINT="your-endpoint"
export AZURE_AI_SEARCH_KEY="your-key"
export GOOGLE_API_KEY="your-key"

# Deploy to Azure
./deploy.sh
```

### Manual Deployment Steps

1. **Create Azure Container Registry**
2. **Build and push Docker image**
3. **Create App Service with container**
4. **Configure environment variables**
5. **Set up Azure PostgreSQL (optional)**

## 📁 Project Structure

```
expense_assistant/
├── expense_agent/           # ADK agent module
│   ├── __init__.py         # Agent exports
│   └── agent.py            # Main agent logic & tools
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Local development stack
├── deploy.sh              # Azure deployment script
├── setup.py               # Environment setup script
├── .env                   # Configuration file
└── README.md              # This file
```

## 🔧 Agent Tools

The agent includes four main tools:

1. **`search_expense_policy`** - Queries Azure AI Search for policy information
2. **`validate_expense_data`** - Checks expenses against policy rules
3. **`categorize_expense`** - Smart categorization of expenses
4. **`generate_expense_summary`** - Creates comprehensive expense reports

## 🛠️ Customization

### Adding Custom Validation Rules

Edit the `validate_expense_data` function in `expense_agent/agent.py`:

```python
# Add your custom policy rules
if category == "your_category":
    if amount > YOUR_LIMIT:
        validation_results["violations"].append("Custom violation message")
```

### Integrating with Your Expense System

Extend the tools to integrate with your existing expense management system:

```python
def submit_to_expense_system(expense_data: dict) -> dict:
    """Submit validated expense to your system"""
    # Your API integration here
    pass
```

## 📊 Monitoring & Analytics

The agent includes built-in monitoring:

- **Health endpoints** for uptime monitoring
- **Cloud Trace integration** for request tracing
- **Session persistence** for conversation analytics
- **Policy compliance metrics** tracking

## 🔒 Security Considerations

- Use Azure Key Vault for secrets in production
- Configure appropriate CORS origins
- Implement authentication for production endpoints
- Use managed identities for Azure service access
- Regular security updates for dependencies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the Apache License 2.0 - see the Google ADK license for details.

## 🆘 Support

For issues related to:
- **ADK Framework**: Check [Google ADK Documentation](https://google.github.io/adk-docs/)
- **Azure Services**: Consult Azure documentation
- **This Implementation**: Create an issue in the project repository

## 🚀 Next Steps

- **Scale**: Deploy to Azure Container Apps for auto-scaling
- **Enhance**: Add more sophisticated ML-based categorization
- **Integrate**: Connect with your existing expense management system
- **Monitor**: Set up comprehensive logging and alerting
- **Extend**: Add support for multiple company policies

---

**Built with Google ADK v1.8.0 | Ready for Azure Deployment**
