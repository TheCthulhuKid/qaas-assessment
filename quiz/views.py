from rest_framework import generics

from .models import Invitation, Question, Quiz, Attempt
from .permissions import IsQuizOwner, IsInvitee
from .serializers import (
    InvitationCreationSerializer, QuestionSerializer, QuizSerializer, QuizDetailSerializer,
    InvitationResponseSerializer, AttemptSerializer, AttemptSubmissionSerializer,
    QuizProgressSerializer, AttemptProgressSerializer
)

############################
# User views
############################




############################
# Quiz views
############################

class ListAddQuiz(generics.ListCreateAPIView):
    """

    """
    serializer_class = QuizSerializer
    permission_classes = [IsQuizOwner]

    def get_queryset(self):
        queryset = Quiz.objects.filter(owner=self.request.user)
        return queryset


class ListPlayableQuiz(generics.ListAPIView):
    """

    """
    serializer_class = QuizSerializer

    def get_queryset(self):
        return Quiz.objects.prefetch_related("attempts__participant").filter(attempts__participant=self.request.user)


class QuizDetail(generics.RetrieveUpdateAPIView):
    """

    """
    serializer_class = QuizDetailSerializer

    def get_queryset(self):
        if "creator" in self.request.path:
            return Quiz.objects.filter(owner=self.request.user)
        else:
            return Quiz.objects.prefetch_related("attempts__participant").filter(attempts__participant=self.request.user)


class ListAddQuestion(generics.ListCreateAPIView):
    """
    Creation and listing of questions
    """
    serializer_class = QuestionSerializer

    def get_queryset(self):
        quiz_id = self.kwargs["pk"]
        qs = Question.objects.filter(quiz=quiz_id)

        return qs


# Take quiz
class ListAttempt(generics.ListAPIView):
    """
    This actually shows the available attempt so the user can access it
    """
    serializer_class = AttemptSerializer

    def get_queryset(self):
        queryset = Attempt.objects.filter(participant=self.request.user)

        return queryset


class SubmitAttempt(generics.RetrieveUpdateAPIView):
    """
    Submit answers for a quiz. This is not my best work.
    """
    serializer_class = AttemptSubmissionSerializer

    def get_queryset(self):
        queryset = Attempt.objects.filter(participant=self.request.user)

        return queryset


# Quiz stats
class QuizProgress(generics.RetrieveAPIView):
    """
    See statistics for an individual quiz
    """
    queryset = Quiz.objects.all()
    serializer_class = QuizProgressSerializer
    permission_classes = [IsQuizOwner]


# Attempt stats
class AttemptProgress(generics.RetrieveAPIView):
    """
    See the progress of an individual attempt
    """
    serializer_class = AttemptProgressSerializer

    def get_queryset(self):
        queryset = Attempt.objects.filter(participant=self.request.user)

        return queryset


# Send invitation
class CreateInvitation(generics.CreateAPIView):
    """
    This view will send an invite via web socket.
    """
    serializer_class = InvitationCreationSerializer


# Respond to invitation
class RespondInvitation(generics.RetrieveUpdateAPIView):
    """
    View for invitation responses as a fallback should channels not work
    """
    serializer_class = InvitationResponseSerializer
    permission_classes = [IsInvitee]

    def get_queryset(self):
        queryset = Invitation.objects.filter(status=Invitation.PENDING)
        return queryset
