from django.http.response import HttpResponse
import json
import datetime
from django.db.models.query import QuerySet
from django.core.serializers import serialize, deserialize
from json.encoder import JSONEncoder
from django.db.models.base import Model


class ComplexEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Model):
            return json.loads(serialize('json', [obj])[1:-1])['fields']
        if isinstance(obj, QuerySet):
            obj = obj.values()
            obj = list(obj)
            return json.loads(json.dumps(obj, cls=ComplexEncoder))
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M')
        if isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

    def jsonBack(self, json):
        if json[0] == '[':
            return deserialize('json', json)
        else:
            return deserialize('json', '[' + json + ']')


class GENERAL_ERRORS:
    ERROR_SUCCESS = 0
    ERROR_BAD_ARGS = 4000
    ERROR_NO_PERMISSION = 4001
    ERROR_INTERNAL = 4002
    ERROR_NOT_FOUND = 4004

    ERRO_STRING = {
        ERROR_SUCCESS: 'success',
        ERROR_BAD_ARGS: 'argument wrong',
        ERROR_NO_PERMISSION: 'not permitted',
        ERROR_INTERNAL: 'internal error',
        ERROR_NOT_FOUND: 'object not found',
    }

    @classmethod
    def default_error_message(cls, code):
        try:
            return GENERAL_ERRORS.ERRO_STRING[code]
        except:
            return 'unknown error'


def general_json_response(code=0, detail=None):
    if detail is None:
        detail = GENERAL_ERRORS.default_error_message(code)
    res = {'code': code, 'details': detail}
    return HttpResponse(json.dumps(res, cls=ComplexEncoder),\
                         content_type="application/json")
