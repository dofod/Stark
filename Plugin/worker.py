__author__ = 'Saurabh'
from tastypie.exceptions import BadRequest
from models import Event, Trigger, Middleware
from api import PluginEvents, PluginTriggers

def applyTriggerMiddleware(trigger_name):
    '''
    Trigger Middleware is mutually exclusive for additional triggers i.e if the middleware causes more triggers,
    those triggers are not sent to the other middlewares. This is done so as to eliminate problem of circular trigger
    generation.
    '''
    trigger_list = {}
    if not Middleware.objects.all().exists():
        trigger_list[trigger_name] = True
    for middleware in Middleware.objects.all():
        altered_trigger = middleware.alter_trigger(trigger_name)
        if type(altered_trigger) is list:
            for trigger in altered_trigger:
                trigger_list[str(trigger)] = True
        elif type(altered_trigger) is str or type(altered_trigger) is unicode:
            trigger_list[str(altered_trigger)] = True
    return list(trigger_list)

def applyEventMiddleware(data):
    '''
    Event Middleware acts as a filter
    '''
    for middleware in Middleware.objects.filter(is_enabled=True):
        data = middleware.alter_event(data)
    return data

def onTrigger(trigger_name):
    trigger_list = applyTriggerMiddleware(trigger_name)
    for plugin in PluginTriggers.objects.filter(trigger_id__in = Trigger.objects.filter(name__in=trigger_list)):
    #for plugin in PluginTriggers.objects.filter(trigger__in=Trigger.objects.filter(name__in=trigger_list)):
        plugin.plugin.trigger(triggerName=trigger_name)

def onEvent(data):
    data = applyEventMiddleware(data)
    try:
        for plugin in PluginEvents.objects.filter(event=Event.objects.get(name=data['event'])):
            plugin.plugin.event(data=data)
    except KeyError:
        #Why not raise bad request? Because blank events intended for middlewares might be sent and they need to be accepted
        print 'Warning: No Event Fired - No event key was found'

