# GW Galaxy Catalogue API — Project Plan

## Overview

A REST API that serves galaxy catalogue data with astronomical queries, built as a mini version of the UpGLADE infrastructure. Demonstrates database design, API development, and GW domain knowledge.

## Tech Stack

- **Language:** Python
- **API Framework:** FastAPI
- **Database:** PostgreSQL + PostGIS (spatial queries)
- **ORM:** SQLAlchemy
- **Data Source:** GLADE+ public catalogue (subset)
- **Optional:** Docker, pytest

---

## Day-by-Day Plan

### Days 1–3: Foundations

**Goal:** Get comfortable with PostgreSQL, SQL basics, and FastAPI.

- [ ] Install PostgreSQL locally
- [ ] Learn core SQL: `CREATE TABLE`, `INSERT`, `SELECT`, `JOIN`, `INDEX`
- [ ] Practice with a toy dataset (10–20 rows, manually created)
- [ ] Install FastAPI and Uvicorn
- [ ] Run the FastAPI hello world tutorial
- [ ] Understand request parameters, path parameters, and response models
- [ ] Install SQLAlchemy and connect it to your PostgreSQL instance
- [ ] Run a basic query from Python using SQLAlchemy

**Resources:**
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)
- [FastAPI Official Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [SQLAlchemy Quick Start](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)

---

### Days 4–6: Database Design & Data Ingestion

**Goal:** Design the schema and load real galaxy data.

- [ ] Download a subset of the GLADE+ catalogue ([GLADE+ data](https://glade.elte.hu/))
- [ ] Explore the data: understand columns, types, missing values
- [ ] Design the database schema:

```sql
CREATE TABLE galaxies (
    id SERIAL PRIMARY KEY,
    glade_id VARCHAR(50),
    name VARCHAR(100),
    ra DOUBLE PRECISION,          -- Right Ascension (degrees)
    dec DOUBLE PRECISION,         -- Declination (degrees)
    redshift DOUBLE PRECISION,
    luminosity_distance DOUBLE PRECISION,  -- Mpc
    apparent_mag_b DOUBLE PRECISION,
    apparent_mag_k DOUBLE PRECISION,
    source VARCHAR(50),           -- Source catalogue (e.g., SDSS, 2MASS)
    created_at TIMESTAMP DEFAULT NOW()
);
```

- [ ] Write a Python ingestion script that reads the CSV and loads it into PostgreSQL
- [ ] Handle missing values and data cleaning during ingestion
- [ ] Add indexes on `ra`, `dec`, `redshift`, `luminosity_distance`
- [ ] Verify data with basic SQL queries

---

### Days 7–9: API Development

**Goal:** Build functional API endpoints with astronomical query support.

- [ ] Install PostGIS extension for spatial queries
- [ ] Add a geometry column to the galaxies table for sky coordinates
- [ ] Build the following endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/galaxies` | GET | List galaxies with pagination |
| `/galaxies/{id}` | GET | Get a single galaxy by ID |
| `/galaxies/search` | GET | Query by redshift range, luminosity distance range |
| `/galaxies/cone_search` | GET | Cone search: galaxies within X degrees of (ra, dec) |
| `/health` | GET | Health check endpoint |

- [ ] Implement query parameters:
  - `redshift_min`, `redshift_max`
  - `dist_min`, `dist_max` (luminosity distance in Mpc)
  - `ra`, `dec`, `radius` (cone search in degrees)
  - `limit`, `offset` (pagination)
- [ ] Add Pydantic response models for clean, typed API responses
- [ ] Test endpoints manually using FastAPI's auto-generated `/docs` page

---

### Days 10–12: Polish & Documentation

**Goal:** Make it presentable and professional.

- [ ] Add input validation (e.g., ra in [0, 360], dec in [-90, 90], positive radius)
- [ ] Add meaningful error responses (400 for bad input, 404 for not found)
- [ ] Write 5–10 basic tests using `pytest` and FastAPI's test client
- [ ] Write a clear `README.md`:
  - Project description and motivation
  - How to set up and run locally
  - API endpoint documentation with example queries
  - Schema diagram or description
- [ ] Clean up code: consistent style, docstrings, type hints
- [ ] Push to GitHub with a clean commit history

---

### Days 13–14: Buffer + Cover Letter

**Goal:** Finalize everything and submit application.

- [ ] Final review of code and documentation
- [ ] Draft cover letter referencing this project
- [ ] Submit application through CNRS portal
- [ ] Send introduction email to Dr. Dálya

---

## Example API Calls

```bash
# Get all galaxies (paginated)
GET /galaxies?limit=20&offset=0

# Search by redshift range
GET /galaxies/search?redshift_min=0.01&redshift_max=0.05

# Cone search: galaxies within 2 degrees of (ra=180, dec=-30)
GET /galaxies/cone_search?ra=180&dec=-30&radius=2

# Get a specific galaxy
GET /galaxies/42
```

---

## Why This Project Matters

- **Directly relevant** to the UpGLADE role: same data (GLADE+), same type of queries, same tech decisions
- **Demonstrates initiative:** you built what they're hiring someone to build
- **Shows domain knowledge:** a backend developer wouldn't know what a cone search or redshift query is
- **Reusable:** good portfolio piece for data engineering and quant roles too

---

## Stretch Goals (if time permits)

- [ ] Dockerize the application (Dockerfile + docker-compose)
- [ ] Add a `/galaxies/stats` endpoint returning summary statistics
- [ ] Implement basic data versioning (track when records were added/updated)
- [ ] Add rate limiting to the API
- [ ] Deploy on a free tier (e.g., Render, Railway)