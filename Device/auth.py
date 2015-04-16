__author__ = 'Saurabh'
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from tastypie.authentication import Authentication, ApiKeyAuthentication, HttpUnauthorized
from tastypie.authorization import Authorization
from Common.auth import OpenAuthorization, OpenAuthentication
from .models import Device

def isDevice(request):
    try:
        getattr(request, 'device')
        return True
    except AttributeError:
        return False


class DeviceTokenAuthentication(Authentication):
    cache = {}
    def is_authenticated(self, request, **kwargs):
        devicename = request.GET.get('devicename') or request.POST.get('devicename')
        authToken = request.GET.get('auth_token') or request.POST.get('auth_token')
        try:
            cacheAuthToken = self.cache[devicename]
            if cacheAuthToken == authToken:
                return True
        except:
            pass
        try:
            device = Device.objects.get(name=devicename, auth_token=authToken)
            if device.is_authorized:
                self.cache[devicename] = authToken
                return True
            return False
        except:
            return False

class DevicePasswordAuthentication(Authentication):
    def is_authenticated(self, request, **kwargs):
        devicename = request.GET.get('devicename') or request.POST.get('devicename')
        password = request.GET.get('key') or request.POST.get('key')
        try:
            device = Device.objects.get(name=devicename)
            if device and device.verifyPassword(password=password):
                setattr(request, 'device', device)
                return True
        except:
            return False

class DeviceAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        if isDevice(bundle.request):
            return object_list.filter(id=bundle.request.device.id)
        else:
            return object_list

    def read_detail(self, object_list, bundle):
        if isDevice(bundle.request):
            return bundle.request.device.id == object_list[0].id
        else:
            return True

    def create_list(self, object_list, bundle):
        return object_list

    def create_detail(self, object_list, bundle):
        return False

    def update_list(self, object_list, bundle):
        return object_list

    def update_detail(self, object_list, bundle):
        if isDevice(bundle.request):
            return False
        return True

    def delete_list(self, object_list, bundle):
        if isDevice(bundle.request):
            return object_list.filter(id=bundle.request.device.id)
        else:
            return object_list

    def delete_detail(self, object_list, bundle):
        if isDevice(bundle.request):
            return bundle.request.device.id == object_list[0].id
        else:
            return True