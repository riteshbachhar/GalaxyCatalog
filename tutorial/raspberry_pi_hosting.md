# GalaxyCatalog — Raspberry Pi Deployment Runbook

Complete sequence for hosting GalaxyCatalog on the Pi, published through an
existing Cloudflare Tunnel.

Everything runs in containers. No PostgreSQL client or Python environment is
installed on the host.

---

## 0. Prerequisites

- Docker installed on the Pi
- `cloudflared` already running as a systemd service, with a local config at
  `/etc/cloudflared/config.yml`
- Repository cloned on the Pi
- `glade_sample.csv` present in the repo root (see main README for the VizieR
  download command)

---

## 1. Secrets

Create a `.env` in the repo root. It is git-ignored and never committed.

Generate both values with:

```bash
openssl rand -hex 24
```

**Use hex, not base64.** Characters like `$`, `` ` ``, and `&` are expanded or
interpreted when `.env` is sourced — a `$` mid-password silently truncates the
value to an empty string, which surfaces much later as `fe_sendauth: no
password supplied` and looks like a database fault rather than a shell quoting
one. `@` and `/` break connection-string parsing for the same reason. Hex is
alphanumeric and safe in every context here.

```bash
cd ~/projects/GalaxyCatalog

cat > .env <<'EOF'
POSTGRES_PASSWORD='paste-generated-value-here'
GALAXY_RO_PASSWORD='paste-generated-value-here'
EOF

chmod 600 .env
```

Quote the values even when using hex — it costs nothing and survives a later
change of generator.

Confirm git will not pick it up:

```bash
grep -q '^\.env$' .gitignore || echo '.env' >> .gitignore
git status --short          # .env must not appear
```

Load into the current shell, and verify both are non-empty:

```bash
source .env
echo "$POSTGRES_PASSWORD"
echo "$GALAXY_RO_PASSWORD"
```

An empty echo here means a quoting problem — fix it now rather than debugging
an auth failure three steps later.

> `source` affects only the shell it runs in. Every new terminal needs it
> again before any command below.

> Passwords passed via `-e` are visible in `docker inspect` and the process
> list. Acceptable for a single-user deployment; a production system would use
> Docker secrets or a secrets manager.

---

## 2. Network and images

```bash
docker network create galaxynet

docker build -t galaxy-db docker/postgres     # postgres:16 + Q3C, compiles C
docker build -t galaxy-api .                  # multi-stage, non-root
```

The Q3C build takes several minutes on the Pi.

```bash
docker images | grep galaxy
```

---

## 3. Start the database

No published port — reachable only from `galaxynet`.

```bash
docker run -d --name db --network galaxynet --restart unless-stopped \
  -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  -e POSTGRES_DB=glade_sample \
  galaxy-db
```

`POSTGRES_PASSWORD` is read only on first initialisation. Changing it later
takes `ALTER USER`, not a restart:

```bash
docker exec db psql -U postgres -c "ALTER USER postgres PASSWORD '$POSTGRES_PASSWORD';"
```

Verify:

```bash
docker exec db psql -U postgres -d glade_sample -c "SELECT 1;"
```

---

## 4. Schema

```bash
docker exec -i db psql -U postgres -d glade_sample < schema.sql
```

Line 1 creates the Q3C extension; the final lines build and cluster the spatial
index. Verify all three:

```bash
docker exec db psql -U postgres -d glade_sample -c "\dx"   # q3c
docker exec db psql -U postgres -d glade_sample -c "\dt"   # galaxies
docker exec db psql -U postgres -d glade_sample -c "\di"   # idx_galaxies_q3c
```

---

## 5. Load the catalogue

Run the loader inside the API image, which already has the Python
dependencies. The CSV is mounted read-only from the host. This step uses the
superuser, since it needs INSERT.

```bash
docker run --rm --network galaxynet \
  -v "$(pwd)/glade_sample.csv:/app/glade_sample.csv:ro" \
  -e DATABASE_URL="postgresql://postgres:$POSTGRES_PASSWORD@db:5432/glade_sample" \
  galaxy-api python load_data.py
```

```bash
docker exec db psql -U postgres -d glade_sample -c "SELECT count(*) FROM galaxies;"
```

---

## 6. Read-only role

The API only ever reads. Give it a role that can only read.

```bash
docker exec -i db psql -U postgres -d glade_sample <<EOF
CREATE ROLE galaxy_ro WITH LOGIN PASSWORD '$GALAXY_RO_PASSWORD';
GRANT CONNECT ON DATABASE glade_sample TO galaxy_ro;
GRANT USAGE ON SCHEMA public TO galaxy_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO galaxy_ro;
EOF
```

Note the **unquoted** `EOF` here — the variable must expand. Elsewhere in this
file heredocs are quoted to prevent expansion.

To change it later:

```bash
docker exec db psql -U postgres -d glade_sample \
  -c "ALTER ROLE galaxy_ro PASSWORD '$GALAXY_RO_PASSWORD';"
```

Verify the restriction holds. **This must fail:**

```bash
docker exec db psql -U galaxy_ro -d glade_sample -c "DELETE FROM galaxies;"
```

---

## 7. Start the API

```bash
docker run -d --name api --network galaxynet -p 8001:8000 --restart unless-stopped \
  -e DATABASE_URL="postgresql://galaxy_ro:$GALAXY_RO_PASSWORD@db:5432/glade_sample" \
  galaxy-api
```

Confirm the password actually landed — an empty one here is the single most
likely failure:

```bash
docker exec api env | grep DATABASE
```

Then verify on the Pi before exposing it:

```bash
docker ps
curl -s localhost:8001/health
curl -s "localhost:8001/galaxies/?limit=5"
curl -s "localhost:8001/galaxies/cone_search?ra=180&dec=0&radius=5&limit=5"
```

The cone search is the only endpoint that exercises Q3C. If it returns rows,
every layer is working.

---

## 8. Cloudflare Tunnel

Reuse the existing tunnel — one tunnel serves many hostnames. Back up first:

```bash
sudo cp /etc/cloudflared/config.yml /etc/cloudflared/config.yml.bak
sudo nano /etc/cloudflared/config.yml
```

Add an entry for the API hostname above the catch-all, leaving the existing
`tunnel:` and `credentials-file:` lines untouched:

```yaml
ingress:
  - hostname: <existing site hostname>
    service: http://localhost:80
  - hostname: <api hostname>
    service: http://localhost:8001
  - service: http_status:404
```

Ingress rules are first-match-wins; `http_status:404` must remain last.

```bash
cloudflared tunnel ingress validate
cloudflared tunnel route dns <tunnel-name> <api hostname>
sudo systemctl restart cloudflared
systemctl status cloudflared --no-pager | head -5
```

Test from another machine — DNS may take a minute:

```bash
curl -s https://<api hostname>/health
curl -s "https://<api hostname>/galaxies/?limit=5"
```

---

## 9. Verify restart behaviour

```bash
docker inspect --format '{{.Name}} {{.HostConfig.RestartPolicy.Name}}' db api
sudo reboot
```

After a minute, from another machine:

```bash
curl -s https://<api hostname>/health
```

The first request or two after boot may error — the API starts alongside
Postgres rather than after it, and connects lazily per request.

---

## Before publicising the URL

- [x] **Bound the cone-search radius.** Done — `radius` now carries `le=10.0`
      in `app/routers/galaxies.py`, so `radius=180` is rejected with 422
      instead of scanning the whole table.
- [ ] **Rate limiting** at the Cloudflare edge — free tier covers it, and it
      belongs there rather than in the application.

---

## Known gaps

- **No data persistence.** The database lives in the `db` container's writable
  layer. A reboot is fine; `docker rm db` destroys it. Fix with a named volume.
- **Manual sequence.** Steps 2–3 and 7 should be one `docker compose up`.
  Compose also handles the volume, a healthcheck, and startup ordering, and
  reads `.env` automatically.
- **`/health` does not check the database.** It reports liveness, not
  readiness — it returns OK even when Postgres is unreachable.

---

## Operations

```bash
docker ps
docker logs api --tail 50
docker exec -it db psql -U postgres -d glade_sample
```

### Redeploying after a code change

The database is untouched; only the API image is rebuilt.

```bash
cd ~/projects/GalaxyCatalog
git pull
source .env                                   # required in every new shell

docker build -t galaxy-api .
docker rm -f api
docker run -d --name api --network galaxynet -p 8001:8000 --restart unless-stopped \
  -e DATABASE_URL="postgresql://galaxy_ro:$GALAXY_RO_PASSWORD@db:5432/glade_sample" \
  galaxy-api

docker logs api --tail 20
curl -s localhost:8001/health
```

Builds are fast for source-only changes — the dependency layer stays cached
because `requirements.txt` is copied before the source. Expect a few seconds of
downtime between `rm -f` and `run`.

Forgetting `source .env` is the most common redeploy failure: the password
expands to an empty string and the first query fails with `fe_sendauth: no
password supplied`.

### Teardown

Destroys the data:

```bash
docker rm -f api db && docker network rm galaxynet
```
