"""
Enhanced FastAPI app with full OSCFacade integration.

This combines the original SML endpoints with new facade endpoints.
Use this as a reference or replace the existing app.py.

To run:
    uvicorn src.api.app_with_facade:app --reload --port 8000

Requirements:
    - OPENAI_API_KEY environment variable (for NL generation)
    - DATABASE_URL environment variable
    - SoundFont file for playback (optional)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the original endpoints
from src.api.app import router as original_router

# Import the new facade endpoints
from src.api.facade_endpoints import router as facade_router


# Create FastAPI app
app = FastAPI(
    title="OSC API with Facade",
    version="0.2.0",
    description="Complete API for OSC operations including NL generation, SML/DSL conversion, and playback"
)

# Add CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include original endpoints (backward compatible)
# These are at the root level: /clips/from-sml, /compositions, etc.
app.include_router(original_router)

# Include new facade endpoints
# These are under /facade: /facade/nl/clip-to-sml, /facade/clips/search, etc.
app.include_router(facade_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "OSC API with Facade Integration",
        "version": "0.2.0",
        "endpoints": {
            "original": {
                "clips": "/clips/from-sml, /clips/by-name, /clips/by-tag",
                "compositions": "/compositions, /compositions/from-sml, /compositions/{id}"
            },
            "facade": {
                "natural_language": "/facade/nl/clip-to-sml, /facade/nl/clip-to-db",
                "conversion": "/facade/sml/clip-to-dsl, /facade/sml/composition-to-dsl",
                "database": "/facade/dsl/load",
                "search": "/facade/clips/search",
                "export": "/facade/clips/{id}/dsl, /facade/compositions/{id}/dsl",
                "midi": "/facade/compositions/{id}/midi",
                "playback": "/facade/playback/sml, /facade/playback/nl, /facade/playback/clip/{id}"
            }
        },
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
