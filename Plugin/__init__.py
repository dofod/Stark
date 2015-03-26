"""
Plugin is a python code that acts as a bridge between the automated devices and the framework. Plugins allow true
framework independant processing of events and triggers for the device. This is achieved by using a standard template
for developing plugins. The template is shown below:

requires_events = [<STRING define events that are required by the plugin]
requires_triggers = [<STRING define triggers that are required for the plugin here>]
requires_timers = [<DICT a python dictionary that states the time and the event to be executed>
	{
		'time':{'hour':<INT Hours 1-24>, 'minute':<INT Minutes 1-60>, 'second':<INT 1-60>},
		'event':<STRING Event to be passed>,
	}
]

def trigger(trigger_name):
    '''
    trigger_name <STRING Name of the trigger>
    '''
	pass

def event(data):
    '''
    data <DICT Contains the event name and additional data fields>
    data['event'] <STRING Name of the event>
    '''
	pass
"""