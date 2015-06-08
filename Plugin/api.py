__author__ = 'Saurabh'
import base64
import os
import importlib
import inspect
from tastypie.resources import Resource, Bundle, ModelResource, ALL, fields
from tastypie.exceptions import BadRequest
from tastypie.authentication import ApiKeyAuthentication, MultiAuthentication
from Stark.settings import scheduler
from Common.auth import OpenAuthentication, OpenAuthorization
from Common.resources import CORSModelResource
from Common.api import TastypieAPIObject
from Common.models import IncompleteDataException
from Device.auth import DeviceTokenAuthentication
from .models import Plugin, Event, Trigger, PluginEvents, PluginTriggers, Middleware
from .worker import onEvent, onTrigger

class PluginResource(ModelResource):
    """
    RESOURCE: /api/v1/plugin/
    DESCRIPTION: The plugin resource allows users and devices to add plugins to the automation system.
    AUTHENTICATION: Device and User can both access this resource.
    AUTHENTICATION GET PARAMETERS:
        For Device:
            devicename, auth_token
        For User:
            username, api_key
    POST DATA FORMAT:
    application/json
    {
        "name": <STRING plugin filename>,
        "file": <BASE64 ENCODED STRING file>
    }
    """
    class Meta:
        queryset = Plugin.objects.all()
        resource_name = 'plugin'
        allowed_methods = ['get', 'post']
        authentication = MultiAuthentication(DeviceTokenAuthentication(), ApiKeyAuthentication())
        authorization = OpenAuthorization()

    def inspectPlugin(self, pluginModule):
        """
        Check if plugin is properly formatted, ie. the core functions 'trigger' and 'event' are correctly defined with
        their arguments.
        """
        if 'trigger' not in dir(pluginModule) \
                or inspect.getargspec(pluginModule.trigger).args[0] != 'trigger_name' \
                or 'event' not in dir(pluginModule) \
                or inspect.getargspec(pluginModule.event).args[0] != 'data':
            return False
        return True

    def rollback(self, bundle):
        """
        Rollback the database and the filesystem if error occurs during plugin installation
        """
        Plugin.objects.get(name=bundle.data['name']).delete()
        os.remove(os.path.join(os.getcwd(), 'plugins', bundle.data['name']+'.py'))

    def obj_create(self, bundle, **kwargs):
        try:
            super(PluginResource, self).obj_create(bundle, **kwargs)
        except:
            if bundle.request.GET['force'] == 'true':
                pass
            else:
                raise BadRequest('Duplicate Plugin')

        plugin = Plugin.objects.get(name=bundle.data['name'])
        pluginFilePath = os.path.join(os.getcwd(), 'plugins', bundle.data['name']+'.py')
        pluginFile = open(pluginFilePath , 'w+')
        pluginFile.write(base64.b64decode(bundle.data['file']))
        pluginFile.close()
        pluginModule = importlib.import_module('plugins.'+bundle.data['name'])

        if not self.inspectPlugin(pluginModule):
            self.rollback(bundle)
            raise BadRequest('ERROR: Malformed plugin')

        try:
            for event in pluginModule.requires_events:
                PluginEvents.objects.get_or_create(plugin=plugin, event=Event.objects.get_or_create(name=event)[0])
        except AttributeError:
            print 'WARNING: requires_events not defined'

        try:
            for trigger in pluginModule.requires_triggers:
                PluginTriggers.objects.get_or_create(plugin=plugin, trigger=Trigger.objects.get_or_create(name=trigger)[0])
        except AttributeError:
            print 'WARNING: requires_triggers not defined'

        try:
            plugin = Plugin.objects.get(name=bundle.data['name'])
            for event in pluginModule.requires_timers:
                try:
                    scheduler.add_job(
                        func=getattr(pluginModule, 'event'),
                        args=[{'event':event['event']}],
                        trigger='cron',
                        month= event['time']['month'] if 'month' in event['time'] else '*',
                        day= event['time']['day'] if 'day' in event['time'] else '*',
                        hour=event['time']['hour'] if 'hour' in event['time'] else '*',
                        minute=event['time']['minute'] if 'minute' in event['time'] else '*',
                        second=event['time']['second'] if 'second' in event['time'] else '*',
                        name=plugin.name+'_'+event['event']
                    )
                except AttributeError:
                    self.rollback(bundle)
                    raise BadRequest('ERROR: Syntax Error in requires_timers')
                except:
                    self.rollback(bundle)
                    raise BadRequest('ERROR: In Scheduling')
        except AttributeError:
            print 'WARNING: requires_timers not defined'

        return bundle

    def dehydrate(self, bundle):
        bundle.data['events'] = [pluginEvent.event.name for pluginEvent in PluginEvents.objects.filter(plugin_id=bundle.obj.id)]
        bundle.data['triggers'] = [pluginTrigger.trigger.name for pluginTrigger in PluginTriggers.objects.filter(plugin_id=bundle.obj.id)]
        return bundle

class MiddlewareResource(ModelResource):
    class Meta:
        queryset = Middleware.objects.all()
        resource_name = 'middleware'
        allowed_methods = ['get', 'post', 'patch', 'delete']
        authentication = ApiKeyAuthentication()
        authorization = OpenAuthorization()

    def inspectMiddleware(self, middlewareModule):
        """
        Check if plugin is properly formatted, ie. the core functions 'filter_trigger' and 'filter_event' are correctly defined with
        their arguments.
        """
        if 'alter_trigger' not in dir(middlewareModule) \
                or inspect.getargspec(middlewareModule.alter_trigger).args[0] != 'trigger_name' \
                or 'alter_event' not in dir(middlewareModule) \
                or inspect.getargspec(middlewareModule.alter_event).args[0] != 'data':
            return False
        return True

    def rollback(self, bundle):
        """
        Rollback the database and the filesystem if error occurs during middleware installation
        """
        Middleware.objects.get(name=bundle.data['name']).delete()
        os.remove(os.path.join(os.getcwd(), 'middlewares', bundle.data['name']+'.py'))

    def obj_create(self, bundle, **kwargs):
        try:
            super(MiddlewareResource, self).obj_create(bundle, **kwargs)
        except:
            if bundle.request.GET['force'] == 'true':
                pass
            else:
                raise BadRequest('Duplicate Middleware')

        middlewareFilePath = os.path.join(os.getcwd(), 'middlewares', bundle.data['name']+'.py')
        middlewareFile = open(middlewareFilePath , 'w+')
        middlewareFile.write(base64.b64decode(bundle.data['file']))
        middlewareFile.close()
        middlewareModule = importlib.import_module('middlewares.'+bundle.data['name'])

        if not self.inspectMiddleware(middlewareModule):
            self.rollback(bundle)
            raise BadRequest('ERROR: Malformed Middleware')

        return bundle

    def obj_delete(self, bundle, **kwargs):
        os.remove(os.path.join(os.getcwd(), 'middlewares', Middleware.objects.get(id=int(kwargs['pk'])).name+'.py'))
        super(MiddlewareResource, self).obj_delete(bundle, **kwargs)


class EventResource(ModelResource):
    """
    RESOURCE: /api/v1/event
    DESCRIPTION: Events are processed here.
    AUTHENTICATION: Device can only access this resource.
    AUTHENTICATION GET PARAMETERS:
        For Device:
            devicename, auth_token
    POST DATA FORMAT:
    application/json
    {
        "event": <STRING Event name>,
        "data": <DICT Optional data to be passed to event>
    }
    """
    class Meta:
        queryset = Event.objects.all()
        resource_name = 'event'
        allowed_methods = ['post']
        authentication = DeviceTokenAuthentication()
        authorization = OpenAuthorization()
        include_resource_uri = False

    def obj_create(self, bundle, **kwargs):
        onEvent(bundle.data)
        return bundle

import datetime
class TriggerResource(ModelResource):
    """
    RESOURCE: /api/v1/trigger
    DESCRIPTION: Triggers are processed here.
    AUTHENTICATION: Device and User can both access this resource
    AUTHENTICATION GET PARAMETERS:
        For Device:
            devicename, auth_token
        For User:
            username, api_key
    POST DATA FORMAT:
    application/json
    {
        "trigger": <STRING Trigger>
    }
    """
    class Meta:
        queryset = Trigger.objects.all()
        resource_name = 'trigger'
        allowed_methods = ['post']
        authentication = MultiAuthentication(DeviceTokenAuthentication(), ApiKeyAuthentication())
        authorization = OpenAuthorization()
        include_resource_uri = False
    def obj_create(self, bundle, **kwargs):
        time = datetime.datetime.now()
        try:
            onTrigger(bundle.data['trigger'])
        except KeyError:
            print 'Error: No Trigger'
        print datetime.datetime.now()-time
        return bundle

class TimerResource(Resource):
    """
    RESOURCE: /api/v1/timer
    DESCRIPTION: Set a timer for an event to take place at a particular time. Note that the system supports cron-style
    format for setting up a timer task.
    AUTHENTICATION: Device and User can both access this resource.
    AUTHENTICATION GET PARAMETERS:
        For Device:
            devicename, auth_token
        For User:
            username, api_key
    POST DATA FORMAT:
    application/json
    {
        "event": <STRING Event name>,
        "month": <INT 1-12>,
        "day": <INT day 1-7>,
        "hour": <INT Hour 1-24>,
        "minute": <INT Minute 1-60>,
        "second": <INT Second 1-60>,
    }
    """
    job = fields.CharField(attribute='job', null=True)
    class Meta:
        resource_name = 'timer'
        allowed_methods = ['get', 'post']
        object_class = TastypieAPIObject
        authentication = MultiAuthentication(DeviceTokenAuthentication(), ApiKeyAuthentication())
        authorization = OpenAuthorization()
        include_resource_uri = False

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.pk
        else:
            kwargs['pk'] = bundle_or_obj.pk

        return kwargs

    def get_object_list(self, request):
        results = []
        for job in scheduler.get_jobs():
            result = TastypieAPIObject()
            result.job = job.name
            results.append(result)
        return results

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)

    def obj_create(self, bundle, **kwargs):
        try:
            event = Event.objects.get(name=bundle.data['event'])
        except KeyError:
            raise BadRequest('ERROR: No Event Defined')
        try:
            scheduler.add_job(
                func=onEvent,
                args=[bundle.data],
                trigger='cron',
                month= bundle.data['month'] if 'month' in bundle.data else '*',
                day= bundle.data['day'] if 'day' in bundle.data else '*',
                hour=bundle.data['hour'] if 'hour' in bundle.data else '*',
                minute=bundle.data['minute'] if 'minute' in bundle.data else '0',
                second=bundle.data['second'] if 'second' in bundle.data else '0',
                name=event.name
            )
        except AttributeError:
            raise BadRequest('ERROR: Syntax Error in timer')
        return bundle

    def obj_delete_list(self, bundle, **kwargs):
        pass

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