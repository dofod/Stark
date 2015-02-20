__author__ = 'Saurabh'
import base64
import os
import importlib
import inspect
from django.db import transaction
from tastypie.resources import Resource, Bundle, ModelResource, ALL, fields
from tastypie.exceptions import BadRequest
from tastypie.authentication import ApiKeyAuthentication, MultiAuthentication
from Common.auth import OpenAuthentication, OpenAuthorization
from Common.resources import CORSModelResource
from Common.api import TastypieAPIObject
from Common.models import IncompleteDataException
from Device.auth import DeviceTokenAuthentication
from .models import Plugin, Event, Trigger, PluginEvents, PluginTriggers

class PluginResource(ModelResource):
    class Meta:
        queryset = Plugin.objects.all()
        resource_name = 'plugin'
        allowed_methods = ['get', 'post']
        authentication = MultiAuthentication(DeviceTokenAuthentication(), ApiKeyAuthentication())
        authorization = OpenAuthorization()

    def inspectPlugin(self, pluginModule):
        if 'trigger' not in dir(pluginModule) \
                or inspect.getargspec(pluginModule.trigger).args[0] != 'trigger_name' \
                or 'event' not in dir(pluginModule) \
                or inspect.getargspec(pluginModule.event).args[0] != 'data':
            return False
        return True

    def obj_create(self, bundle, **kwargs):
        try:
            super(PluginResource, self).obj_create(bundle, **kwargs)
        except:
            raise BadRequest('Duplicate Plugin')

        plugin = Plugin.objects.get(name=bundle.data['name'])
        pluginFilePath = os.path.join(os.getcwd(), 'plugins', bundle.data['name']+'.py')
        pluginFile = open(pluginFilePath , 'w+')
        pluginFile.write(base64.b64decode(bundle.data['file']))
        pluginFile.close()
        pluginModule = importlib.import_module('plugins.'+bundle.data['name'])

        if not self.inspectPlugin(pluginModule):
            Plugin.objects.get(name=bundle.data['name']).delete()
            os.remove(pluginFilePath)
            raise BadRequest('ERROR: Malformed plugin, trigger undefined')

        try:
            for event in pluginModule.requires_events:
                PluginEvents.objects.create(plugin=plugin, event=Event.objects.get_or_create(name=event)[0])
        except AttributeError:
            print 'WARNING: requires_events not defined'

        try:
            for trigger in pluginModule.requires_triggers:
                PluginTriggers.objects.create(plugin=plugin, trigger=Trigger.objects.get_or_create(name=trigger)[0])
        except AttributeError:
            print 'WARNING: requires_triggers not defined'

        return bundle

    def dehydrate(self, bundle):
        bundle.data['events'] = [pluginEvent.event.name for pluginEvent in PluginEvents.objects.filter(plugin_id=bundle.obj.id)]
        bundle.data['triggers'] = [pluginTrigger.trigger.name for pluginTrigger in PluginTriggers.objects.filter(plugin_id=bundle.obj.id)]
        return bundle

class EventResource(ModelResource):
    class Meta:
        queryset = Event.objects.all()
        resource_name = 'event'
        allowed_methods = ['post']
        authentication = DeviceTokenAuthentication()
        authorization = OpenAuthorization()
        include_resource_uri = False

    def obj_create(self, bundle, **kwargs):
        for plugin in PluginEvents.objects.filter(event=Event.objects.get(name=bundle.data['event'])):
            plugin.plugin.event(data=bundle.data)
        return bundle

class TriggerResource(ModelResource):
    class Meta:
        queryset = Trigger.objects.all()
        resource_name = 'trigger'
        allowed_methods = ['post']
        authentication = OpenAuthentication()
        authorization = OpenAuthorization()
        include_resource_uri = False
    def obj_create(self, bundle, **kwargs):
        for plugin in PluginTriggers.objects.filter(trigger=Trigger.objects.get(name=bundle.data['trigger'])):
            plugin.plugin.trigger(triggerName=bundle.data['trigger'])
        return bundle

class PluginTriggersResource(CORSModelResource):
    plugin = fields.ForeignKey(to=PluginResource, attribute='plugin', full=True)
    trigger = fields.ForeignKey(to=TriggerResource, attribute='trigger', full=True)
    class Meta:
        queryset = PluginTriggers.objects.all()
        resource_name = 'plugin-triggers'
        allowed_methods = ['get']
        authentication = OpenAuthentication()
        authorization = OpenAuthorization()
        filtering = {
            'plugin_id': ALL
        }
        include_resource_uri = False

class PluginEventsResource(CORSModelResource):
    plugin = fields.ForeignKey(to=PluginResource, attribute='plugin', full=True)
    event = fields.ForeignKey(to=EventResource, attribute='event', full=True)
    class Meta:
        queryset = PluginEvents.objects.all()
        resource_name = 'plugin-events'
        allowed_methods = ['get']
        authentication = OpenAuthentication()
        authorization = OpenAuthorization()
        filtering = {
            'plugin_id': ALL
        }
        include_resource_uri = False