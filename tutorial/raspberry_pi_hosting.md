# GalaxyCatalog on the Raspberry Pi

Deployment notes for the `RiPy` host. Written 2026-08-24.

## Why the Pi

Always-on, low power, and already on the LAN. The catalogue is ~100k rows and
the query load is one person, so the Pi is comfortably sufficient.

## Architecture

Two containers on a user-defined bridge network (`galaxynet`):

- **`db`** — `galaxy-db`, built from `postgres:16` with the Q3C spatial
  extension compiled in. Publishes no host port; only reachable from inside the
  network.
- **`api`** — `galaxy-api`, the FastAPI service. Publishes `8000:8000`.

The API reaches the database at `db:5432` via Docker's embedded DNS. Nothing on
the host talks to Postgres directly.

## Architecture note (aarch64)

The Pi is ARM64, as is the development Mac (Apple Silicon), so images built in
either place run in the other without emulation. Every dependency in
`requirements.txt` ships an `aarch64` wheel, so no compiler is needed in the
API image. The one exception is Q3C, which is C source and must be compiled —
that is what `docker/postgres/Dockerfile` does. Building it on the Pi takes
noticeably longer than on the Mac.

## Setup

Full command sequence is in the main README under "Running with Docker". In
brief: create the network, build both images, start `db`, pipe `schema.sql`
into it via `docker exec -i`, load the CSV using the API image
(`docker run --rm ... galaxy-api python load_data.py`), then start `api`.

Nothing is installed on the host except Docker. No PostgreSQL client, no
Python environment — deliberately, since the whole point was to stop depending
on hand-installed local state.

## Things that bit us

- **Host port 8000 was already in use** on first attempt. Check with
  `sudo ss -tlnp | grep :8000` before starting the API; remap the left-hand
  side (`-p 8001:8000`) if something else owns it.
- **The host's `psql` is not the container's `psql`.** Running `psql ... <
  schema.sql` without the `docker exec -i db` prefix produces a confusing Unix
  socket error that looks like the container is broken. It isn't.
- **`/docker-entrypoint-initdb.d/` only runs on first boot.** If the data
  directory already exists, the entrypoint logs `ignoring
  /docker-entrypoint-initdb.d/*` and skips it. Recreate the container if you
  need init scripts to fire.
- **Q3C is a hard dependency of the schema**, not an optional index. Line 1 of
  `schema.sql` is `CREATE EXTENSION IF NOT EXISTS q3c;` and lines 49–50 build
  and cluster on `q3c_ang2ipix`. Stock `postgres:16` will fail all three.

## Known gaps

- **No persistence.** The database lives in the `db` container's writable
  layer, so `docker rm db` destroys it. Needs a named volume.
- **No restart policy.** Containers do not come back after a reboot. Add
  `--restart unless-stopped`, or move to Compose.
- **Password is `pw`.** Fine on a LAN-only service; not fine if this is ever
  exposed.
- **Manual sequence.** Five commands that should be one `docker compose up`.

## Next step

Replace the whole sequence with a `docker-compose.yml`: named volume for
`pgdata`, healthcheck on the database, `depends_on: condition:
service_healthy` for the API, and a restart policy on both.
