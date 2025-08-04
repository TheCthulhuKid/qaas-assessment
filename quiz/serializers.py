from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from . import models

QuizUserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuizUserModel
        fields = ["id", "username", "email"]


class ChoiceCreationSerializer(serializers.ModelSerializer):
    """Detailed serializer for Choice model - includes correct answer info for creators"""

    class Meta:
        model = models.Choice
        fields = ["id", "text", "is_correct", "order"]


class QuestionSerializer(serializers.ModelSerializer):
    """Detailed serializer for Question model for creators"""

    choices = ChoiceCreationSerializer(many=True)

    class Meta:
        model = models.Question
        fields = [
            "id",
            "text",
            "question_type",
            "order",
            "points",
            "choices",
        ]

    def create(self, validated_data):
        validated_data["quiz_id"] = self.context["request"].parser_context["kwargs"]["pk"]
        choices_data = validated_data.pop("choices")
        question = super().create(validated_data)
        for choice_data in choices_data:
            models.Choice.objects.create(question=question, **choice_data)
        return question


class QuizSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = models.Quiz
        fields = "__all__"

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)


class QuizDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Quiz model"""

    owner = UserSerializer(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)
    total_questions = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = models.Quiz
        fields = [
            "id",
            "title",
            "description",
            "owner",
            "status",
            "start_time",
            "end_time",
            "questions",
            "total_questions",
            "is_active",
        ]
        depth = 2


class QuizProgressSerializer(serializers.ModelSerializer):
    """

    """
    total_questions = serializers.ReadOnlyField()
    total_attempts = serializers.SerializerMethodField()
    average_score = serializers.SerializerMethodField()

    class Meta:
        model = models.Quiz
        fields = ["id", "total_attempts", "total_questions", "average_score", "participant_stats"]

    def get_total_attempts(self, obj: models.Quiz) -> int:
        return obj.attempts.count()

    def get_average_score(self, obj: models.Quiz) -> float:
        attempts = obj.attempts.filter(status=models.Attempt.COMPLETED)
        if not attempts:
            return 0.0
        return round(sum(a.percentage_score or 0 for a in attempts) / len(attempts), 2)


class AttemptProgressSerializer(serializers.ModelSerializer):
    """

    """
    score = serializers.ReadOnlyField()
    percentage_score = serializers.ReadOnlyField()
    answered_questions_count = serializers.ReadOnlyField()

    class Meta:
        model = models.Attempt
        fields = ["id", "score", "percentage_score", "answered_questions_count"]


class AttemptSerializer(serializers.ModelSerializer):
    """
    Serialize an existing attempt
    """
    quiz = serializers.PrimaryKeyRelatedField(read_only=True)
    participant = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.Attempt
        fields = ["id", "quiz", "participant"]


class AnswerSerializer(serializers.ModelSerializer):
    """
    Serialize an answer for submission
    """

    class Meta:
        model = models.Answer
        fields = ["id", "attempt", "question", "selected_choice"]

    def validate(self, attrs):
        if attrs["attempt"].quiz != attrs["question"].quiz:
            raise serializers.ValidationError("This question is not part of this quiz")
        if attrs["selected_choice"].question != attrs["question"]:
            raise serializers.ValidationError("This is not a valid answer")
        return attrs


class AttemptSubmissionSerializer(serializers.ModelSerializer):
    """
    This is not the best way to do this. My mind hit a blank. Sorry!
    """
    quiz = QuizDetailSerializer(read_only=True)
    answers = AnswerSerializer(many=True)

    class Meta:
        model = models.Attempt
        fields = ["id", "quiz", "participant", "status", "answers"]
        read_only_fields = ["id", "quiz", "participant", "status"]
        depth = 2

    def update(self, instance, validated_data):
        answers = validated_data.pop("answers")
        for answer in answers:
            if not answer.get("id"):
                models.Answer.objects.create(**answer)
        return instance


class InvitationCreationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating quiz invitations
    """
    quiz = serializers.PrimaryKeyRelatedField(read_only=True)
    invited_by = serializers.PrimaryKeyRelatedField(read_only=True)
    participant = serializers.PrimaryKeyRelatedField(queryset=models.QuizUser.objects.all())

    class Meta:
        model = models.Invitation
        fields = ["id", "quiz", "participant", "invited_by"]

    def create(self, validated_data):
        validated_data["quiz_id"] = self.context["request"].parser_context["kwargs"]["pk"]
        validated_data["invited_by"] = self.context["request"].user
        invitation = super().create(validated_data)

        # Send WebSocket notification
        channel_layer = get_channel_layer()
        participant_id = validated_data["participant"].id

        # Get quiz title for the notification
        quiz_title = invitation.quiz.title
        inviter_name = invitation.invited_by.get_full_name() or invitation.invited_by.username

        # Prepare the message
        message = {
            "type": "invitation",
            "invitation_id": str(invitation.id),
            "quiz_id": str(invitation.quiz.id),
            "quiz_title": quiz_title,
            "inviter": inviter_name,
            "message": f"You have been invited to take the quiz: {quiz_title} by {inviter_name}"
        }

        # Send to the participant's group
        async_to_sync(channel_layer.group_send)(
            f"user_{participant_id}",
            {
                "type": "invitation_message",
                "content": message
            }
        )

        return invitation


class InvitationResponseSerializer(serializers.ModelSerializer):
    """
    This is actually legacy as the response should be handled by channels
    """
    quiz = serializers.PrimaryKeyRelatedField(read_only=True)
    invited_by = serializers.PrimaryKeyRelatedField(read_only=True)
    participant = serializers.PrimaryKeyRelatedField(read_only=True)
    responded_at = serializers.HiddenField(default=timezone.now)

    class Meta:
        model = models.Invitation
        fields = ["quiz", "participant", "invited_by", "status", "responded_at"]

    def validate_status(self, value):
        """

        """
        if value not in [models.Invitation.ACCEPTED, models.Invitation.DECLINED]:
            raise serializers.ValidationError("Respondees can only accept or decline")
        return value
