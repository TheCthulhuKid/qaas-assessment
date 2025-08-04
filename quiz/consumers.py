import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

from quiz.models import Invitation

User = get_user_model()


class InvitationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        # Create a user-specific group
        self.group_name = f"user_{self.user.id}"

        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type")

        if message_type == "invitation_response":
            invitation_id = data.get("invitation_id")
            status = data.get("status")

            # Update invitation status in the database
            await self.update_invitation_status(invitation_id, status)

            # Send confirmation back to the client
            await self.send(text_data=json.dumps({
                "type": "response_confirmation",
                "invitation_id": invitation_id,
                "status": status,
                "message": f"Your response has been recorded: {status}"
            }))

    # Database operation to update invitation status
    @database_sync_to_async
    def update_invitation_status(self, invitation_id, status):
        try:
            invitation = Invitation.objects.get(id=invitation_id, participant=self.user)

            # Convert string status to integer status code
            status_map = {
                "accept": Invitation.ACCEPTED,
                "decline": Invitation.DECLINED
            }

            if status in status_map:
                invitation.status = status_map[status]
                invitation.responded_at = timezone.now()
                invitation.save()
                return True
            return False
        except Invitation.DoesNotExist:
            return False

    # Receive message from group
    async def invitation_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event["content"]))
