"""
Tests for the GalaxyCatelog API endpoints.
Uses FastAPI's TestClient against the live database (glade_api).
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, follow_redirects=True)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# GET /galaxies  (list)
# ---------------------------------------------------------------------------

def test_list_default_limit():
    r = client.get("/galaxies/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 100          # default limit


def test_list_custom_limit():
    r = client.get("/galaxies/?limit=5")
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_list_offset_advances():
    page1 = client.get("/galaxies/?limit=3&offset=0").json()
    page2 = client.get("/galaxies/?limit=3&offset=3").json()
    ids1 = [g["id"] for g in page1]
    ids2 = [g["id"] for g in page2]
    assert ids1 != ids2
    assert not set(ids1) & set(ids2)  # no overlap


def test_list_limit_too_large_rejected():
    r = client.get("/galaxies/?limit=9999")
    assert r.status_code == 422


def test_list_negative_offset_rejected():
    r = client.get("/galaxies/?offset=-1")
    assert r.status_code == 422


def test_list_item_schema():
    r = client.get("/galaxies/?limit=1")
    g = r.json()[0]
    assert "id" in g
    assert "ra" in g
    assert "dec" in g
    assert "redshift_helio" in g
    assert "luminosity_distance" in g
    # sky_position geometry column must NOT leak into the response
    assert "sky_position" not in g


# ---------------------------------------------------------------------------
# GET /galaxies/{id}
# ---------------------------------------------------------------------------

def _get_first_id() -> int:
    return client.get("/galaxies/?limit=1").json()[0]["id"]


def test_get_by_id():
    gid = _get_first_id()
    r = client.get(f"/galaxies/{gid}")
    assert r.status_code == 200
    assert r.json()["id"] == gid


def test_get_by_id_not_found():
    r = client.get("/galaxies/999999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Galaxy not found"


def test_get_by_id_invalid_type():
    r = client.get("/galaxies/not-an-int")
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /galaxies/search
# ---------------------------------------------------------------------------

def test_search_no_filters():
    r = client.get("/galaxies/search")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_search_redshift_range():
    zmin, zmax = 0.01, 0.05
    r = client.get(f"/galaxies/search?redshift_min={zmin}&redshift_max={zmax}&limit=50")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    for g in data:
        if g["redshift_helio"] is not None:
            assert zmin <= g["redshift_helio"] <= zmax


def test_search_dist_range():
    dmin, dmax = 50.0, 200.0
    r = client.get(f"/galaxies/search?dist_min={dmin}&dist_max={dmax}&limit=50")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    for g in data:
        if g["luminosity_distance"] is not None:
            assert dmin <= g["luminosity_distance"] <= dmax


def test_search_combined_filters():
    r = client.get("/galaxies/search?redshift_min=0.02&redshift_max=0.03&dist_min=80&dist_max=150&limit=20")
    assert r.status_code == 200
    data = r.json()
    for g in data:
        if g["redshift_helio"] is not None:
            assert 0.02 <= g["redshift_helio"] <= 0.03
        if g["luminosity_distance"] is not None:
            assert 80 <= g["luminosity_distance"] <= 150


def test_search_empty_result():
    # Impossible redshift range → empty list, not an error
    r = client.get("/galaxies/search?redshift_min=999&redshift_max=1000")
    assert r.status_code == 200
    assert r.json() == []


def test_search_pagination():
    page1 = client.get("/galaxies/search?redshift_min=0.01&redshift_max=0.1&limit=10&offset=0").json()
    page2 = client.get("/galaxies/search?redshift_min=0.01&redshift_max=0.1&limit=10&offset=10").json()
    ids1 = {g["id"] for g in page1}
    ids2 = {g["id"] for g in page2}
    assert not ids1 & ids2


# ---------------------------------------------------------------------------
# GET /galaxies/cone_search
# ---------------------------------------------------------------------------

def test_cone_search_basic():
    r = client.get("/galaxies/cone_search?ra=182&dec=12&radius=2")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0


def test_cone_search_results_within_radius():
    """All returned galaxies must be within the search radius (approx check)."""
    ra, dec, radius = 183.0, 13.0, 3.0
    r = client.get(f"/galaxies/cone_search?ra={ra}&dec={dec}&radius={radius}&limit=50")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    for g in data:
        if g["ra"] is not None and g["dec"] is not None:
            delta_ra = abs(g["ra"] - ra)
            delta_dec = abs(g["dec"] - dec)
            # loose bounding-box check: angular sep can't exceed radius in either axis
            assert delta_ra <= radius + 1.0
            assert delta_dec <= radius + 1.0


def test_cone_search_small_radius_fewer_results():
    large = client.get("/galaxies/cone_search?ra=182&dec=12&radius=5&limit=1000").json()
    small = client.get("/galaxies/cone_search?ra=182&dec=12&radius=0.5&limit=1000").json()
    assert len(large) >= len(small)


def test_cone_search_empty_sky_region():
    # Galactic pole region — very sparse in GLADE+
    r = client.get("/galaxies/cone_search?ra=192.85&dec=27.13&radius=0.01")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_cone_search_missing_params():
    r = client.get("/galaxies/cone_search?ra=180&dec=0")  # radius missing
    assert r.status_code == 422


def test_cone_search_invalid_ra():
    r = client.get("/galaxies/cone_search?ra=400&dec=0&radius=1")
    assert r.status_code == 422


def test_cone_search_invalid_dec():
    r = client.get("/galaxies/cone_search?ra=180&dec=95&radius=1")
    assert r.status_code == 422


def test_cone_search_negative_radius():
    r = client.get("/galaxies/cone_search?ra=180&dec=0&radius=-1")
    assert r.status_code == 422


def test_cone_search_zero_radius():
    r = client.get("/galaxies/cone_search?ra=180&dec=0&radius=0")
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /galaxies/search  — input validation
# ---------------------------------------------------------------------------

def test_search_negative_redshift_rejected():
    r = client.get("/galaxies/search?redshift_min=-0.1")
    assert r.status_code == 422


def test_search_negative_dist_rejected():
    r = client.get("/galaxies/search?dist_min=-50")
    assert r.status_code == 422


def test_search_zero_dist_rejected():
    r = client.get("/galaxies/search?dist_max=0")
    assert r.status_code == 422


def test_cone_search_pagination():
    page1 = client.get("/galaxies/cone_search?ra=182&dec=12&radius=10&limit=5&offset=0").json()
    page2 = client.get("/galaxies/cone_search?ra=182&dec=12&radius=10&limit=5&offset=5").json()
    ids1 = {g["id"] for g in page1}
    ids2 = {g["id"] for g in page2}
    assert not ids1 & ids2
