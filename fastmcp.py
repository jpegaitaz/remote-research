from fastapi import FastAPI
from fastapi.responses import JSONResponse

class FastMCP:
    def __init__(self, name: str, stateless_http: bool = False):
        self.name = name
        self.stateless_http = stateless_http
        self.app = FastAPI(title=f"{name} MCP")
        self.tools = {}
        self.resources = {}
        self.prompts = {}

        self._register_base_routes()

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
        @self.app.get("/")
        def health_check():
            return JSONResponse(content={"status": "ok", "name": self.name})
