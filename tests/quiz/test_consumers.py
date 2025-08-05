import pytest
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model

from quiz.models import Invitation
from quiz.consumers import InvitationConsumer

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_websocket_connect(user_factory):
    user = await database_sync_to_async(user_factory)()

    communicator = WebsocketCommunicator(
        application=InvitationConsumer.as_asgi(),
        path="/ws/invitations/"
    )
    communicator.scope["user"] = user

    connected, _ = await communicator.connect()
    assert connected

    await communicator.disconnect()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_invitation_message(user_factory, quiz_factory, invitation_factory):
    inviter = await database_sync_to_async(user_factory)(username="inviter1", email="inviter1@inv.iter")
    participant = await database_sync_to_async(user_factory)(username="participant1", email="part1@ici.pant")

    quiz = await database_sync_to_async(quiz_factory)(owner=inviter)

    communicator = WebsocketCommunicator(
        application=InvitationConsumer.as_asgi(),
        path="/ws/invitations/"
    )
    communicator.scope["user"] = participant
    connected, _ = await communicator.connect()
    assert connected

    # Create an invitation (this should trigger a WebSocket message)
    invitation = await database_sync_to_async(invitation_factory)(
        quiz=quiz,
        participant=participant,
        invited_by=inviter
    )

    # Send the WebSocket message manually (since we"re bypassing the serializer)
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"user_{participant.id}",
        {
            "type": "invitation_message",
            "content": {
                "type": "invitation",
                "invitation_id": str(invitation.id),
                "quiz_id": str(quiz.id),
                "quiz_title": quiz.title,
                "inviter": inviter.username,
                "message": f"You have been invited to take the quiz: {quiz.title} by {inviter.username}"
            }
        }
    )

    response = await communicator.receive_json_from()

    # Verify the message content
    assert response["type"] == "invitation"
    assert response["invitation_id"] == str(invitation.id)
    assert response["quiz_id"] == str(quiz.id)
    assert response["quiz_title"] == quiz.title

    await communicator.disconnect()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_invitation_response(user_factory, quiz_factory, invitation_factory):
    inviter = await database_sync_to_async(user_factory)(username="inviter2", email="inviter2@inv.ite")
    participant = await database_sync_to_async(user_factory)(username="participant2", email="part2@ici.pant")

    quiz = await database_sync_to_async(quiz_factory)(owner=inviter)

    invitation = await database_sync_to_async(invitation_factory)(
        quiz=quiz,
        participant=participant,
        invited_by=inviter
    )

    communicator = WebsocketCommunicator(
        application=InvitationConsumer.as_asgi(),
        path="/ws/invitations/"
    )
    communicator.scope["user"] = participant
    connected, _ = await communicator.connect()
    assert connected

    # Send a response to the invitation via WebSocket
    await communicator.send_json_to({
        "type": "invitation_response",
        "invitation_id": str(invitation.id),
        "status": "accept"
    })

    # Receive confirmation
    response = await communicator.receive_json_from()
    assert response["type"] == "response_confirmation"
    assert response["invitation_id"] == str(invitation.id)
    assert response["status"] == "accept"

    # Verify the database was updated
    invitation = await database_sync_to_async(Invitation.objects.get)(id=invitation.id)
    assert invitation.status == Invitation.ACCEPTED

    await communicator.disconnect()
