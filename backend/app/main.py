"""
LunaScope 3.0 FastAPI Application Entrypoint.
Provides REST API endpoints and static file serving for the React frontend.
"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router as api_router
from app.api.ws import ws_router
from app.api.matches import router as match_router
from fastapi import HTTPException,Request
from fastapi.responses import JSONResponse
from app.core.nasa_data import DataUnavailable

app = FastAPI(
    title="LunaScope 3.0 API",
    description="Lunar Mission Window, 360° Horizon & Contingency Navigator Engine",
    version="3.0.0"
)

@app.exception_handler(DataUnavailable)
async def missing_data(request:Request,exc:DataUnavailable):
    return JSONResponse(status_code=503,content={'detail':str(exc),'data_mode':'nasa-official','synthetic_fallback':False})

# CORS middleware for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")
app.include_router(ws_router, prefix="/api")
app.include_router(match_router, prefix="/api")

@app.middleware('http')
async def provenance_header(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith('/api/'):
        response.headers['X-LunaScope-Data-Mode'] = 'nasa-official'
    return response


# Static files directory (built frontend)
DIST_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if DIST_DIR.exists() and (DIST_DIR / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api/"):
            raise HTTPException(404, "Unknown API endpoint")
        file_path = (DIST_DIR / full_path).resolve()
        if not file_path.is_relative_to(DIST_DIR.resolve()):
            raise HTTPException(404, "Not found")
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(DIST_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
