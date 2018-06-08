from functools import wraps

from .exception import UnauthorizedUser, UnsupportedHttpMethod

ß
def login_required(func):
    @wraps(func)
    def check_user_login(request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise UnauthorizedUser()
        return func(request, *args, **kwargs)
    return check_user_login


def allow_http_methods(method_list):
    """
    A clone of Django's require_http_methods decoration.
    We want a customized Exception.
    https://github.com/django/django/blob/master/django/views/decorators/http.py#L19
    Note: method list should be upper case.
    """
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if request.method not in method_list:
                raise UnsupportedHttpMethod(request.method)
            return func(request, *args, **kwargs)
        return inner
    return decorator


def redirect_after_signin(func):
    @wraps(func)
    def inner(request, *args, **kwargs):
        resp = func(request, *args, **kwargs)
        if not request.user.is_authenticated():
            resp.set_cookie('next', request.get_full_path())
        return resp

    return inner
