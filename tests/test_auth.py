import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.test_links import client, setup_db, override_get_db

# We reuse the client and setup_db from test_links
# However, we must ensure imports are available. We'll explicitly import the fixtures.


def test_register_user(setup_db):
    response = client.post(
        "/auth/register", json={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 201
    assert response.json() == {"username": "testuser"}


def test_register_duplicate_user(setup_db):
    client.post(
        "/auth/register", json={"username": "testuser", "password": "password123"}
    )
    response = client.post(
        "/auth/register", json={"username": "testuser", "password": "newpassword"}
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Username already registered"


def test_login_user(setup_db):
    client.post(
        "/auth/register", json={"username": "testuser", "password": "password123"}
    )
    response = client.post(
        "/auth/login", json={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(setup_db):
    client.post(
        "/auth/register", json={"username": "testuser", "password": "password123"}
    )
    response = client.post(
        "/auth/login", json={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_login_wrong_username(setup_db):
    response = client.post(
        "/auth/login", json={"username": "unknownuser", "password": "password123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
