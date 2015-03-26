__author__ = 'Saurabh'
from django.contrib.auth.admin import User
from django.db import models
from tastypie.models import create_api_key, ApiKey
from tastypie.resources import ModelResource
from tastypie.authentication import ApiKeyAuthentication
from Common.resources import CORSModelResource
from Common.auth import OpenAuthentication, OpenAuthorization
from .auth import PasswordAuthentication, ApiKeyAuthorization

class AddUserResource(ModelResource):
    """
    RESOURCE: /api/v1/add-user
    DESCRIPTION: Users are added here.
    AUTHENTICATION: Anyone can access this resource.
    POST DATA FORMAT:
    application/json
    {
        "username": <STRING Username>,
        "password": <STRING Password>,
        "email": <STRING Email>
    }
    """
    class Meta:
        queryset = User.objects.all()
        resource_name = 'add-user'
        allowed_methods = ['post']
        include_resource_uri = False
        authentication = OpenAuthentication()
        authorization = OpenAuthorization()

    def obj_create(self, bundle, **kwargs):
        bundle = super(AddUserResource, self).obj_create(bundle, **kwargs)
        bundle.obj.set_password(bundle.data['password'])
        bundle.obj.save()
        return bundle

class UserResource(ModelResource):
    """
    RESOURCE: /api/v1/user/
    DESCRIPTION: Get information on users
    AUTHENTICATION: Only users can access this resource
    AUTHENTICATION GET PARAMETERS:
        For User:
            username, api_key
    """
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        allowed_methods = ['get']
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'last_login'
        ]
        excludes = ['username']
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = OpenAuthorization()
    def dehydrate(self, bundle):
        bundle.data['username'] = bundle.obj.username
        return bundle

class ApiKeyResource(ModelResource):
    """
    RESOURCE: /api/v1/api-key/
    DESCRIPTION: Get api-key for user
    AUTHENTICATION: Only users can access this resource
    AUTHENTICATION GET PARAMETERS:
        For User:
            username, password
    """
    class Meta:
        queryset = ApiKey.objects.all()
        resource_name = 'api-key'
        allowed_methods = ['get']
        include_resource_uri = False
        authentication = PasswordAuthentication()
        authorization = ApiKeyAuthorization()

models.signals.post_save.connect(create_api_key, sender=User)