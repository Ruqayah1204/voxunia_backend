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


def _create_group(client, headers, name="Red Cross Ogun"):
    response = client.post("/api/v1/groups", json={"name": name}, headers=headers)
    return response.json()["id"]


def _live_session(client, headers, group_id, title="Weekly Standup"):
    session = client.post(
        f"/api/v1/groups/{group_id}/sessions",
        json={"title": title, "visibility": "public"},
        headers=headers,
    ).json()
    client.patch(f"/api/v1/sessions/{session['id']}/start", headers=headers)
    return session


def _join_as_attendee(client, session_id, display_name="Tunde"):
    response = client.post(
        f"/api/v1/sessions/{session_id}/join",
        json={"display_name": display_name},
    )
    token = response.json()["attendee_token"]
    return {"X-Attendee-Token": token}


def test_organizer_can_comment(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _live_session(client, headers, group_id)
    attendee = _join_as_attendee(client, session["id"])

    question = client.post(
        f"/api/v1/sessions/{session['id']}/questions", json={"body": "Q for organizer reply"}, headers=attendee
    ).json()

    response = client.post(
        f"/api/v1/questions/{question['id']}/comments",
        json={"body": "Great question, answering now."},
        headers=headers,
    )
    assert response.status_code == 201


def test_attendee_can_comment(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _live_session(client, headers, group_id)
    attendee = _join_as_attendee(client, session["id"])

    question = client.post(
        f"/api/v1/sessions/{session['id']}/questions", json={"body": "Q for attendee reply"}, headers=attendee
    ).json()

    response = client.post(
        f"/api/v1/questions/{question['id']}/comments",
        json={"body": "I have the same question!"},
        headers=attendee,
    )
    assert response.status_code == 201


def test_comment_without_any_auth_rejected(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _live_session(client, headers, group_id)
    attendee = _join_as_attendee(client, session["id"])

    question = client.post(
        f"/api/v1/sessions/{session['id']}/questions", json={"body": "No-auth comment test"}, headers=attendee
    ).json()

    response = client.post(
        f"/api/v1/questions/{question['id']}/comments",
        json={"body": "Should be rejected"},
    )
    assert response.status_code == 401


def test_comment_on_ended_session_rejected(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _live_session(client, headers, group_id)
    attendee = _join_as_attendee(client, session["id"])

    question = client.post(
        f"/api/v1/sessions/{session['id']}/questions", json={"body": "Ended session comment test"}, headers=attendee
    ).json()

    client.patch(f"/api/v1/sessions/{session['id']}/end", headers=headers)

    response = client.post(
        f"/api/v1/questions/{question['id']}/comments",
        json={"body": "Too late to comment"},
        headers=attendee,
    )
    assert response.status_code == 400