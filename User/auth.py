__author__ = 'Saurabh'
from django.contrib.auth.admin import User
from django.contrib.auth import authenticate
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from django.core.exceptions import ObjectDoesNotExist
class PasswordAuthentication(Authentication):
    def is_authenticated(self, request, **kwargs):
        try:
            user = authenticate(username=request.GET['username'], password=request.GET['password'])
            if user:
                setattr(request, 'user', user)
                return True
            else:
                return False
        except:
            return False

class ApiKeyAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        return object_list.filter(user_id=bundle.request.user.id)

    def read_detail(self, object_list, bundle):
        if object_list[0].user_id == bundle.request.user.id:
            return True
        return False
