from django.http import HttpResponse, HttpResponseServerError

from ..exception import ApiError, UnknownError
from ..result import ApiResult
from core import get_logger

CONTENT_TYPE_JSON = "application/json"


class ApiResponseMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if isinstance(response, ApiResult):
            content = response.to_json()
            return HttpResponse(content, content_type=CONTENT_TYPE_JSON)
        elif isinstance(response, HttpResponse):
            return response
        else:
            # Response middleware happens after view & exception middleware.
            # If there are unhandled exception happened in view function, code flow may not reach here.
            return HttpResponseServerError("Unknown request " + str(request))


class ApiErrorMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = get_logger()

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # Log debug information and dump request.
        if isinstance(exception, ApiError):
            caught_exception = exception
        else:
            if request.get_full_path().startswith('/api'):
                logger = self.logger
                if logger:
                    logger.error('Unknown error. ' + str(exception))
                caught_exception = UnknownError()
            else:
                return None
        content = caught_exception.to_json()
        return HttpResponse(content, content_type=CONTENT_TYPE_JSON, status=caught_exception.http_status_code)
