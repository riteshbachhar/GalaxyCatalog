from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class GalaxyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    glade_id: Optional[int] = None
    pgc: Optional[int] = None
    gwgc: Optional[str] = None
    hyperleda: Optional[str] = None
    twomass: Optional[str] = None
    wisexscos: Optional[str] = None
    sdss_dr16q: Optional[str] = None
    object_type: Optional[str] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    redshift_helio: Optional[float] = None
    redshift_cmb: Optional[float] = None
    luminosity_distance: Optional[float] = None
    e_luminosity_distance: Optional[float] = None
    apparent_mag_b: Optional[float] = None
    apparent_mag_k: Optional[float] = None
    stellar_mass: Optional[float] = None
    log_bns_rate: Optional[float] = None
    created_at: Optional[datetime] = None
