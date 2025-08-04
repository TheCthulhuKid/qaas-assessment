from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Answer, Attempt, Invitation


@receiver(post_save, sender=Invitation)
def handle_invitation_status_change(sender, instance, created, **kwargs) -> None:
    """
    If an invitation is accepted create an attempt.
    """
    if not created and instance.status != Invitation.PENDING:
        # Invitation status has changed, notify the inviter
        channel_layer = get_channel_layer()
        inviter_id = instance.invited_by.id

        status_text = dict(Invitation.STATUS_CHOICES)[instance.status]

        # Prepare the message
        message = {
            "type": "invitation_response",
            "invitation_id": str(instance.id),
            "quiz_id": str(instance.quiz.id),
            "quiz_title": instance.quiz.title,
            "participant": instance.participant.get_full_name() or instance.participant.username,
            "status": status_text,
            "message": f"{instance.participant.get_full_name() or instance.participant.username} has {status_text.lower()} your invitation to {instance.quiz.title}"
        }

        # Send to the inviter's group
        async_to_sync(channel_layer.group_send)(
            f"user_{inviter_id}",
            {
                "type": "invitation_message",
                "content": message
            }
        )

        # If accepted, create an attempt
        if instance.status == Invitation.ACCEPTED:
            Attempt.objects.create(
                quiz=instance.quiz,
                participant=instance.participant,
                status=Attempt.IN_PROGRESS
            )


@receiver(post_save, sender=Answer)
def handle_assigning_score(sender, instance, created, **kwargs) -> None:
    if instance and created:
        if instance.selected_choice.is_correct:
            instance.attempt.score += instance.question.points
            instance.attempt.save()
