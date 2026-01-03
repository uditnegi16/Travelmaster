from pydantic import BaseModel
from typing import List, Optional, Any

class MessagePart(BaseModel):
    text: Optional[str] = None

class Message(BaseModel):
    role: str
    parts: List[MessagePart]
    id: str
    context_id: str

class AgentCard(BaseModel):
    name: str
    description: str
    tools: List[dict]
