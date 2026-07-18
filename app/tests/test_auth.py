def test_signup_creates_user(client):
    response = client.post(
        "api/v1/auth/signup",
        json={"name": "Rukky", "email": "rukky@example.com", "password": "testpass123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "rukky@example.com"
    assert data["role"] == "organizer"
    assert "hashed_password" not in data  # make sure we never leak this


def test_signup_rejects_duplicate_email(client):
    client.post(
        "/api/v1/auth/signup",
        json={"name": "Rukky", "email": "rukky@example.com", "password": "testpass123"},
    )
    response = client.post(
        "/api/v1/auth/signup",
        json={"name": "Someone Else", "email": "rukky@example.com", "password": "different"},
    )
    assert response.status_code == 400

def test_login_returns_token(client):
    client.post(
        "/api/v1/auth/signup",
        json={"name": "Rukky", "email": "rukky@example.com", "password": "testpass123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "rukky@example.com", "password": "testpass123"},  # note: form data, not json
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_rejects_wrong_password(client):
    client.post(
        "/api/v1/auth/signup",
        json={"name": "Rukky", "email": "rukky@example.com", "password": "testpass123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "rukky@example.com", "password": "wrongpassword"},
    )