from sqlalchemy import Column, Integer, String, Float, DateTime, func
from geoalchemy2 import Geometry
from app.database import Base


class Galaxy(Base):
    __tablename__ = "galaxies"

    id = Column(Integer, primary_key=True)
    glade_id = Column(Integer)
    pgc = Column(Integer)
    gwgc = Column(String(28))
    hyperleda = Column(String(29))
    twomass = Column(String(16))
    wisexscos = Column(String(19))
    sdss_dr16q = Column(String(18))
    object_type = Column(String(1))
    ra = Column(Float)
    dec = Column(Float)
    redshift_helio = Column(Float)
    redshift_cmb = Column(Float)
    luminosity_distance = Column(Float)
    e_luminosity_distance = Column(Float)
    apparent_mag_b = Column(Float)
    apparent_mag_k = Column(Float)
    stellar_mass = Column(Float)
    log_bns_rate = Column(Float)
    sky_position = Column(Geometry("POINT", srid=4326))
    created_at = Column(DateTime, server_default=func.now())
