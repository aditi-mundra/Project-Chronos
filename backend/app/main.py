"""
Project Chronos — FastAPI Main Application Entrypoint
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database.schema import create_tables
from .routes import auth, game, round3, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema on startup
    create_tables()
    yield

app = FastAPI(
    title="Project Chronos — Central Mainframe API",
    description="Backend API for Project Chronos (Year 2140 Temporal Investigation Game)",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend (Vite dev server and production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(auth.router)
app.include_router(game.router)
app.include_router(round3.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {
        "status": "online",
        "system": "PROJECT CHRONOS CENTRAL MAINFRAME",
        "protocol": 2140,
        "active_round": 3
    }
