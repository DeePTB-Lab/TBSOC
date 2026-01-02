from fastapi.testclient import TestClient
from tbsoc.server.main import app
import os

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_list_files():
    response = client.get("/api/files")
    assert response.status_code == 200
    files = response.json()
    assert isinstance(files, list)

import pytest

def test_serve_frontend():
    # Verify strict static file serving for root
    # This feature depends on the frontend being built (npm run build)
    
    # Check if the static mount exists
    # app.routes contains the mounted routes. 
    # Mounts are usually starlette.routing.Mount
    is_mounted = False
    for route in app.routes:
        if getattr(route, "path", "") == "/":
             is_mounted = True
             break
    
    if not is_mounted:
        pytest.skip("Frontend build not found (frontend/dist). Skipping frontend serving test.")

    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<!doctype html>" in response.text.lower()
