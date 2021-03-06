import importlib
from django.db import models

class Plugin(models.Model):
    name = models.CharField(max_length=128, null=False, unique=True)
    triggers = None
    events = None
    pluginModule = None
    def __init__(self, *args, **kwargs):
        super(Plugin, self).__init__(*args, **kwargs)
        if self.name:
            try:
                self.pluginModule = importlib.import_module('plugins.'+self.name)
            except ImportError:
                return
            self.events = PluginEvents.objects.filter(plugin_id=self.pk)
            self.triggers = PluginTriggers.objects.filter(plugin_id=self.pk)

    def get(self):
        return super(Plugin, self).get()

    def authorize(self):
        self.is_authorized = True
        self.save()

    def trigger(self, triggerName=None):
        self.pluginModule.trigger(trigger_name=triggerName)

    def event(self, data=None):
        self.pluginModule.event(data=data)

class Middleware(models.Model):
    name = models.CharField(max_length=128, null=False, unique=True)
    is_enabled = models.BooleanField(default=True)
    middlewareModule = None

    def __init__(self, *args, **kwargs):
        super(Middleware, self).__init__(*args, **kwargs)
        if self.name:
            try:
                self.middlewareModule = importlib.import_module('middlewares.'+self.name)
            except ImportError:
                return

    def alter_event(self, data):
        return self.middlewareModule.alter_event(data)

    def alter_trigger(self, trigger_name):
        return self.middlewareModule.alter_trigger(trigger_name)

class Event(models.Model):
    name = models.CharField(max_length=128, null=False, unique=True)

class Trigger(models.Model):
    name = models.CharField(max_length=128, null=False, unique=True)

class PluginEvents(models.Model):
    plugin = models.ForeignKey(to=Plugin)
    event = models.ForeignKey(to=Event)

class PluginTriggers(models.Model):
    plugin = models.ForeignKey(to=Plugin)
    trigger = models.ForeignKey(to=Trigger)
