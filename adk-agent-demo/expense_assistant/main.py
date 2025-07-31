# main.py - Updated for Latest ADK
from google.adk import get_fast_api_app
from google.adk.sessions import DatabaseSessionService
import os
from dotenv import load_dotenv

load_dotenv()

# Configure session service for Azure PostgreSQL
session_service = None
if os.getenv("AZURE_POSTGRES_CONNECTION_STRING"):
    session_service = DatabaseSessionService(
        db_url=os.getenv("AZURE_POSTGRES_CONNECTION_STRING")
    )

# Create FastAPI app with latest ADK syntax
app = get_fast_api_app(
    # Import agent directly - latest ADK pattern
    agent_import_path="expense_agent.agent:root_agent",
    
    # Session service configuration
    session_service=session_service,
    
    # Enable ADK Web UI
    enable_web_ui=True,
    
    # Enable tracing
    enable_tracing=True,
    
    # CORS configuration
    cors_allow_origins=["*"],  # Configure appropriately for production
    cors_allow_credentials=True,
    cors_allow_methods=["*"],
    cors_allow_headers=["*"],
)

# Custom health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "expense-report-assistant",
        "version": "1.0.0",
        "adk_version": "latest"
    }

# Custom endpoint for direct policy search
@app.post("/api/search-policy")
async def search_policy_direct(request: dict):
    """Direct access to policy search for testing"""
    from expense_agent.agent import search_expense_policy
    return search_expense_policy(
        query=request.get("query", ""),
        category=request.get("category")
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") == "development"
    )