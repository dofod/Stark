from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
from tastypie.api import Api
from Device.api import DeviceResource, DevicePluginRegistrationResource, AddDeviceResource
from User.api import UserResource, AddUserResource, ApiKeyResource
from Plugin.api import PluginResource, EventResource, TriggerResource, PluginEventsResource, PluginTriggersResource

apiV1 = Api(api_name='v1')

apiV1.register(DeviceResource())
apiV1.register(AddDeviceResource())
apiV1.register(DevicePluginRegistrationResource())

apiV1.register(UserResource())
apiV1.register(AddUserResource())
apiV1.register(ApiKeyResource())

apiV1.register(PluginResource())
apiV1.register(EventResource())
apiV1.register(TriggerResource())
apiV1.register(PluginTriggersResource())
apiV1.register(PluginEventsResource())

urlpatterns = patterns('',
    url(r'^api/', include(apiV1.urls)),
    # Examples:
    # url(r'^$', 'Stark.views.home', name='home'),
    # url(r'^Stark/', include('Stark.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
