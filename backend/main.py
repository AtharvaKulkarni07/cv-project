"""FastAPI entry point — mounts CORS, static files, and stitch router."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers.stitch import router as stitch_router

# Output directory for generated images
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

app = FastAPI(title="Pano — Panorama Stitching API", version="1.0.0")

# CORS — allow the Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated images at /outputs/<filename>
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

# Register API routes
app.include_router(stitch_router, prefix="/api/stitch", tags=["stitch"])


@app.get("/health")
async def health():
    return {"status": "ok"}