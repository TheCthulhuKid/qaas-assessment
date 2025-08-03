from rest_framework import permissions

from quiz.models import Invitation


class IsQuizOwner(permissions.BasePermission):
    """
    Custom permission to only allow quiz creators to edit their quizzes.
    """

    def has_object_permission(self, request, view, obj) -> bool:
        return obj.creator == request.user


class IsInvitedParticipant(permissions.BasePermission):
    """
    Custom permission to only allow invited participants to access quiz.
    """

    def has_object_permission(self, request, view, obj) -> bool:
        # Check if user has an accepted invitation
        return Invitation.objects.filter(
            quiz=obj, participant=request.user, status=Invitation.ACCEPTED
        ).exists()
