import os
from typing import Any, Dict

import httpx
from mcp.server.fastmcp import FastMCP

# ---- Config ----
CL_API_KEY = os.getenv("CL_API_KEY")
CL_BASE_URL = os.getenv("CL_BASE_URL", "https://cl.kaisek.com")

if not CL_API_KEY:
    raise ValueError("CL_API_KEY environment variable is required")

TIMEOUT = 30.0

# ---- MCP Server ----
mcp = FastMCP("context-layer-mcp")

# ---- Helpers ----

def _headers() -> Dict[str, str]:
    return {
        "x-api-key": CL_API_KEY,
        "Content-Type": "application/json",
    }


def _raise_if_http_error(response: httpx.Response, data: Any) -> None:
    if 200 <= response.status_code < 300:
        return
    if isinstance(data, dict):
        raise Exception(
            f"CL API error ({response.status_code}): {data.get('error', response.text)}"
        )
    raise Exception(f"CL API error ({response.status_code}): {response.text}")


async def _post_json(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            f"{CL_BASE_URL}{path}",
            json=payload,
            headers=_headers(),
        )

    try:
        data = response.json()
    except Exception:
        if not (200 <= response.status_code < 300):
            raise Exception(f"CL API error ({response.status_code}): {response.text}")
        raise Exception(f"Invalid CL response: {response.text}")

    if not isinstance(data, dict):
        raise Exception(f"Invalid CL response: {response.text}")

    _raise_if_http_error(response, data)
    return data


# ---- Tools ----

@mcp.tool()
async def send_message(message: str) -> Dict[str, Any]:
    """Send a message to Context Layer."""

    if not isinstance(message, str):
        raise Exception("message must be a non-empty string")
    message = message.strip()
    if not message:
        raise Exception("message must be a non-empty string")

    data = await _post_json("/api/flow", {"message": message})

    if "output_text" not in data:
        raise Exception(f"Unexpected CL response: {data}")

    return {
        "output_text": data["output_text"],
        "raw": data,
    }


app = mcp.sse_app()

# ---- Entry ----

if __name__ == "__main__":
    mcp.run()
