import json  # Compare performance between json and simplejson

from django.db.models.query import QuerySet

from common.func import convert_model_to_dict, convert_models_to_dict_list

API_SUCCESS_MESSAGE = "success"
API_SUCCESS_CODE = 0


class ApiResult(object):

    def __init__(self, data=None, code: int=API_SUCCESS_CODE, message: str=API_SUCCESS_MESSAGE):
        self.code = code
        self.message = message
        if data is None:
            self.data = None
            return
        if isinstance(data, (list, tuple)):
            self.data = convert_models_to_dict_list(data)
        elif isinstance(data, QuerySet):
            # Get data only when iterate QuerySet.
            results = list(data)
            self.data = convert_models_to_dict_list(results)
        else:
            self.data = convert_model_to_dict(data)

    def to_json(self):
        data = self.data
        if data is None:
            data = {}
        result = {
            'code': self.code,
            'message': self.message,
            'data': data
        }
        return json.dumps(result)
