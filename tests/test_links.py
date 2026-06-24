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


def test_create_link():
    response = client.post("/links", json={"url": "https://example.com"})
    assert response.status_code == 201
    data = response.json()
    assert "short_code" in data
    assert data["original_url"] == "https://example.com/"
    assert "created_at" in data


def test_create_link_invalid_url():
    response = client.post("/links", json={"url": "not-a-url"})
    assert response.status_code == 422


# --- GET /{code} redirect ---


def test_redirect():
    create_resp = client.post("/links", json={"url": "https://example.com"})
    code = create_resp.json()["short_code"]

    redirect_resp = client.get(f"/{code}", follow_redirects=False)
    assert redirect_resp.status_code == 307
    assert redirect_resp.headers["location"] == "https://example.com/"


def test_redirect_increments_click_count():
    create_resp = client.post("/links", json={"url": "https://example.com"})
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


def test_stats_returns_click_count():
    create_resp = client.post("/links", json={"url": "https://example.com"})
    code = create_resp.json()["short_code"]

    stats_resp = client.get(f"/links/{code}/stats")
    assert stats_resp.status_code == 200
    data = stats_resp.json()
    assert data["click_count"] == 0
    assert data["short_code"] == code


# --- GET /links (paginated list) ---


def test_list_links_empty():
    response = client.get("/links")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_links_pagination():
    for i in range(5):
        client.post("/links", json={"url": f"https://example.com/{i}"})

    response = client.get("/links?limit=2&offset=0")
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5

    response = client.get("/links?limit=2&offset=4")
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 5


def test_export_links_csv():
    client.post("/links", json={"url": "https://example.com/one"})
    client.post("/links", json={"url": "https://example.com/two"})

    list_resp = client.get("/links")
    items = list_resp.json()["items"]
    assert len(items) == 2

    code_newest = items[0]["short_code"]
    client.get(f"/{code_newest}", follow_redirects=False)

    response = client.get("/links/export")
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

