from django.contrib.auth.models import User
from django.db import models


class Message(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE, default=None, null=True)
    message = models.TextField()
    datetime = models.DateTimeField()
    room = models.IntegerField()
    ip_address = models.GenericIPAddressField()