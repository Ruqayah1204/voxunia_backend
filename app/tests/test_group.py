def _signup_and_login(client, email="rukky@example.com"):
    client.post(
        "/api/v1/auth/signup",
        json={"name": "Rukky", "email": email, "password": "testpass123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_group_requires_auth(client):
    response = client.post("/api/v1/groups", json={"name": "Red Cross Ogun"})
    assert response.status_code == 401


def test_create_group_success(client):
    headers = _signup_and_login(client)
    response = client.post(
        "/api/v1/groups",
        json={"name": "Red Cross Ogun", "description": "Community meetups", "tags": ["ngo", "community"]},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Red Cross Ogun"
    assert data["slug"] == "red-cross-ogun"
    assert data["tags"] == ["ngo", "community"]


def test_create_group_generates_unique_slug_on_duplicate_name(client):
    headers = _signup_and_login(client)
    first = client.post("/api/v1/groups", json={"name": "Tech Meetup"}, headers=headers)
    second = client.post("/api/v1/groups", json={"name": "Tech Meetup"}, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["slug"] != second.json()["slug"]


def test_list_my_groups_only_returns_own_groups(client):
    headers_a = _signup_and_login(client, email="organizer_a@example.com")
    headers_b = _signup_and_login(client, email="organizer_b@example.com")

    client.post("/api/v1/groups", json={"name": "Group A"}, headers=headers_a)
    client.post("/api/v1/groups", json={"name": "Group B"}, headers=headers_b)

    response = client.get("/api/v1/groups", headers=headers_a)
    assert response.status_code == 200
    names = [g["name"] for g in response.json()]
    assert names == ["Group A"]


def test_get_group_by_id(client):
    headers = _signup_and_login(client)
    created = client.post("/api/v1/groups", json={"name": "Devfest Ibadan"}, headers=headers)
    group_id = created.json()["id"]

    response = client.get(f"/api/v1/groups/{group_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Devfest Ibadan"


def test_get_nonexistent_group_returns_404(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/groups/{fake_id}")
    assert response.status_code == 404