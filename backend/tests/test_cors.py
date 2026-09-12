"""Regression test for a real bug found manually driving the frontend
against this backend in a browser (Phase 6): with no CORS middleware
configured, every cross-origin fetch from the React app was silently
blocked, since the browser's preflight OPTIONS request got a plain
405 instead of the expected Access-Control-* headers. Not a dev-only
concern -- Vercel (frontend) and Render (backend) are always different
origins in production too.
"""

from fastapi.testclient import TestClient

from app.main import app


def test_preflight_request_from_configured_frontend_origin_is_allowed():
    client = TestClient(app)
    response = client.options(
        "/applications",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
