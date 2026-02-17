# backend/app/adapters/interceptors.py
from langchain_mcp_adapters.interceptors import MCPToolCallRequest
from langchain_mcp_adapters.client import MultiServerMCPClient

async def auth_header_interceptor(request: MCPToolCallRequest, handler):
    """
    Simple interceptor that ensures an Authorization header is present.
    It reads runtime.context.api_key if available; otherwise uses env fallback.
    """
    # runtime may be None in some test contexts; guard access
    runtime = getattr(request, "runtime", None)
    api_key = None
    if runtime and getattr(runtime, "context", None):
        api_key = runtime.context.get("api_key")
    if not api_key:
        # fallback token can be set via env var MCP_TOKEN
        import os
        api_key = os.getenv("MCP_TOKEN", "")
    headers = {**(request.headers or {}), "Authorization": f"Bearer {api_key}"}
    modified = request.override(headers=headers)
    return await handler(modified)

async def append_structured_content_interceptor(request: MCPToolCallRequest, handler):
    """
    If the tool returns structuredContent (artifact), append a short JSON string
    to the tool message content so the model can see machine-readable data.
    """
    result = await handler(request)
    # Some tool results expose structuredContent attribute; guard access
    structured = getattr(result, "structuredContent", None)
    if structured:
        # Append a compact representation to the content list if available
        try:
            import json
            snippet = json.dumps(structured, separators=(",", ":"))[:1000]
            # Many result objects expose .content as a list of content blocks
            if hasattr(result, "content") and isinstance(result.content, list):
                result.content.append({"type": "text", "text": snippet})
        except Exception:
            # If anything goes wrong, return the original result
            pass
    return result

def make_interceptors():
    """
    Return a list of interceptors to pass into MultiServerMCPClient.
    Order matters: first in list is outermost.
    """
    return [auth_header_interceptor, append_structured_content_interceptor]
