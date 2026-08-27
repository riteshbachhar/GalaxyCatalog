from fastapi import FastAPI
from app.routers import galaxies

app = FastAPI(
    title="GalaxyCatalog API",
    description=(
        "REST API over the GLADE+ galaxy catalogue, with redshift, distance, "
        "and cone-search queries for gravitational wave follow-up."
    ),
)


@app.get("/")
def index():
    """Service index — what this is and where to go next."""
    return {
        "name": "GalaxyCatalog API",
        "description": "Queries over the GLADE+ galaxy catalogue.",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "endpoints": {
            "health": "/health",
            "list": "/galaxies/",
            "by_id": "/galaxies/{id}",
            "search": "/galaxies/search",
            "cone_search": "/galaxies/cone_search",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(galaxies.router, prefix="/galaxies")
