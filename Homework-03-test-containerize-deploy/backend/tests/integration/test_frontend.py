"""B. The backend serves the built frontend on the same origin — behavior that
only exists in the real image (the unit suite never builds or serves the SPA)."""

import re

import pytest

pytestmark = pytest.mark.integration


def test_root_serves_the_spa(api):
    response = api.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert '<div id="root">' in response.text


def test_client_side_route_falls_back_to_index(api):
    # /status is a client-side (React Router) route, not a file — the SPA
    # fallback must hand back index.html so a deep link / refresh works.
    response = api.get("/status")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert '<div id="root">' in response.text


def test_hashed_js_asset_is_served(api):
    # Discover the hashed bundle from index.html rather than hard-coding it, so
    # the test survives a rebuild that changes the hash.
    index = api.get("/").text
    match = re.search(r'src="(/assets/[^"]+\.js)"', index)
    assert match, "no hashed JS asset referenced in index.html"

    asset = api.get(match.group(1))
    assert asset.status_code == 200
    assert "javascript" in asset.headers["content-type"]


def test_unknown_api_path_returns_json_404_not_index(api):
    # Unmatched /api/* must stay a real JSON 404 — the SPA fallback must not
    # swallow it and return index.html.
    response = api.get("/api/does-not-exist")
    assert response.status_code == 404
    assert "application/json" in response.headers["content-type"]
    assert "detail" in response.json()
