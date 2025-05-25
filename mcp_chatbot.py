import os
import json
import asyncio
from dotenv import load_dotenv
from anthropic import Anthropic
from contextlib import AsyncExitStack
from typing import List, Dict, TypedDict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

# Load .env
load_dotenv()
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY not set in environment variables")

# Define tool type
class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict


class MCP_ChatBot:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        self.sessions: List[ClientSession] = []
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        try:
            transport_type = server_config.get("transport", "stdio")
            if transport_type == "http":
                read, write, _get_session_id = await self.exit_stack.enter_async_context(
                    streamablehttp_client(server_config["url"])
                )
            else:
                server_params = StdioServerParameters(**server_config)
                read, write = await self.exit_stack.enter_async_context(stdio_client(server_params))

            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.sessions.append(session)

            response = await session.list_tools()
            tools = response.tools
            print(f"✅ Connected to '{server_name}' with tools: {[t.name for t in tools]}")

            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })

        except Exception as e:
            print(f"❌ Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self):
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)

            servers = data.get("mcpServers", {})
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"❌ Error loading server configuration: {e}")
            raise

    async def chat_once(self, query: str) -> str:
        messages = [{'role': 'user', 'content': query}]
        full_reply = ""

        while True:
            response = self.anthropic.messages.create(
                model='claude-3-7-sonnet-20250219',
                max_tokens=2024,
                tools=self.available_tools,
                messages=messages
            )

            assistant_content = []
            has_tool_use = False

            for content in response.content:
                if content.type == 'text':
                    full_reply += content.text
                    assistant_content.append(content)
                elif content.type == 'tool_use':
                    has_tool_use = True
                    assistant_content.append(content)
                    messages.append({'role': 'assistant', 'content': assistant_content})

                    session = self.tool_to_session.get(content.name)
                    if not session:
                        return f"❌ Tool '{content.name}' not found."

                    result = await session.call_tool(content.name, arguments=content.input)
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": result.content
                        }]
                    })

            if not has_tool_use:
                break

        return full_reply or "🤖 No response generated."

    async def chat_loop(self):
        print("\n📚 MCP Chatbot started (CLI mode). Type 'quit' to exit.")
        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == 'quit':
                    break
                response = await self.chat_once(query)
                print(f"\n🤖 {response}\n")
            except Exception as e:
                print(f"❌ Error: {e}")

    async def cleanup(self):
        await self.exit_stack.aclose()


# ===== FastAPI HTTP Mode =====
app = FastAPI(title="MCP Chatbot")

# Allow cross-origin requests (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chatbot = MCP_ChatBot()

@app.on_event("startup")
async def startup_event():
    await chatbot.connect_to_servers()

@app.on_event("shutdown")
async def shutdown_event():
    await chatbot.cleanup()

@app.post("/chat")
async def chat_endpoint(request: Request):
    try:
        body = await request.json()
        query = body.get("query")
        if not query:
            return JSONResponse(status_code=400, content={"error": "Missing query"})
        print(f"🛠️ Received POST to /chat: {body}")
        response = await chatbot.chat_once(query)
        return {"response": response}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ===== CLI or HTTP Entrypoint =====
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        port = int(os.environ.get("PORT", 8080))
        uvicorn.run("mcp_chatbot:app", host="0.0.0.0", port=port)
    else:
        asyncio.run(chatbot.connect_to_servers())
        asyncio.run(chatbot.chat_loop())
