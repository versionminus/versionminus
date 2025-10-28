from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI

mcp = FastMCP("hello-world-app")
app = FastAPI()

@mcp.tool()
def greet_user(name: str) -> dict:
    """Display a personalized greeting"""
    return {
        "content": [{"type": "text", "text": f"Greeting {name}"}],
        "structuredContent": {"message": f"Hello, {name}!"},
        "_meta": {
            "openai/outputTemplate": "ui://widget/hello.html",
            "openai/toolInvocation/invoking": "Creating greeting…",
            "openai/toolInvocation/invoked": "Greeting ready."
        }
    }