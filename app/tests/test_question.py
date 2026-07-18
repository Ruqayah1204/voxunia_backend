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
        json={"title": title, "visibility": "public"},
        headers=headers,
    )
    return response.json()


def _join_as_attendee(client, session_id, display_name="Tunde"):
    response = client.post(
        f"/api/v1/sessions/{session_id}/join",
        json={"display_name": display_name},
    )
    token = response.json()["attendee_token"]
    return {"X-Attendee-Token": token}


def _live_session(client, headers, group_id):
    """Helper: create + start a session, return the session dict."""
    session = _create_session(client, headers, group_id)
    client.patch(f"/api/v1/sessions/{session['id']}/start", headers=headers)
    return session


def test_cannot_post_question_before_session_starts(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _create_session(client, headers, group_id)  # not started
    attendee_headers = _join_as_attendee(client, session["id"])

    response = client.post(
        f"/api/v1/sessions/{session['id']}/questions",
        json={"body": "What time do we start?"},
        headers=attendee_headers,
    )
    assert response.status_code == 400
    assert "hasn't started" in response.json()["detail"]


def test_post_question_success(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _live_session(client, headers, group_id)
    attendee_headers = _join_as_attendee(client, session["id"], display_name="Tunde")

    response = client.post(
        f"/api/v1/sessions/{session['id']}/questions",
        json={"body": "What's the roadmap for this quarter?"},
        headers=attendee_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["body"] == "What's the roadmap for this quarter?"
    assert data["vote_score"] == 0
    assert data["display_name"] == "Tunde"
    assert data["status"] == "visible"


def test_post_question_requires_attendee_token(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _live_session(client, headers, group_id)

    response = client.post(
        f"/api/v1/sessions/{session['id']}/questions",
        json={"body": "No token attached"},
    )
    assert response.status_code in (401, 422)  # 422 if header entirely missing, 401 if invalid


def test_list_questions_sorted_by_vote_score(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _live_session(client, headers, group_id)
    attendee_a = _join_as_attendee(client, session["id"], display_name="Tunde")
    attendee_b = _join_as_attendee(client, session["id"], display_name="Ada")

    q1 = client.post(
        f"/api/v1/sessions/{session['id']}/questions", json={"body": "Question one"}, headers=attendee_a
    ).json()
    q2 = client.post(
        f"/api/v1/sessions/{session['id']}/questions", json={"body": "Question two"}, headers=attendee_b
    ).json()

    # Upvote q2 twice (from two different attendees) so it outranks q1
    client.post(f"/api/v1/questions/{q2['id']}/vote", json={"value": 1}, headers=attendee_a)
    client.post(f"/api/v1/questions/{q2['id']}/vote", json={"value": 1}, headers=attendee_b)

    response = client.get(f"/api/v1/sessions/{session['id']}/questions")
    ordered = response.json()
    assert ordered[0]["id"] == q2["id"]
    assert ordered[0]["vote_score"] == 2
    assert ordered[1]["id"] == q1["id"]


def test_voting_twice_same_value_toggles_off(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _live_session(client, headers, group_id)
    attendee = _join_as_attendee(client, session["id"])

    question = client.post(
        f"/api/v1/sessions/{session['id']}/questions", json={"body": "Toggle test"}, headers=attendee
    ).json()

    first = client.post(f"/api/v1/questions/{question['id']}/vote", json={"value": 1}, headers=attendee)
    assert first.json()["vote_score"] == 1

    second = client.post(f"/api/v1/questions/{question['id']}/vote", json={"value": 1}, headers=attendee)
    assert second.json()["vote_score"] == 0  # same vote again removes it


def test_voting_switch_flips_score_correctly(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _live_session(client, headers, group_id)
    attendee = _join_as_attendee(client, session["id"])

    question = client.post(
        f"/api/v1/sessions/{session['id']}/questions", json={"body": "Flip test"}, headers=attendee
    ).json()

    client.post(f"/api/v1/questions/{question['id']}/vote", json={"value": 1}, headers=attendee)
    response = client.post(f"/api/v1/questions/{question['id']}/vote", json={"value": -1}, headers=attendee)
    assert response.json()["vote_score"] == -1  # +1 removed, -1 applied = net -1, not -2


def test_vote_rejects_invalid_value(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _live_session(client, headers, group_id)
    attendee = _join_as_attendee(client, session["id"])

    question = client.post(
        f"/api/v1/sessions/{session['id']}/questions", json={"body": "Bad vote test"}, headers=attendee
    ).json()

    response = client.post(f"/api/v1/questions/{question['id']}/vote", json={"value": 5}, headers=attendee)
    assert response.status_code == 400


def test_cannot_post_question_after_session_ends(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _live_session(client, headers, group_id)
    attendee = _join_as_attendee(client, session["id"])

    client.patch(f"/api/v1/sessions/{session['id']}/end", headers=headers)

    response = client.post(
        f"/api/v1/sessions/{session['id']}/questions",
        json={"body": "Too late"},
        headers=attendee,
    )
    assert response.status_code == 400
    assert "ended" in response.json()["detail"]


def test_cannot_vote_after_session_ends(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _live_session(client, headers, group_id)
    attendee = _join_as_attendee(client, session["id"])

    question = client.post(
        f"/api/v1/sessions/{session['id']}/questions", json={"body": "Vote after end test"}, headers=attendee
    ).json()

    client.patch(f"/api/v1/sessions/{session['id']}/end", headers=headers)

    response = client.post(f"/api/v1/questions/{question['id']}/vote", json={"value": 1}, headers=attendee)
    assert response.status_code == 400
    assert "ended" in response.json()["detail"]


def test_hidden_questions_excluded_from_list(client):
    headers = _signup_and_login(client)
    group_id = _create_group(client, headers)
    session = _live_session(client, headers, group_id)
    attendee = _join_as_attendee(client, session["id"])

    question = client.post(
        f"/api/v1/sessions/{session['id']}/questions", json={"body": "Should be hidden"}, headers=attendee
    ).json()

    client.patch(f"/api/v1/questions/{question['id']}", json={"status": "hidden"}, headers=headers)

    response = client.get(f"/api/v1/sessions/{session['id']}/questions")
    ids = [q["id"] for q in response.json()]
    assert question["id"] not in ids


def test_moderate_question_requires_owning_organizer(client):
    headers_a = _signup_and_login(client, email="a@example.com")
    headers_b = _signup_and_login(client, email="b@example.com")
    group_id = _create_group(client, headers_a)
    session = _live_session(client, headers_a, group_id)
    attendee = _join_as_attendee(client, session["id"])

    question = client.post(
        f"/api/v1/sessions/{session['id']}/questions", json={"body": "Ownership test"}, headers=attendee
    ).json()

    response = client.patch(
        f"/api/v1/questions/{question['id']}", json={"status": "answered"}, headers=headers_b
    )
    assert response.status_code == 404