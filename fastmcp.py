from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio
import json

class FastMCP:
    def __init__(self, name: str, stateless_http: bool = False):
        self.name = name
        self.stateless_http = stateless_http
        self.app = FastAPI(title=f"{name} MCP")
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

    def _register_streamable_routes(self):
        @self.app.get("/sse")
        async def sse_stream(request: Request):
            """
            A basic Server-Sent Events stream endpoint. 
            Replace this with your tool dispatch or chat streaming logic.
            """

            async def event_generator():
                yield "retry: 1000\n\n"  # instruct client to retry every 1s
                count = 0
                while not await request.is_disconnected():
                    yield f"data: {json.dumps({'message': f'Ping {count}'})}\n\n"
                    await asyncio.sleep(2)
                    count += 1
                yield "event: close\ndata: connection closed\n\n"

            return StreamingResponse(event_generator(), media_type="text/event-stream")
