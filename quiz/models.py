import uuid
from datetime import datetime, timezone

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils.translation import gettext_lazy as _


class QuizUser(AbstractUser):
    """
    Custom user setting the ID to a UUID and requiring an email address.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("eMail Address"), unique=True, blank=True)


class BaseModel(models.Model):
    """
    Basic mixin for standard data (id, creation/mod times).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class Quiz(BaseModel):
    """
    Representation of a basic quiz structure.
    TODO: Given this is a backend does it make sense to give each a slug?
    """
    DRAFT = 1
    ACTIVE = 2
    CLOSED = 3
    STATUS = [
        (DRAFT, _("Draft")),
        (ACTIVE, _("Active")),
        (CLOSED, _("Closed")),
    ]
    owner = models.ForeignKey(QuizUser, on_delete=models.CASCADE, related_name="created_quizzes")
    title = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    status = models.PositiveSmallIntegerField(choices=STATUS, default=DRAFT)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Quizzes"

    def __str__(self) -> str:
        return self.title


    @property
    def is_active(self) -> bool:
        """
        Check if a quiz is still active.
        TODO: Use a signal to set status
        """
        if not self.status == self.ACTIVE:
            return False

        now = datetime.now(timezone.utc)
        if self.start_time and self.start_time > now:
            return False
        if self.end_time and now  < self.end_time:
            return False

        return True

    @property
    def max_score(self):
        return sum(self.questions.points)


class Question(models.Model):
    """
    Model representing a question in a Quiz.
    """
    # Different types of quiz questions may become available (free text, image, etc.)
    MULTI = 1

    QUESTION_TYPES = [
        (MULTI, _("Multiple Choice")),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    question_type = models.PositiveSmallIntegerField(choices=QUESTION_TYPES, default=MULTI)
    order = models.PositiveSmallIntegerField(default=0)
    points = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["order"]
        constraints = [
            UniqueConstraint(
                fields=["quiz", "order"],
                name="unique_question_order_in_quiz",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.quiz.title} - Question {self.order + 1}"


class Choice(models.Model):
    """
    A single option for a question. Only a single choice may be marked as 'is_correct'.
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=240)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        constraints = [
            UniqueConstraint(
                fields=["question"],
                condition=Q(is_correct=True),
                name="unique_correct_choice_per_question",
            ),
            UniqueConstraint(
                fields=["question", "order"],
                name="unique_choice_order_for_question",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.question} - {self.text[:50]}"


class Invitation(BaseModel):
    """
    Invitation between users. This should be sent 'in-app' and possibly per email.
    """

    PENDING = 1
    ACCEPTED = 2
    DECLINED = 3
    EXPIRED = 4

    STATUS_CHOICES = [
        (PENDING, _("Pending")),
        (ACCEPTED, _("Accepted")),
        (DECLINED, _("Declined")),
        (EXPIRED, _("Expired")),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="invitations")
    participant = models.ForeignKey(QuizUser, on_delete=models.CASCADE, related_name="quiz_invitations")
    invited_by = models.ForeignKey(QuizUser, on_delete=models.CASCADE, related_name="sent_invitations")
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=PENDING)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["quiz", "participant"],
                name="one_entry_per_participant_per_quiz",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.quiz.title} - {self.participant.email}"


class Attempt(BaseModel):
    """
    Represents an attempt by a user at a quiz. For the moment limited to 1 (one).
    """

    IN_PROGRESS = 1
    COMPLETED = 2
    EXPIRED = 3

    STATUS_CHOICES = [
        (IN_PROGRESS, _("In Progress")),
        (COMPLETED, _("Completed")),
        (EXPIRED, _("Out of Time")),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    participant = models.ForeignKey(QuizUser, on_delete=models.CASCADE, related_name="quiz_attempts")
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=IN_PROGRESS)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.participant.email} - {self.quiz.title} ({self.status})"

    @property
    def percentage_score(self):
        if self.score is None:
            return 0.0
        return round((self.score/self.quiz.max_score) * 100, 2)


class Answer(models.Model):
    """
    An answer selected by the user. Currently only 1 (one) is allowed.
    """

    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["attempt", "question"],
                name="single_attempt_per_questions",
            ),
        ]

    def __str__(self) -> str:
        return f"Answer: {self.selected_choice.text}"
