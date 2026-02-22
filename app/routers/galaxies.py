from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID

from app.database import get_db
from app.models import Galaxy
from app.schemas import GalaxyResponse

router = APIRouter()


@router.get("/", response_model=List[GalaxyResponse])
def list_galaxies(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return db.query(Galaxy).offset(offset).limit(limit).all()


@router.get("/search", response_model=List[GalaxyResponse])
def search_galaxies(
    redshift_min: Optional[float] = Query(default=None),
    redshift_max: Optional[float] = Query(default=None),
    dist_min: Optional[float] = Query(default=None),
    dist_max: Optional[float] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Galaxy)
    if redshift_min is not None:
        q = q.filter(Galaxy.redshift_helio >= redshift_min)
    if redshift_max is not None:
        q = q.filter(Galaxy.redshift_helio <= redshift_max)
    if dist_min is not None:
        q = q.filter(Galaxy.luminosity_distance >= dist_min)
    if dist_max is not None:
        q = q.filter(Galaxy.luminosity_distance <= dist_max)
    return q.offset(offset).limit(limit).all()


@router.get("/cone_search", response_model=List[GalaxyResponse])
def cone_search(
    ra: float = Query(..., description="Right Ascension in degrees (0–360)"),
    dec: float = Query(..., description="Declination in degrees (-90–90)"),
    radius: float = Query(..., description="Search radius in degrees"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    point = ST_SetSRID(ST_MakePoint(ra, dec), 4326)
    return (
        db.query(Galaxy)
        .filter(ST_DWithin(Galaxy.sky_position, point, radius))
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{galaxy_id}", response_model=GalaxyResponse)
def get_galaxy(galaxy_id: int, db: Session = Depends(get_db)):
    galaxy = db.get(Galaxy, galaxy_id)
    if galaxy is None:
        raise HTTPException(status_code=404, detail="Galaxy not found")
    return galaxy
