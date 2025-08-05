import pytest
from django.db.utils import IntegrityError

from quiz.models import Invitation, Attempt, Answer

pytestmark = pytest.mark.django_db


class TestQuizModel:
    def test_quiz_creation(self, quiz_factory):
        quiz = quiz_factory()
        assert quiz.title == "Test Quiz"
        assert quiz.description == "Test Description"
        assert quiz.owner is not None

    def test_max_score(self, quiz_factory, question_factory):
        quiz = quiz_factory()
        question_factory(quiz=quiz, points=2, order=0)
        question_factory(quiz=quiz, points=3, order=1)
        assert quiz.max_score == 5

    def test_total_questions(self, quiz_factory, question_factory):
        quiz = quiz_factory()
        question_factory(quiz=quiz, order=0)
        question_factory(quiz=quiz, order=1)
        assert quiz.total_questions == 2


class TestQuestionModel:
    def test_question_creation(self, quiz_factory, question_factory):
        quiz = quiz_factory()
        question = question_factory(quiz=quiz)
        assert question.text == "Test Question"
        assert question.quiz == quiz
        assert question.points == 1

    def test_unique_order_constraint(self, quiz_factory, question_factory):
        quiz = quiz_factory()
        question_factory(quiz=quiz, order=0)
        with pytest.raises(IntegrityError):
            question_factory(quiz=quiz, order=0)


class TestChoiceModel:
    def test_choice_creation(self, quiz_factory, question_factory, choice_factory):
        quiz = quiz_factory()
        question = question_factory(quiz=quiz)
        choice = choice_factory(question=question)
        assert choice.text == "Test Choice"
        assert choice.question == question
        assert not choice.is_correct

    def test_unique_correct_choice_constraint(self, quiz_factory, question_factory, choice_factory):
        quiz = quiz_factory()
        question = question_factory(quiz=quiz)
        choice_factory(question=question, is_correct=True)
        with pytest.raises(IntegrityError):
            choice_factory(question=question, is_correct=True)


class TestInvitationModel:
    def test_invitation_creation(self, quiz_factory, user_factory, invitation_factory):
        quiz = quiz_factory()
        participant = user_factory(username="pp", email="p@p.com")
        invited_by = user_factory(username="ii", email="i@i.com")
        invitation = invitation_factory(quiz=quiz, participant=participant, invited_by=invited_by)
        assert invitation.quiz == quiz
        assert invitation.participant == participant
        assert invitation.invited_by == invited_by
        assert invitation.status == Invitation.PENDING

    def test_unique_participant_constraint(self, quiz_factory, user_factory, invitation_factory):
        quiz = quiz_factory()
        participant = user_factory(username="par", email="golf@under.com")
        invited_by = user_factory(username="inv", email="always@invites.you")
        invitation_factory(quiz=quiz, participant=participant, invited_by=invited_by)
        with pytest.raises(IntegrityError):
            invitation_factory(quiz=quiz, participant=participant, invited_by=invited_by)


class TestAttemptModel:
    def test_attempt_creation(self, quiz_factory, user_factory, attempt_factory):
        quiz = quiz_factory()
        participant = user_factory(username="john_doe", email="john@aon.co.uk")
        attempt = attempt_factory(quiz=quiz, participant=participant)
        assert attempt.quiz == quiz
        assert attempt.participant == participant
        assert attempt.status == Attempt.IN_PROGRESS
        assert attempt.score == 0

    def test_percentage_score(self, quiz_factory, user_factory, question_factory, attempt_factory):
        quiz = quiz_factory()
        question_factory(quiz=quiz, points=2, order=0)
        question_factory(quiz=quiz, points=3, order=1)
        participant = user_factory(username="joe_johns_brother", email="joe@aon.co.uk")
        attempt = attempt_factory(quiz=quiz, participant=participant)
        attempt.score = 4
        attempt.save()
        assert attempt.max_score == 5
        assert attempt.percentage_score == 80.0


class TestAnswerModel:
    def test_answer_creation(self, quiz_factory, user_factory, question_factory, choice_factory, attempt_factory):
        quiz = quiz_factory()
        question = question_factory(quiz=quiz)
        choice = choice_factory(question=question, is_correct=True)
        participant = user_factory(username="answerer", email="knows@allthe.answers")
        attempt = attempt_factory(quiz=quiz, participant=participant)

        answer = Answer.objects.create(
            attempt=attempt,
            question=question,
            selected_choice=choice
        )

        assert answer.attempt == attempt
        assert answer.question == question
        assert answer.selected_choice == choice
