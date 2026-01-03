import os
from pathlib import Path

def create_travelguru_v5():
    # Base project directory
    project_root = Path("travelguru-v5")
    
    # 1. Define complete Directory Structure
    dirs = [
        "backend/app/api/v1",
        "backend/app/core",
        "backend/app/db",
        "backend/app/agents/adk_travel",
        "backend/app/agents/langgraph_planner",
        "backend/app/agents/shared",
        "backend/app/mcp",
        "backend/app/mlops/training",
        "backend/app/mlops/pipelines",
        "backend/app/mlops/evaluation",
        "backend/app/mlops/monitoring",
        "backend/app/services",
        "frontend/src/components/chat",
        "frontend/src/components/dashboard",
        "frontend/src/components/billing",
        "frontend/src/hooks",
        "frontend/src/lib",
        "infrastructure/k8s",
        "infrastructure/terraform",
        "infrastructure/pipelines",
        "data/raw",
        "data/processed",
        "data/metadata",
    ]

    # 2. Define Core File Templates based on shared knowledge
    files = {
        "backend/requirements.txt": "fastapi==0.104.0\nuvicorn==0.24.0\ngoogle-genai==0.3.0\nlanggraph==0.1.0\nbrowser-use==0.1.0\nmcp==0.1.0\nmlflow==2.8.0\nstripe==7.1.0\nclerk-sdk-python\nsqlalchemy\npsycopg2-binary\n",
        
        "backend/app/main.py": "from fastapi import FastAPI\nfrom app.api.v1 import a2a_endpoints, mlops_api\n\napp = FastAPI(title='TravelGuru v5')\n\n# Mount routers for A2A and B2C logic\napp.include_router(a2a_endpoints.router, prefix='/api/v1/a2a')\napp.include_router(mlops_api.router, prefix='/api/v1/mlops')\n",
        
        "backend/app/agents/shared/protocol.py": "from pydantic import BaseModel\nfrom typing import List, Optional, Any\n\nclass MessagePart(BaseModel):\n    text: Optional[str] = None\n\nclass Message(BaseModel):\n    role: str\n    parts: List[MessagePart]\n    id: str\n    context_id: str\n\nclass AgentCard(BaseModel):\n    name: str\n    description: str\n    tools: List[dict]\n",
        
        "backend/app/db/models.py": "from sqlalchemy import Column, String, Integer, JSON, TIMESTAMP\nfrom sqlalchemy.ext.declarative import declarative_base\n\nBase = declarative_base()\n\nclass User(Base):\n    __tablename__ = 'users'\n    id = Column(String, primary_key=True)  # Clerk ID\n    stripe_id = Column(String)\n    tokens_used = Column(Integer, default=0)\n    subscription = Column(String, default='free')\n",
        
        "data/metadata/well-known-agents.json": '{"agents": [{"name": "Planner", "id": "lg-planner"}, {"name": "Travel-Agent", "id": "adk-agent"}]}',
        
        "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: ./backend\n    ports: ['8000:8000']\n  mcp-server:\n    build: ./backend/app/mcp\n    ports: ['5000:5000']\n"
    }

    # Create directories and __init__.py files
    for d in dirs:
        path = project_root / d
        path.mkdir(parents=True, exist_ok=True)
        if "backend" in d: # Initialize python packages
            (path / "__init__.py").touch()

    # Create template files
    for path_str, content in files.items():
        file_path = project_root / path_str
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w") as f:
            f.write(content)

    print(f"🚀 TravelGuru-v5 structure created at: {project_root.absolute()}")

if __name__ == "__main__":
    create_travelguru_v5()
