from django.contrib import auth
from django.contrib.auth.backends import ModelBackend
from app.models import MyUser


class AccessTokenMiddleware(object):
    def process_request(self, request):
        try:
            access_token = request.GET['access_token']
        except KeyError:
            return
        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        if hasattr(request, 'user') and request.user.is_authenticated():
            return

        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        user = auth.authenticate(access_token=access_token)
        if user:
            request.user = user
            auth.login(request, user)


class AccessTokenBackend(ModelBackend):
    def authenticate(self, access_token, **kwargs):
        res = MyUser.objects.get(access_token=access_token)
        return res.user if res is not None else None
