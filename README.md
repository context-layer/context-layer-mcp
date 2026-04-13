# Context Layer MCP Server

This is a minimal MCP (Model Context Protocol) server for Context Layer (CL).

It exposes one tool:

- **`send_message(message: string)`** — This tool sends a message to Context Layer and returns the response.

## CL Backend usage

Default API base: **`https://cl.kaisek.com`** (override with `CL_BASE_URL`).

The server calls **`POST /api/flow`** with body `{"message": "<your message>"}`. Requests send the **`x-api-key`** header (from `CL_API_KEY`). On success, the tool returns **`output_text`** and **`raw`** (the full parsed JSON body from CL).

### Usage example

From any MCP client, call **`send_message`** with a single string argument, for example:

- `message`: `"Hello from my agent"`

## Setup

### 1. Install dependencies

From the project directory:

```bash
pip install -r requirements.txt
```

Using a virtual environment is recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure `CL_API_KEY`

The server reads your Context Layer API key from the environment. It **must** be set before the process starts; if it is missing, the server exits with `CL_API_KEY environment variable is required`.

**Shell (current session):**

```bash
export CL_API_KEY="your-cl-api-key"
```

**Optional — override the API host** (defaults to `https://cl.kaisek.com`):

```bash
export CL_BASE_URL="https://cl.kaisek.com"
```

For Claude Desktop, put these in the `env` block of the MCP server entry (see below) instead of exporting in the shell.

### 3. Run the server

The server uses **stdio** (standard input/output) to speak MCP, which is what Claude Desktop and other MCP clients expect.

From the project directory, with `CL_API_KEY` set:

```bash
python server.py
```

If your `python` is not Python 3, use `python3`. If you use a venv, run with that environment’s interpreter (for example `.venv/bin/python server.py`).

To smoke-test that dependencies and config load, you can run the same command; the process will wait on stdio until a client connects.

### 4. Add it to Claude Desktop MCP config

Claude Desktop loads MCP servers from a JSON config file. Edit that file in a plain text editor, then **fully quit and restart** Claude Desktop so changes apply.

**Config file paths:**

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

If the file does not exist, create it with at least a top-level `mcpServers` object.

**Example** — replace the Python path and project path with **absolute paths** on your machine, and set your real API key:

```json
{
  "mcpServers": {
    "context-layer-mcp": {
      "command": "/absolute/path/to/context-layer-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/context-layer-mcp/server.py"],
      "env": {
        "CL_API_KEY": "your-cl-api-key"
      }
    }
  }
}
```

If you are not using a venv, point `command` at your `python3` binary (for example from `which python3` on macOS/Linux).

To use a non-default CL base URL, add it under `env`:

```json
"CL_BASE_URL": "https://cl.kaisek.com"
```

After restarting Claude Desktop, the **context-layer-mcp** server should appear among your MCP tools.

For more detail, see [Getting started with local MCP servers on Claude Desktop](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop).
