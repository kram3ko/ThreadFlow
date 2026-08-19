import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_guest_can_create_root_and_reply(api_client):
    root_response = api_client.post(
        "/api/comments",
        {
            "username": "Alice1",
            "email": "alice@example.com",
            "homepage": "https://example.com",
            "text": "Root comment",
        },
        format="json",
    )
    assert root_response.status_code == 201
    root = root_response.json()
    assert root["root_id"] == root["id"]
    assert root["depth"] == 0

    reply_response = api_client.post(
        f"/api/comments/{root['id']}/replies",
        {
            "username": "Bob2",
            "email": "bob@example.com",
            "text": "Reply",
        },
        format="json",
    )
    assert reply_response.status_code == 201
    assert reply_response.json()["depth"] == 1

    list_response = api_client.get("/api/comments")
    assert list_response.status_code == 200
    assert list_response.json()["results"][0]["replies"][0]["text"] == "Reply"


@pytest.mark.django_db
def test_guest_identity_is_required(api_client):
    response = api_client.post("/api/comments", {"text": "Missing author"}, format="json")
    assert response.status_code == 400
    assert set(response.json()["error"]["details"]) == {"username", "email"}


@pytest.mark.django_db
def test_initial_text_storage_is_safe(api_client):
    response = api_client.post(
        "/api/comments",
        {
            "username": "Alice1",
            "email": "alice@example.com",
            "text": "<script>alert(1)</script>",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["html_text"] == "&lt;script&gt;alert(1)&lt;/script&gt;"


@pytest.mark.django_db
def test_roots_can_be_sorted_by_name(api_client):
    for username in ("Zulu", "Alpha"):
        response = api_client.post(
            "/api/comments",
            {
                "username": username,
                "email": f"{username.lower()}@example.com",
                "text": username,
            },
            format="json",
        )
        assert response.status_code == 201

    response = api_client.get("/api/comments?sort=name&direction=asc")
    assert [item["author_name"] for item in response.json()["results"]] == ["Alpha", "Zulu"]


@pytest.mark.django_db
def test_deep_branches_are_truncated_with_marker(api_client):
    payload = {
        "username": "Depth1",
        "email": "depth@example.com",
        "text": "Depth 0",
    }
    response = api_client.post("/api/comments", payload, format="json")
    parent_id = response.json()["id"]

    for depth in range(1, 4):
        payload["text"] = f"Depth {depth}"
        response = api_client.post(
            f"/api/comments/{parent_id}/replies",
            payload,
            format="json",
        )
        parent_id = response.json()["id"]

    tree = api_client.get("/api/comments").json()["results"][0]
    depth_two = tree["replies"][0]["replies"][0]
    assert depth_two["depth"] == 2
    assert depth_two["replies"] == []
    assert depth_two["has_more_replies"] is True
