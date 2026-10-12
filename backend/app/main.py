import mimetypes
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

_backend_dir = Path(__file__).resolve().parents[1]
_root_dir = _backend_dir.parent
for _p in (str(_root_dir), str(_backend_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from dotenv import load_dotenv
    for _env_path in (_root_dir / ".env", _backend_dir / ".env"):
        if _env_path.is_file():
            load_dotenv(_env_path, override=False)
except Exception:
    pass


from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

try:
    from .database.schema import (
        create_tables,
        seed_round1_items_if_empty,
    )
    from .services.round2_service import init_round2
    from .routes.auth import router as auth_router
    from .routes.round1 import router as round1_router
    from .routes.round2 import router as round2_router
    from .routes.round3 import router as round3_router
    from .routes.game import router as game_router
    from .routes.admin import router as admin_router
    from .routes.transition import router as transition_router
except (ImportError, ValueError):
    from backend.app.database.schema import (
        create_tables,
        seed_round1_items_if_empty,
    )
    from backend.app.services.round2_service import init_round2
    from backend.app.routes.auth import router as auth_router
    from backend.app.routes.round1 import router as round1_router
    from backend.app.routes.round2 import router as round2_router
    from backend.app.routes.round3 import router as round3_router
    from backend.app.routes.game import router as game_router
    from backend.app.routes.admin import router as admin_router
    from backend.app.routes.transition import router as transition_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    seed_round1_items_if_empty()  # no-op when items already exist
    init_round2()  # Round 2 tables + the 24 cases (no-op when already loaded)
    yield


# Some Windows Python installs do not know .webp (the Round 1 images); register it so the
# static files are always served as image/webp.
mimetypes.add_type("image/webp", ".webp")

app = FastAPI(
    title="Project Chronos API",
    lifespan=lifespan
)


# CORS: Allow all origins, methods, headers, and credentials for seamless LAN and local access
cors_env = os.getenv("CORS_ORIGINS", "").strip()
if cors_env and cors_env != "*":
    origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Serve Round 1 images
BASE_DIR = Path(__file__).resolve().parents[1]

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)


# Built frontend (frontend/dist, created by `npm run build`). When present, the
# backend serves the whole app so one process hosts everything.
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"


@app.get("/api")
@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "service": "Project Chronos Central Mainframe",
        "timestamp": os.environ.get("SERVER_START_TIME", "2140"),
        "mode": "LAN_PARTY_HOST",
        "lan_ready": True
    }


@app.get("/")
def home():
    if FRONTEND_INDEX.is_file():
        return FileResponse(FRONTEND_INDEX)
    return {"message": "Project Chronos API is running", "lan_ready": True}


app.include_router(
    auth_router,
    prefix="/api/auth"
)

app.include_router(
    round1_router,
    prefix="/api/round1"
)

app.include_router(
    round2_router
)

app.include_router(
    round3_router
)

app.include_router(
    game_router
)

app.include_router(
    admin_router
)

app.include_router(
    transition_router
)


# Must stay LAST: catch-all for the frontend's files and client-side routes.
@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(request: Request, full_path: str):
    # Enforce localhost-only access for master leaderboard
    lower_path = full_path.lower().strip("/")
    if lower_path in ("leaderboard", "leaderboard.html", "admin") or lower_path.startswith("leaderboard"):
        client_host = request.client.host if request.client else ""
        is_local = client_host in ("127.0.0.1", "::1", "localhost", "testclient") or client_host.startswith("127.")
        if not is_local:
            raise HTTPException(
                status_code=403,
                detail="Access Denied: Master Leaderboard is strictly restricted to localhost and cannot be accessed over the network.",
            )

    if not FRONTEND_INDEX.is_file() or full_path.startswith(("api/", "static/")):
        raise HTTPException(status_code=404, detail="Not found")

    requested = (FRONTEND_DIST / full_path).resolve()
    if requested.is_file() and FRONTEND_DIST.resolve() in requested.parents:
        return FileResponse(requested)

    return FileResponse(FRONTEND_INDEX)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"\n⚡ [Project Chronos] Starting API Server on http://{host}:{port} ...\n")
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=False)

