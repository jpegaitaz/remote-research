from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json

class FastMCP:
    def __init__(self, name: str, stateless_http: bool = False):
        self.name = name
        self.stateless_http = stateless_http
        self.app = FastAPI(title=f"{name} MCP")

        # ✅ CORS middleware: allow frontend access
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 🔒 Replace "*" with your frontend URL in production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.tools = {}
        self.resources = {}
        self.prompts = {}

        self._register_base_routes()
        if not self.stateless_http:
            self._register_streamable_routes()

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator

    def resource(self, route: str):
        def decorator(func):
            self.resources[route] = func
            self.app.get(f"/resource/{route}")(func)
            return func
        return decorator

    def prompt(self):
        def decorator(func):
            self.prompts[func.__name__] = func
            return func
        return decorator

    def _register_base_routes(self):
        @self.app.api_route("/", methods=["GET", "HEAD"])
        def root():
            return JSONResponse(content={"status": "ok", "name": self.name})

        @self.app.api_route("/health", methods=["GET", "HEAD"])
        def health():
            return JSONResponse(content={"status": "ok"})

        @self.app.get("/config")
        def config():
            return JSONResponse(content={
                "tools": list(self.tools.keys()),
                "resources": list(self.resources.keys()),
                "prompts": list(self.prompts.keys()),
            })

        @self.app.post("/chat")
        async def chat_handler(req: Request):
            data = await req.json()
            query = data.get("query")
            print(f"🛠️ Received POST to /chat: {data}")

            if not query:
                return JSONResponse({"reply": "⚠️ No query provided"}, status_code=400)

            try:
                from mcp_chatbot import MCP_ChatBot
                bot = MCP_ChatBot()
                await bot.connect_to_servers()
                reply = await bot.chat_once(query)
                await bot.cleanup()
                return JSONResponse({"reply": reply})
            except Exception as e:
                return JSONResponse({"reply": f"❌ Error: {str(e)}"}, status_code=500)

    def _register_streamable_routes(self):
        @self.app.get("/sse")
        async def sse_stream(request: Request):
            async def event_generator():
                yield "retry: 1000\n\n"
                count = 0
                while not await request.is_disconnected():
                    msg = {
                        "event": "ping",
                        "data": f"Ping {count}"
                    }
                    yield f"data: {json.dumps(msg)}\n\n"
                    await asyncio.sleep(2)
                    count += 1
                yield "event: close\ndata: connection closed\n\n"

            return StreamingResponse(event_generator(), media_type="text/event-stream")
