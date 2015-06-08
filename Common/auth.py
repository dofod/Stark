__author__ = 'Saurabh'
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization

class OpenAuthentication(Authentication):
    def is_authenticated(self, request, **kwargs):
        return True

class OpenAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):
        return object_list

    def create_detail(self, object_list, bundle):
        return True

    def update_list(self, object_list, bundle):
        return object_list

    def update_detail(self, object_list, bundle):
        return True

    def delete_list(self, object_list, bundle):
        return object_list

    def delete_detail(self, object_list, bundle):
        return True
