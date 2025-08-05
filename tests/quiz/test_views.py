import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestQuizViews:
    def test_list_add_quiz(self, authenticated_client, quiz_factory):
        client, user = authenticated_client
        quiz_factory(owner=user)
        quiz_factory(owner=user)

        url = reverse("owned_quizzes")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_create_quiz(self, authenticated_client):
        client, user = authenticated_client
        url = reverse("owned_quizzes")
        data = {
            "title": "New Quiz",
            "description": "New Description"
        }

        response = client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Quiz"
        assert response.data["owner"]["id"] == str(user.id)

    def test_quiz_detail(self, authenticated_client, quiz_factory):
        client, user = authenticated_client
        quiz = quiz_factory(owner=user)

        url = reverse("quiz_detail", kwargs={"pk": quiz.id})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == quiz.title
        assert response.data["description"] == quiz.description


class TestQuestionViews:
    def test_list_add_question(self, authenticated_client, quiz_factory, question_factory):
        client, user = authenticated_client
        quiz = quiz_factory(owner=user)
        question_factory(quiz=quiz)

        url = reverse("quiz_questions", kwargs={"pk": quiz.id})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_create_question(self, authenticated_client, quiz_factory):
        client, user = authenticated_client
        quiz = quiz_factory(owner=user)

        url = reverse("quiz_questions", kwargs={"pk": quiz.id})
        data = {
            "text": "New Question",
            "order": 0,
            "points": 2,
            "choices": [
                {"text": "Choice 1", "is_correct": True, "order": 0},
                {"text": "Choice 2", "is_correct": False, "order": 1}
            ]
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["text"] == "New Question"
        assert len(response.data["choices"]) == 2


class TestInvitationViews:
    def test_create_invitation(self, authenticated_client, quiz_factory, user_factory):
        client, user = authenticated_client
        quiz = quiz_factory(owner=user)
        participant = user_factory(username="parti", email="parti@cip.ant")

        url = reverse("quiz_invitation", kwargs={"pk": quiz.id})
        data = {
            "participant": participant.id
        }

        response = client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["quiz"] == quiz.id
        assert response.data["participant"] == participant.id
        assert response.data["invited_by"] == user.id

    def test_respond_invitation(self, authenticated_client, quiz_factory, user_factory, invitation_factory):
        client, user = authenticated_client
        quiz = quiz_factory()
        inviter = user_factory(username="inviter_v", email="inviter_v@inv.ite")
        invitation = invitation_factory(quiz=quiz, participant=user, invited_by=inviter)

        url = reverse("quiz_invitation_response", kwargs={"pk": invitation.id})
        data = {
            "status": 2  # ACCEPTED
        }

        response = client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == 2


class TestAttemptViews:
    def test_list_attempt(self, authenticated_client, quiz_factory, attempt_factory):
        client, user = authenticated_client
        quiz = quiz_factory()
        attempt_factory(quiz=quiz, participant=user)

        url = reverse("quiz_attempt_creation")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_submit_attempt(self, authenticated_client, quiz_factory, question_factory, choice_factory,
                            attempt_factory):
        client, user = authenticated_client
        quiz = quiz_factory()
        question = question_factory(quiz=quiz)
        correct_choice = choice_factory(question=question, is_correct=True)
        attempt = attempt_factory(quiz=quiz, participant=user)

        url = reverse("quiz_attempt_submission", kwargs={"pk": attempt.id})
        data = {
            "answers": [
                {
                    "attempt": attempt.id,
                    "question": question.id,
                    "selected_choice": correct_choice.id
                }
            ]
        }

        response = client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["answers"]) == 1
