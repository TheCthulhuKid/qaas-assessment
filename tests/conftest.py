import pytest
import asyncio
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from quiz.models import Quiz, Question, Choice, Invitation, Attempt

User = get_user_model()


# This fixture ensures that the channel layer is cleared between tests
@pytest.fixture(autouse=True)
def clear_channel_layer():
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.flush())


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_factory():
    def create_user(username="testuser", password="testpassword", email="test@test.com", **kwargs):
        return User.objects.create_user(username=username, password=password, email=email, **kwargs)
    return create_user


@pytest.fixture
def authenticated_client(api_client, user_factory):
    user = user_factory()
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client, user


@pytest.fixture
def quiz_factory(user_factory):
    def create_quiz(owner=None, title="Test Quiz", description="Test Description"):
        if owner is None:
            owner = user_factory(username=f"owner_{title}", email="another@test.com")
        return Quiz.objects.create(
            title=title,
            description=description,
            owner=owner
        )
    return create_quiz


@pytest.fixture
def question_factory():
    def create_question(quiz, text="Test Question", order=0, points=1):
        return Question.objects.create(
            quiz=quiz,
            text=text,
            order=order,
            points=points
        )
    return create_question


@pytest.fixture
def choice_factory():
    def create_choice(question, text="Test Choice", is_correct=False, order=0):
        return Choice.objects.create(
            question=question,
            text=text,
            is_correct=is_correct,
            order=order
        )
    return create_choice


@pytest.fixture
def invitation_factory():
    def create_invitation(quiz, participant, invited_by, status=Invitation.PENDING):
        return Invitation.objects.create(
            quiz=quiz,
            participant=participant,
            invited_by=invited_by,
            status=status
        )
    return create_invitation


@pytest.fixture
def attempt_factory():
    def create_attempt(quiz, participant, status=Attempt.IN_PROGRESS):
        return Attempt.objects.create(
            quiz=quiz,
            participant=participant,
            status=status
        )
    return create_attempt
