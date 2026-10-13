# Production 04 — MCP Tools: Agent Tool Servers

## What is MCP?

MCP (Model Context Protocol) is an open protocol developed by Anthropic that defines
a standard interface between AI assistants and external tools/data sources.

Without MCP: Every agent has its own bespoke way of calling tools. Jira integration
in agent A is incompatible with Jira integration in agent B. Maintenance is a nightmare.

With MCP: Tools are exposed as standardized servers. Any MCP-compatible agent can
connect to any MCP server and use its tools — like browser plugins, but for AI agents.

---

## The Real Story

Building the healthcare Jira assistant required calling multiple external systems:
- Jira: create tickets, update status, add comments, query sprint boards
- Pharmacy API: look up prescription records, check formulary, verify patient data
- Internal scheduling system: check bed availability, assign transfer coordinators

Without MCP, each of these would be custom code inside the agent. With MCP, they
become separate servers. The agent connects to whichever servers it needs.

This made a critical architectural difference: **the Jira MCP server** we built for
the healthcare assistant is now reused by the Jira assistant project, the V2 migration
tool's ticket tracker, and internal tools — without any code duplication.

---

## MCP Architecture

```
Claude Agent
     │
     ├── Connects to: Jira MCP Server
     │     Exposes tools: create_ticket, update_ticket, search_tickets, ...
     │
     ├── Connects to: NovaDash MCP Server
     │     Exposes tools: create_task, list_projects, invite_user, ...
     │
     └── Connects to: Database MCP Server
           Exposes tools: query, insert, update, ...
```

The agent sees all tools from all connected servers in a single unified tool list.
It can call `create_ticket` or `create_task` and the MCP layer routes to the right server.

---

## Building an MCP Server

An MCP server is a Python process that exposes tools via the MCP protocol:

```python
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as types

app = Server("novadash-mcp")

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="create_task",
            description="Create a new task in a NovaDash project",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "project_id": {"type": "string", "description": "Project ID"},
                    "priority": {
                        "type": "string",
                        "enum": ["Low", "Medium", "High", "Urgent"]
                    }
                },
                "required": ["title", "project_id"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "create_task":
        # Call NovaDash API
        import httpx
        response = httpx.post(
            "https://api.novadash.io/v2/tasks",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json=arguments,
        )
        return [types.TextContent(type="text", text=response.text)]
    raise ValueError(f"Unknown tool: {name}")
```

---

## Connecting an Agent to an MCP Server

```python
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_agent_with_mcp():
    # Start the MCP server as a subprocess
    server_params = StdioServerParameters(
        command="python",
        args=["novadash_mcp_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Get all available tools from the MCP server
            tools = await session.list_tools()

            # Convert to Claude tool format
            claude_tools = [
                {"name": t.name, "description": t.description, "input_schema": t.inputSchema}
                for t in tools.tools
            ]

            client = Anthropic()
            # Now Claude can call any tool from the MCP server
            response = client.messages.create(
                model="claude-sonnet-4-5-20251001",
                max_tokens=4096,
                tools=claude_tools,
                messages=[{"role": "user", "content": "Create a task to fix the login bug"}],
            )
```

---

## Why MCP Over Direct API Calls?

| Direct API Calls                | MCP                                     |
|---------------------------------|-----------------------------------------|
| Tool logic inside the agent     | Tool logic in the MCP server            |
| Rewriting for every agent       | One server, many agents                 |
| Auth credentials in agent code  | Auth handled in server, not exposed     |
| No standard contract            | Standard MCP interface                  |
| Hard to test tool logic alone   | MCP server testable independently       |

---

## Coming Soon

Full implementation covering:
- NovaDash MCP server (tasks, projects, users endpoints)
- Connecting Claude to the MCP server
- Multi-server agent (Jira + NovaDash + GitHub simultaneously)
- Authentication and credential management for MCP servers
- Testing MCP servers independently

**Prerequisites:** `pip install mcp anthropic`
