__author__ = 'Saurabh'
from django.db import models
import uuid
import hmac
from django.contrib.auth.models import User
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from Common.models import IncompleteDataException
from Plugin.models import Plugin

try:
    from hashlib import sha1
except ImportError:
    import sha
    sha1 = sha.sha

class Device(models.Model):
    name = models.CharField(max_length=128, null=False, unique=True)
    password = models.CharField(max_length=128, null=False)
    auth_token = models.CharField(max_length=128, blank=True, default='', db_index=True)
    is_authorized = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.name:
            raise IncompleteDataException('Name')
        if not self.password:
            raise IncompleteDataException('Password')
        if not self.auth_token:
            self.auth_token = self.generateKey()
            self.password = PBKDF2PasswordHasher().encode(self.password, salt=self.name)
        return super(Device, self).save(*args, **kwargs)

    def verifyPassword(self, password):
        if PBKDF2PasswordHasher().verify(password=password, encoded=self.password):
            return True
        return False

    def generateKey(self):
            new_uuid = uuid.uuid4()
            return hmac.new(new_uuid.bytes, digestmod=sha1).hexdigest()

    def authorize(self, token):
        if self.auth_token == token:
            self.is_authorized = True
            self.save()

class DevicePluginRegistration(models.Model):
    device = models.ForeignKey(to=Device, null=False)
    plugin = models.ForeignKey(to=Plugin, null=False)
