# GalaxyCatelog

A REST API for querying galaxy catalogue data, built on the [GLADE+](https://glade.elte.hu/) public catalogue. Supports astronomical queries including redshift/distance filtering and cone searches — the same query types used in gravitational wave follow-up pipelines like [UpGLADE](https://upglade.elte.hu/).

## Tech Stack

- **FastAPI** — REST API framework with auto-generated `/docs`
- **PostgreSQL + PostGIS** — spatial database for cone search queries
- **SQLAlchemy 2.0** — ORM and query building
- **Python 3.10+**

## Local Setup

### 1. Prerequisites

- PostgreSQL 12+ with PostGIS extension
- Python 3.10+

### 2. Create the database

```bash
psql -U postgres -c "CREATE DATABASE glade_api;"
psql -U postgres -d glade_api -c "CREATE EXTENSION postgis;"
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get the data

Download the GLADE+ catalogue from [VizieR](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=VII/281) and place the exported CSV in the project root as `glade_sample.csv`.

### 5. Create the schema and load data

```bash
psql -U postgres -d glade_api -f schema.sql
python load_data.py
```

### 6. Run the API

```bash
uvicorn app.main:app --reload
```

API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## API Reference

### `GET /health`
Health check.

```bash
curl http://localhost:8000/health
```

---

### `GET /galaxies`
List galaxies with pagination.

| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 20 | Results per page |
| `offset` | int | 0 | Pagination offset |

```bash
curl "http://localhost:8000/galaxies?limit=20&offset=0"
```

---

### `GET /galaxies/{id}`
Get a single galaxy by its database ID.

```bash
curl http://localhost:8000/galaxies/42
```

---

### `GET /galaxies/search`
Filter galaxies by redshift and/or luminosity distance range.

| Param | Type | Description |
|---|---|---|
| `redshift_min` | float | Minimum redshift |
| `redshift_max` | float | Maximum redshift |
| `dist_min` | float | Minimum luminosity distance (Mpc) |
| `dist_max` | float | Maximum luminosity distance (Mpc) |
| `limit` | int | Results per page (default 20) |
| `offset` | int | Pagination offset (default 0) |

```bash
# Galaxies in redshift range typical for LIGO O3 BNS events
curl "http://localhost:8000/galaxies/search?redshift_min=0.01&redshift_max=0.05"
```

---

### `GET /galaxies/cone_search`
Find galaxies within a given angular radius of a sky position. Requires PostGIS.

| Param | Type | Description |
|---|---|---|
| `ra` | float | Right Ascension in degrees (0–360) |
| `dec` | float | Declination in degrees (−90–90) |
| `radius` | float | Search radius in degrees |
| `limit` | int | Results per page (default 20) |
| `offset` | int | Pagination offset (default 0) |

```bash
# Galaxies within 2 degrees of (RA=180, Dec=-30)
curl "http://localhost:8000/galaxies/cone_search?ra=180&dec=-30&radius=2"
```

---

## Data

Galaxy data is sourced from the **GLADE+ v7.5.4** catalogue (Dálya et al. 2022), which aggregates data from SDSS, 2MASS, HyperLEDA, and other surveys. The catalogue is designed for identifying electromagnetic counterparts to gravitational wave events.

### Identifiers

| DB Column | Source Column | Description |
|---|---|---|
| `glade_id` | `GLADE+` | GLADE+ catalogue number |
| `pgc` | `PGC` | Principal Galaxies Catalogue number |
| `gwgc` | `GWGC` | Name in the GWGC catalogue |
| `hyperleda` | `HyperLEDA` | Name in the HyperLEDA catalogue |
| `twomass` | `2MASS` | Name in the 2MASS XSC catalogue |
| `wisexscos` | `WISExSCOS` | Name in the WISExSuperCOSMOS catalogue |
| `sdss_dr16q` | `SDSS-DR16Q` | Name in the SDSS-DR16Q catalogue |
| `object_type` | `Type` | `G` = galaxy, `Q` = quasar |

### Sky Coordinates

| DB Column | Source Column | Unit | Description |
|---|---|---|---|
| `ra` | `RAJ2000` | degrees | Right Ascension (J2000, 0–360) |
| `dec` | `DEJ2000` | degrees | Declination (J2000, −90–90) |

### Redshift

| DB Column | Source Column | Description |
|---|---|---|
| `redshift_helio` | `zhelio` | Redshift in the heliocentric frame |
| `redshift_cmb` | `zcmb` | Redshift converted to the CMB frame |

### Distance

| DB Column | Source Column | Unit | Description |
|---|---|---|---|
| `luminosity_distance` | `dL` | Mpc | Luminosity distance |
| `e_luminosity_distance` | `e_dL` | Mpc | 1-sigma error of luminosity distance |

### Photometry

| DB Column | Source Column | Unit | Description |
|---|---|---|---|
| `apparent_mag_b` | `Bmag` | mag | Apparent B-band magnitude |
| `apparent_mag_k` | `Kmag` | mag | Apparent K-band magnitude |

### Physical Properties

| DB Column | Source Column | Unit | Description |
|---|---|---|---|
| `stellar_mass` | `M*` | 10¹⁰ M☉ | Stellar mass |
| `log_bns_rate` | `logRate` | log(Gyr⁻¹) | log₁₀ of estimated BNS merger rate |

> Many fields are optional — missing values in the source catalogue are stored as `NULL`.
