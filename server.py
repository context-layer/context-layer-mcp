import json
import os
from typing import Any, Dict, Optional

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


def _format_state_value(value: Any) -> str:
    if value is None:
        result = "null"
    elif isinstance(value, bool):
        result = "true" if value else "false"
    elif isinstance(value, (int, float)):
        result = str(value)
    elif isinstance(value, str):
        clean = value.strip()
        result = clean if clean else "(empty)"
    else:
        result = json.dumps(value, sort_keys=True, ensure_ascii=False)

    if len(result) > 500:
        result = result[:500] + "...[truncated]"
    return result


def build_cl_message(
    step_description: str,
    state: Dict[str, Any],
    context: Optional[str] = None,
    constraint: Optional[str] = None,
) -> str:
    """Build a concise, deterministic natural-language message for Context Layer."""
    lines = [
        f"Step: {step_description.strip()}",
        "",
        "State:",
    ]
    for key in sorted(state.keys()):
        lines.append(f"- {key}: {_format_state_value(state[key])}")
    ctx = (context or "").strip()
    if ctx:
        lines.extend(["", f"Context: {ctx}"])
    cst = (constraint or "").strip()
    if cst:
        lines.extend(["", f"Constraint: {cst}"])
    return "\n".join(lines)


# ---- Tools ----

@mcp.tool()
async def send_message(
    message: Optional[str] = None,
    step_description: Optional[str] = None,
    state: Optional[Dict[str, Any]] = None,
    context: Optional[str] = None,
    constraint: Optional[str] = None,
    workflow_end: bool = False,
    stateless: bool = False,
) -> Dict[str, Any]:
    """Send a message to Context Layer.

    Provide either a plain ``message`` OR ``step_description`` with ``state``
    (State Bridge); do not use both. Optional ``context`` and ``constraint``
    apply only to the structured path.

    workflow_end: ends workflow when True (Flow only).
    stateless: runs outside workflow (Flow only).
    These flags cannot be used together.
    """

    msg = message.strip() if isinstance(message, str) else ""
    step = step_description.strip() if isinstance(step_description, str) else ""

    if msg and step:
        raise Exception("cannot provide both message and step_description")
    if not msg and not step:
        raise Exception("must provide either message or step_description")
    if step and state is None:
        raise Exception("step_description requires state")
    if step and not isinstance(state, dict):
        raise Exception("state must be a dict")

    if msg:
        final_message = msg
    else:
        final_message = build_cl_message(step, state, context, constraint)

    final_message = final_message.strip()
    if not final_message:
        raise Exception("message must be a non-empty string")

    if workflow_end and stateless:
        raise Exception("workflowEnd cannot be combined with stateless")

    payload: Dict[str, Any] = {"message": final_message}
    if workflow_end:
        payload["workflowEnd"] = True
    if stateless:
        payload["stateless"] = True

    data = await _post_json("/api/execute", payload)

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
