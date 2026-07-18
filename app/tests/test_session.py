def _signup_and_login(client, email="rukky@example.com"):
    client.post(
        "/api/v1/auth/signup",
        json={"name": "Rukky", "email": email, "password": "testpass123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_group(client, headers, name="Red Cross Ogun"):
    response = client.post("/api/v1/groups", json={"name": name}, headers=headers)
    return response.json()["id"]


def _create_session(client, headers, group_id, title="Weekly Standup"):
    response = client.post(
        f"/api/v1/groups/{group_id}/sessions",
        json={"title": title, "visibility": "private"},
        headers=headers,
    )
    return response.json()


def test_create_session_success(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)

    response = client.post(
        f"/api/v1/groups/{group_id}/sessions",
        json={"title": "Weekly Standup", "visibility": "public"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Weekly Standup"
    assert data["status"] == "upcoming"
    assert len(data["join_code"]) == 6


def test_create_session_rejects_other_organizers_group(client):
    headers_a = _signup_and_login(client, email="a@example.com")
    headers_b = _signup_and_login(client, email="b@example.com")
    group_id = _create_group(client, headers_a)

    response = client.post(
        f"/api/v1/groups/{group_id}/sessions",
        json={"title": "Sneaky Session"},
        headers=headers_b,
    )
    assert response.status_code == 404


def test_preview_session_by_join_code(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _create_session(client, headers, group_id)

    response = client.get(f"/api/v1/sessions/preview/{session['join_code']}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Weekly Standup"
    assert data["live_attendee_count"] == 0


def test_preview_invalid_code_returns_404(client):
    response = client.get("/api/v1/sessions/preview/BADCODE")
    assert response.status_code == 404


def test_join_session_returns_attendee_token(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _create_session(client, headers, group_id)

    response = client.post(
        f"/api/v1/sessions/{session['id']}/join",
        json={"display_name": "Tunde"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Tunde"
    assert "attendee_token" in data


def test_join_session_allows_anonymous(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _create_session(client, headers, group_id)

    response = client.post(f"/api/v1/sessions/{session['id']}/join", json={})
    assert response.status_code == 200
    assert response.json()["display_name"] is None


def test_preview_reflects_live_attendee_count(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _create_session(client, headers, group_id)

    client.post(f"/api/v1/sessions/{session['id']}/join", json={"display_name": "Tunde"})
    client.post(f"/api/v1/sessions/{session['id']}/join", json={"display_name": "Ada"})

    response = client.get(f"/api/v1/sessions/preview/{session['join_code']}")
    assert response.json()["live_attendee_count"] == 2


def test_start_session_transitions_to_live(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _create_session(client, headers, group_id)

    response = client.patch(f"/api/v1/sessions/{session['id']}/start", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "live"


def test_start_session_twice_fails(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _create_session(client, headers, group_id)

    client.patch(f"/api/v1/sessions/{session['id']}/start", headers=headers)
    response = client.patch(f"/api/v1/sessions/{session['id']}/start", headers=headers)
    assert response.status_code == 400


def test_end_session_sets_status_and_ends_at(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _create_session(client, headers, group_id)

    client.patch(f"/api/v1/sessions/{session['id']}/start", headers=headers)
    response = client.patch(f"/api/v1/sessions/{session['id']}/end", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ended"
    assert data["ends_at"] is not None