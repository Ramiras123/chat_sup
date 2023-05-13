import json
from urllib import request

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings
from django.utils import timezone
import asyncpg
from datetime import datetime
from channels.db import database_sync_to_async
from . models import Message
from django.contrib.auth.models import User

async def add_message(username, message, datetime, room, ip_address):
    conn = await asyncpg.connect(
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        database=settings.DATABASES['default']['NAME'],
    )
    try:
        await conn.execute(
            "INSERT INTO chat_message (username_id, message, datetime, room, ip_address) VALUES ($1, $2, $3, $4, $5)",
            username, message, datetime, room, ip_address
        )
    finally:
        await conn.close()


@database_sync_to_async
def get_messages(room):
    messages = Message.objects.filter(room=room)
    return messages


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.ip_address = self.scope['client'][0]
        self.id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.id}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        messages = await get_messages(self.id)
        await self.accept()
        async for message in messages:
            if message.username:
                username = message.username.username
            else:
                username = 'Аноним'
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'message': message.message,
                'user': username,
                'datetime': message.datetime.isoformat(),
                'ip_address': message.ip_address
            }))

    async def disconnect(self, code):
        await async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        now = timezone.now()
        await add_message(self.user.id, message, now, int(self.id), self.ip_address)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': self.user.username,
                'datetime': now.isoformat(),
                'ip_address': self.ip_address,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
        