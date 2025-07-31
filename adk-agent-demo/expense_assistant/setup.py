#!/usr/bin/env python3

import os
import subprocess
import sys

def run_command(command, check=True):
    """Run a shell command"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if check and result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"Error output: {result.stderr}")
        sys.exit(1)
    return result

def setup_development_environment():
    """Set up the development environment"""
    print("🚀 Setting up Expense Assistant development environment...")
    
    # Create virtual environment
    print("Creating virtual environment...")
    run_command("python -m venv venv")
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate && pip install -r requirements.txt"
    else:  # Unix/Linux/macOS
        activate_cmd = "source venv/bin/activate && pip install -r requirements.txt"
    
    print("Installing dependencies...")
    run_command(activate_cmd)
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        print("Creating .env file...")
        with open(".env", "w") as f:
            f.write("""# Azure AI Search Configuration
AZURE_AI_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_AI_SEARCH_KEY=your-search-api-key
AZURE_AI_SEARCH_INDEX=expense-policy-index

# Google AI Configuration
GOOGLE_API_KEY=your-google-api-key

# Local PostgreSQL (for development)
AZURE_POSTGRES_CONNECTION_STRING=postgresql://adk_user:secure_password@localhost:5432/expense_sessions

# Application Configuration
PORT=8000
ENVIRONMENT=development
""")
        print("⚠️  Please update the .env file with your actual configuration values")
    
    print("✅ Development environment setup complete!")
    print("\n📋 Next steps:")
    print("1. Update .env file with your Azure AI Search and Google API credentials")
    print("2. Start local development with ADK web interface: adk web")
    print("3. Or run the FastAPI server directly: python main.py")
    print("4. Access the app at: http://localhost:8000")
    print("5. Test your agent at: http://localhost:8000/docs")

if __name__ == "__main__":
    setup_development_environment()
