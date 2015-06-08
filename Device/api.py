__author__ = 'Saurabh'
from tastypie.resources import ModelResource
from tastypie.authentication import MultiAuthentication, ApiKeyAuthentication
from Plugin.models import *
from .models import Device, DevicePluginRegistration
from .auth import OpenAuthorization, OpenAuthentication, DevicePasswordAuthentication, DeviceAuthorization, isDevice

class AddDeviceResource(ModelResource):
    """
    RESOURCE: /api/v1/add-device/
    DESCRIPTION: Add a device.
    AUTHENTICATION: Authentication is kept open, However the device is not activated by default. Any request made by the
    device will not be processed by the framework unless user explicity allows the device via /api/v1/device resource
    which has user authentication.
    POST DATA FORMAT:
    application/json
    {
        "name": <STRING Name of the device>,
        "password": <STRING Password for the device, known only by the device>
    }
    """
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
    """
    RESOURCE: /api/v1/device/<id>
    DESCRIPTION:
        For users: Get information about a device, allow/block or delete a device
        For devices: Get information about itself, get authorization token.
    AUTHENTICATION: Both users and devices can access this resource. However there are some differences in authorization.
    A device is only limited to itself and cannot access list of other devices, neither can it set the is_authorized flag
    which allows processing of the device's requests by the framework. A user can access list of devices and can set the
    is_authorized flag.
    AUTHENTICATION GET PARAMETERS:
        For User:
            username, api_key
        For Device:
            devicename, key
    PATCH-DATA FORMAT:
    application/json
    {
        is_authorized: <BOOLEAN Set the flag to allow device, unset it to block the device>
    }
    """
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