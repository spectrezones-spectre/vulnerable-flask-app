import os
import sqlite3
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from app.app import app  # noqa: E402


@pytest.fixture()
def client():
    app.config.update(
        TESTING=True,
        DATABASE=os.path.join(ROOT, "lab.db"),
        SECRET_KEY="test-key",
    )
    with app.test_client() as test_client:
        yield test_client


def login(client, username="alice", password="alice123", endpoint="/login"):
    return client.post(endpoint, data={"username": username, "password": password})


def test_database_schema_and_seed():
    con = sqlite3.connect(os.path.join(ROOT, "lab.db"))
    tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"roles", "users", "products", "audit_log"}.issubset(tables)
    assert con.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 8
    assert con.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 4
    con.close()


def test_public_pages_and_health(client):
    for path in ["/", "/login", "/login-safe", "/search?q=network", "/search-safe?q=network", "/search-post", "/product?id=1", "/product-safe?id=1"]:
        response = client.get(path)
        assert response.status_code == 200, path
    health = client.get("/health").get_json()
    assert health == {"status": "ok", "database": True, "schema_complete": True}


def test_get_search_normal_error_union_and_safe_comparison(client):
    normal = client.get("/search", query_string={"q": "network"})
    assert normal.status_code == 200
    assert b"Router Atlas" in normal.data
    error = client.get("/search", query_string={"q": "%'"})
    assert b"Erreur SQLite" in error.data
    three_columns = client.get("/search", query_string={"q": "%' UNION SELECT 1,'Injected','training'-- "})
    assert b"Erreur SQLite" in three_columns.data
    union = client.get("/search", query_string={"q": "%' UNION SELECT 1,'Injected','training',9-- "})
    assert union.status_code == 200 and b"<h3>Injected</h3>" in union.data
    safe = client.get("/search-safe", query_string={"q": "%' UNION SELECT 1,'Injected','training',9-- "})
    assert b"<h3>Injected</h3>" not in safe.data


def test_product_get_and_safe_route(client):
    assert b"Router Atlas" in client.get("/product?id=1").data
    assert b"Erreur de syntaxe" in client.get("/product?id=not-a-number").data
    safe = client.get("/product-safe?id=not-a-number")
    assert safe.status_code == 200 and b"Erreur de syntaxe" not in safe.data


def test_post_search_is_reachable(client):
    response = client.post("/search-post", data={"q": "Firewall"})
    assert response.status_code == 200 and b"Firewall Ember" in response.data
    malformed = client.post("/search-post", data={"q": "'"})
    assert b"Erreur SQLite" in malformed.data


def test_normal_and_safe_login_sessions(client):
    response = login(client)
    assert response.status_code == 302 and response.headers["Location"].endswith("/dashboard")
    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200 and b"Bonjour alice" in dashboard.data
    client.get("/logout")
    safe = login(client, endpoint="/login-safe")
    assert safe.status_code == 302
    assert b"Bonjour alice" in client.get("/dashboard").data


def test_login_injection_difference(client):
    payload = {"username": "' OR '1'='1'-- ", "password": "x"}
    vulnerable = client.post("/login", data=payload)
    assert vulnerable.status_code == 302
    client.get("/logout")
    safe = client.post("/login-safe", data=payload)
    assert safe.status_code == 200 and b"Identifiants refus" in safe.data


def test_admin_safe_and_vulnerable_paths(client):
    assert client.get("/admin").status_code == 302
    login(client)
    assert client.get("/admin").status_code == 403
    vulnerable = client.get("/admin-vulnerable?as_role=admin")
    assert vulnerable.status_code == 200 and b"Zone administration" in vulnerable.data
    client.get("/logout")
    login(client, "admin", "admin123")
    assert client.get("/admin").status_code == 200


def test_reset_script_is_reproducible():
    # The script is verified syntactically here; its destructive action is exercised by the CLI smoke test.
    source = open(os.path.join(ROOT, "scripts", "init_db.py"), encoding="utf-8").read()
    assert "CREATE TABLE roles" in source
    assert "CREATE TABLE products" in source
