import json
import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        query_params = self.scope['query_string'].decode()
        token = None
        
        # Extract token from query string
        for param in query_params.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break
        
        if not token:
            await self.close()
            return
            
        try:
            # Validate token
            access_token = AccessToken(token)
            user_id_from_token = access_token['user_id']
            
            if int(self.user_id) != user_id_from_token:
                await self.close()
                return
                
            self.user = await sync_to_async(User.objects.get)(id=user_id_from_token)
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            await self.close()
            return
            
        self.group_name = f'user_{self.user_id}'
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["message"]))