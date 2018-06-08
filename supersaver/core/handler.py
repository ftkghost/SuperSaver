import json

from core import get_logger


class RequestHandler:
    def __init__(self, request):
        self.request = request
        self.logger = get_logger()

    def get_post_json(self):
        request = self.request
        if getattr(request, 'POST_JSON', None) is None:
            if 'CONTENT_TYPE' in request.META:
                content_type = request.META['CONTENT_TYPE']
                if content_type.lower().find('application/json') != -1:
                    try:
                        request.POST_JSON = json.loads(request.body.decode('utf-8'))
                    except Exception as e:
                        self.logger.warning("Failed to parse json from POST request body.")
        return getattr(request, 'POST_JSON', {})
