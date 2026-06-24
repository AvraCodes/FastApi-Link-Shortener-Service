import csv
import io
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import get_db
from app.main import app
from app.models import Base
from app.shortcode import ALPHABET, generate_short_code

TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


@pytest.fixture
def auth_headers(setup_db):
    client.post("/auth/register", json={"username": "user1", "password": "pw"})
    resp = client.post("/auth/login", json={"username": "user1", "password": "pw"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_2(setup_db):
    client.post("/auth/register", json={"username": "user2", "password": "pw"})
    resp = client.post("/auth/login", json={"username": "user2", "password": "pw"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Short code unit tests ---

def test_short_code_default_length():
    code = generate_short_code()
    assert len(code) == 7


def test_short_code_custom_length():
    for length in (6, 7, 8):
        code = generate_short_code(length=length)
        assert len(code) == length


def test_short_code_charset():
    code = generate_short_code()
    for char in code:
        assert char in ALPHABET


# --- POST /links ---

def test_create_link_no_token():
    response = client.post("/links", json={"url": "https://example.com"})
    assert response.status_code == 401


def test_create_link(auth_headers):
    response = client.post("/links", json={"url": "https://example.com"}, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert "short_code" in data
    assert data["original_url"] == "https://example.com/"
    assert "created_at" in data


def test_create_link_invalid_url(auth_headers):
    response = client.post("/links", json={"url": "not-a-url"}, headers=auth_headers)
    assert response.status_code == 422


# --- GET /{code} redirect ---

def test_redirect(auth_headers):
    create_resp = client.post("/links", json={"url": "https://example.com"}, headers=auth_headers)
    code = create_resp.json()["short_code"]

    redirect_resp = client.get(f"/{code}", follow_redirects=False)
    assert redirect_resp.status_code == 307
    assert redirect_resp.headers["location"] == "https://example.com/"


def test_redirect_increments_click_count(auth_headers):
    create_resp = client.post("/links", json={"url": "https://example.com"}, headers=auth_headers)
    code = create_resp.json()["short_code"]

    client.get(f"/{code}", follow_redirects=False)
    client.get(f"/{code}", follow_redirects=False)

    stats_resp = client.get(f"/links/{code}/stats")
    assert stats_resp.json()["click_count"] == 2


def test_redirect_not_found():
    response = client.get("/nonexistent", follow_redirects=False)
    assert response.status_code == 404
    assert response.json()["detail"] == "Short link not found"


# --- GET /links/{code}/stats ---

def test_stats_not_found():
    response = client.get("/links/nonexistent/stats")
    assert response.status_code == 404
    assert response.json()["detail"] == "Short link not found"


def test_stats_returns_click_count(auth_headers):
    create_resp = client.post("/links", json={"url": "https://example.com"}, headers=auth_headers)
    code = create_resp.json()["short_code"]

    stats_resp = client.get(f"/links/{code}/stats")
    assert stats_resp.status_code == 200
    data = stats_resp.json()
    assert data["click_count"] == 0
    assert data["short_code"] == code


# --- GET /links (paginated list & isolation) ---

def test_list_links_empty(auth_headers):
    response = client.get("/links", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_links_pagination(auth_headers):
    for i in range(5):
        client.post("/links", json={"url": f"https://example.com/{i}"}, headers=auth_headers)

    response = client.get("/links?limit=2&offset=0", headers=auth_headers)
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5

    response = client.get("/links?limit=2&offset=4", headers=auth_headers)
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 5


def test_list_links_isolation(auth_headers, auth_headers_2):
    # User 1 creates a link
    client.post("/links", json={"url": "https://user1.com"}, headers=auth_headers)
    # User 2 creates two links
    client.post("/links", json={"url": "https://user2.com/1"}, headers=auth_headers_2)
    client.post("/links", json={"url": "https://user2.com/2"}, headers=auth_headers_2)

    # User 1 should see only 1 link
    resp1 = client.get("/links", headers=auth_headers)
    assert resp1.json()["total"] == 1

    # User 2 should see only 2 links
    resp2 = client.get("/links", headers=auth_headers_2)
    assert resp2.json()["total"] == 2


def test_export_links_csv(auth_headers):
    client.post("/links", json={"url": "https://example.com/one"}, headers=auth_headers)
    client.post("/links", json={"url": "https://example.com/two"}, headers=auth_headers)

    list_resp = client.get("/links", headers=auth_headers)
    items = list_resp.json()["items"]
    assert len(items) == 2

    code_newest = items[0]["short_code"]
    client.get(f"/{code_newest}", follow_redirects=False)

    response = client.get("/links/export", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'attachment; filename="link_stats.csv"' in response.headers["content-disposition"]

    rows = list(csv.reader(io.StringIO(response.text)))

    assert len(rows) == 3
    assert rows[0] == ["Short Code", "Original URL", "Created At", "Click Count"]
    assert rows[1][0] == code_newest
    assert rows[1][1] == "https://example.com/two"
    assert rows[1][3] == "1"
    assert rows[2][0] == items[1]["short_code"]
    assert rows[2][1] == "https://example.com/one"
    assert rows[2][3] == "0"
