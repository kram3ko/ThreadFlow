import pytest
from apps.accounts.models import User
from apps.captcha.services import issue_challenge
from apps.comments.models import Comment, CommentVote
from rest_framework.test import APIClient

CREDENTIALS = "Str0ngPass!234"


def _root_comment() -> Comment:
    comment = Comment.objects.create(
        author_name="Author",
        author_email="author@example.com",
        html_text="Root",
        search_text="Root",
        depth=0,
    )
    comment.root_id = comment.id
    comment.save(update_fields=["root"])
    return comment


@pytest.mark.django_db
def test_guest_vote_updates_score_and_cannot_double_count():
    comment = _root_comment()
    client = APIClient()
    url = f"/api/comments/{comment.id}/vote"

    assert client.post(url, {"value": 1}, format="json").json()["score"] == 1
    assert client.post(url, {"value": 1}, format="json").json()["score"] == 1
    assert client.post(url, {"value": -1}, format="json").json()["score"] == -1
    assert client.post(url, {"value": 0}, format="json").json()["score"] == 0
    assert CommentVote.objects.filter(comment=comment).count() == 0


@pytest.mark.django_db
def test_authenticated_user_can_post_without_guest_fields():
    user = User.objects.create_user(
        username="Poster", email="poster@example.com", password=CREDENTIALS
    )
    client = APIClient()
    client.force_authenticate(user=user)
    challenge = issue_challenge(answer="ABC123")

    response = client.post(
        "/api/comments",
        {
            "username": "",
            "email": "",
            "text": "authenticated comment",
            "captcha_id": str(challenge.id),
            "captcha_answer": "ABC123",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["author_name"] == "Poster"


@pytest.mark.django_db
def test_guest_without_name_or_email_gets_a_clear_message():
    challenge = issue_challenge(answer="ABC123")
    response = APIClient().post(
        "/api/comments",
        {
            "username": "",
            "email": "",
            "text": "guest comment",
            "captcha_id": str(challenge.id),
            "captcha_answer": "ABC123",
        },
        format="json",
    )

    assert response.status_code == 400
    details = response.json()["error"]["details"]
    assert "required for guests" in details["username"][0]
