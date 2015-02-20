__author__ = 'Saurabh'
from tastypie.resources import ModelResource, ALL
from tastypie.authentication import MultiAuthentication, ApiKeyAuthentication
from Common.resources import CORSModelResource
from Plugin.models import *
from .models import Device, DevicePluginRegistration
from .auth import OpenAuthorization, OpenAuthentication, DevicePasswordAuthentication, DeviceAuthorization, isDevice

class AddDeviceResource(ModelResource):
    class Meta:
        queryset = Device.objects.all()
        resource_name = 'add-device'
        allowed_methods = ['post']
        authentication = OpenAuthentication()
        authorization = OpenAuthorization()
    def hydrate(self, bundle):
        bundle.data['is_authorized'] = False
        return bundle

class DeviceResource(ModelResource):
    class Meta:
        queryset = Device.objects.all()
        resource_name = 'device'
        allowed_methods = ['get', 'patch', 'delete']
        authentication = MultiAuthentication(DevicePasswordAuthentication(), ApiKeyAuthentication())
        authorization = DeviceAuthorization()
    def dehydrate(self, bundle):
        del(bundle.data['password'])
        return bundle
    def hydrate(self, bundle):
        if isDevice(bundle.request):
            del(bundle.data['is_authorized'])
        return bundle

class DevicePluginRegistrationResource(ModelResource):
    class Meta:
        queryset = DevicePluginRegistration.objects.all()
        resource_name = 'register-plugin'
        #fields = ['user_id', 'key', 'resource_uri']
        allowed_methods = ['get', 'post']
        authentication = OpenAuthentication()
        authorization = OpenAuthorization()

    def obj_create(self, bundle, **kwargs):
        for plugin in Plugin.objects.filter(name__in=bundle.data['plugins']):
            DevicePluginRegistration.objects.create(plugin=plugin, device=Device.objects.get(name=bundle.data['device']))
        return bundle