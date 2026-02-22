from fastapi import FastAPI
from app.routers import galaxies

app = FastAPI(title="GalaxyCatelog API")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(galaxies.router, prefix="/galaxies")
