import os


os.environ["MOCK_AI"] = "true"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DATABASE_URL"] = (
    "sqlite:///./test_pocketsmart.db"
)


from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


Base.metadata.create_all(
    bind=engine
)


client = TestClient(app)


def authenticate():
    email = "tester@example.com"
    password = "password123"

    client.post(
        "/register",
        json={
            "name": "Tester",
            "email": email,
            "password": password,
        },
    )

    response = client.post(
        "/token",
        json={
            "email": email,
            "password": password,
        },
    )

    return {
        "Authorization":
            "Bearer "
            + response.json()["access_token"]
    }


def test_health():
    response = client.get("/health")

    assert response.status_code == 200


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert "PocketSmart AI" in response.text


def test_planners():
    headers = authenticate()


    response = client.post(
        "/api/generate-home",
        json={
            "budget": 50000,
            "room_type": "Living Room",
            "style": "Modern",
            "items": [
                {
                    "category": "Fan",
                    "quantity": 2,
                }
            ],
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert (
        "HOME INTERIOR"
        in response.json()["response"]
    )


    response = client.post(
        "/api/generate-party",
        json={
            "budget": 30000,
            "guests": 30,
            "event_type": "Birthday",
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert (
        "PARTY PLAN"
        in response.json()["response"]
    )


    response = client.post(
        "/api/generate-jewelry",
        data={
            "budget": 10000,
            "occasion": "Wedding",
            "style": "Elegant",
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert (
        "JEWELRY PLAN"
        in response.json()["response"]
    )