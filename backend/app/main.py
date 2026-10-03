import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from .database.schema import create_tables
from .routes import auth, game, round3, admin

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
ASSETS_DIR = FRONTEND_DIST / "assets"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema on startup
    create_tables()
    yield

app = FastAPI(
    title="Project Chronos — Unified Central Mainframe",
    description="Unified single-server host for Project Chronos (Web App + REST API)",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API route modules under /api
app.include_router(auth.router)
app.include_router(game.router)
app.include_router(round3.router)
app.include_router(admin.router)

# Mount static asset directory if built
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

@app.get("/api/health")
def health():
    return {
        "status": "online",
        "system": "PROJECT CHRONOS CENTRAL MAINFRAME",
        "protocol": 2140,
        "single_server_mode": True
    }

# SPA Fallback: Serve React index.html for all non-API routes
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    # Do not intercept API or docs routes
    if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
        return HTMLResponse(content="Not Found", status_code=404)
    
    # Check if a specific static file in dist is requested (e.g. vite.svg, favicon.ico)
    static_file = FRONTEND_DIST / full_path
    if full_path and static_file.is_file():
        return FileResponse(str(static_file))
    
    # Return index.html for SPA client-side routing
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    
    return HTMLResponse(
        content="""
        <html>
            <head><title>Project Chronos — Initializing</title></head>
            <body style="background:#07060A; color:#E0D4FC; font-family:monospace; padding:40px; text-align:center;">
                <h1 style="color:#A855F7;">PROJECT CHRONOS CENTRAL MAINFRAME</h1>
                <p>Frontend assets are building. Run <code>npm run build</code> inside <code>frontend/</code> or use <code>python3 run.py</code>.</p>
                <p><a href="/docs" style="color:#38BDF8;">Access Swagger API Docs</a></p>
            </body>
        </html>
        """,
        status_code=200
    )

