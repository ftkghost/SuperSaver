import json
import traceback
from http import HTTPStatus
from common.func import convert_model_to_dict


class Error(Exception):
    def __init__(self, message, inner_exception=None):
        super().__init__(message)
        self.message = message
        # TODO: Distinguish public error message and internal error message.
        # Use internal error message for logging to improve security, public error message can be sent back to client.
        self.public_message = message
        self.inner_exception = inner_exception


class ErrorCode:
    NewVersionAvailable = 0, HTTPStatus.UNSUPPORTED_MEDIA_TYPE.value

    # Error name = Error Code, Http Status Code
    UnknownError = 9999, HTTPStatus.SERVICE_UNAVAILABLE.value
    UnsupportedVersion = 10000, HTTPStatus.UNSUPPORTED_MEDIA_TYPE.value
    UnsupportedHttpMethod = 10001, HTTPStatus.BAD_REQUEST.value
    InvalidServerStatus = 10002, HTTPStatus.INTERNAL_SERVER_ERROR.value
    UnauthorizedUser = 11000, HTTPStatus.FORBIDDEN.value
    InvalidEmailLogin = 11001, HTTPStatus.FORBIDDEN.value
    InvalidExtServiceLogin = 11002, HTTPStatus.FORBIDDEN.value
    InvalidExtServiceLoginWithEmailOccupied = 11003, HTTPStatus.FORBIDDEN.value
    PermissionDenied = 11004, HTTPStatus.FORBIDDEN.value
    InvalidOperation = 11005, HTTPStatus.FORBIDDEN.value
    InactiveUser = 11006, HTTPStatus.FORBIDDEN.value
    RegisterFailure = 11007, HTTPStatus.FORBIDDEN.value
    UnauthorizedDevice = 11008, HTTPStatus.FORBIDDEN.value
    InvalidInput = 20001, HTTPStatus.BAD_REQUEST.value
    InvalidSignature = 20002, HTTPStatus.BAD_REQUEST.value
    ObjectNotFound = 21000, HTTPStatus.NOT_FOUND.value
    UniqueTokenConflict = 21000, HTTPStatus.CONFLICT.value
    TokenExpired = 21001, HTTPStatus.UNAUTHORIZED.value


class ApiError(Error):
    """
    API Exception which returned to client.
    Notes:
        Don't put sensitive data in error message.
    """
    def __init__(self, message: str, sca_error_code: int, http_status_code: int=200, context=None):
        super().__init__(message)
        self.error_code = sca_error_code
        self.message = message
        self.http_status_code = http_status_code
        self.context = context

    def to_json(self):
        data = None
        if self.context is not None and isinstance(self.context, dict) and 'data' in self.context:
            data = self.context['data']

        result = {
            'code': self.error_code,
            'message': self.message
        }
        if data is not None:
            result['extra'] = convert_model_to_dict(data)
        return json.dumps(result)


class UnknownError(ApiError):
    def __init__(self, message='', context=None):
        error = 'Unexpected error encounters. ' + message
        super().__init__(error, *ErrorCode.UnknownError, context=context)


class UnsupportedVersion(ApiError):
    def __init__(self, version, context=None):
        error = 'Version {0} is not supported, please upgrade your app to latest version. '.format(version)
        super().__init__(error, *ErrorCode.UnsupportedVersion, context=context)


class UnsupportedHttpMethod(ApiError):
    def __init__(self, method, context=None):
        error = 'Unsupported http method {0}'.format(method)
        super().__init__(error, *ErrorCode.UnsupportedHttpMethod, context=context)


class InvalidServerStatus(ApiError):
    def __init__(self, message='', context=None):
        error = 'Invalid server status. ' + message
        super().__init__(error, *ErrorCode.InvalidServerStatus, context=context)


class UnauthorizedUser(ApiError):
    def __init__(self, message='', context=None):
        error = 'User is not authorized. ' + message
        super().__init__(error, *ErrorCode.UnauthorizedUser, context=context)


class InvalidEmailLogin(ApiError):
    def __init__(self, message='', context=None):
        error = 'Invalid login username or password. ' + message
        super().__init__(error, *ErrorCode.InvalidEmailLogin, context=context)


class InvalidExtServiceLogin(ApiError):
    def __init__(self, service, message='', context=None):
        error = 'Invalid {0} login with token. {1}'.format(service, message)
        super().__init__(error, *ErrorCode.InvalidExtServiceLogin, context=context)


class InvalidExtServiceLoginWithEmailOccupied(ApiError):
    def __init__(self, service, message='', context=None):
        error = 'Invalid {0} login with token, ext service account email is occupied. {1}'.format(service, message)
        super().__init__(error, *ErrorCode.InvalidExtServiceLoginWithEmailOccupied, context=context)


class PermissionDenied(ApiError):
    def __init__(self, message='', context=None):
        error = 'Permission denied. ' + message
        super().__init__(error, *ErrorCode.PermissionDenied, context=context)


class InvalidOperation(ApiError):
    def __init__(self, message='', context=None):
        error = 'Invalid operation. ' + message
        super().__init__(error, *ErrorCode.InvalidOperation, context=context)


class InactiveUser(ApiError):
    def __init__(self, message='', context=None):
        error = 'Inactive user. ' + message
        super().__init__(error, *ErrorCode.InactiveUser, context=context)


class RegisterFailure(ApiError):
    def __init__(self, message='', context=None):
        error = 'Failed to register user. ' + message
        super().__init__(error, *ErrorCode.RegisterFailure, context=context)


class UnauthorizedDevice(ApiError):
    def __init__(self, message='', context=None):
        error = 'Unauthorized device. ' + message
        super().__init__(error, *ErrorCode.UnauthorizedDevice, context=context)


class InvalidInput(ApiError):
    def __init__(self, message, context=None):
        super().__init__(message, *ErrorCode.InvalidInput, context=context)


class InvalidSignature(ApiError):
    def __init__(self, message='', context=None):
        error = 'Invalid signature. ' + message
        super().__init__(error, *ErrorCode.InvalidSignature, context=context)


class ObjectNotFound(ApiError):
    def __init__(self, message='', context=None):
        error = 'Object not found. ' + message
        super().__init__(error, *ErrorCode.ObjectNotFound, context=context)


class UniqueTokenConflict(ApiError):
    def __init__(self, message='', context=None):
        error = 'Unique token conflicts. ' + message
        super().__init__(error, *ErrorCode.UniqueTokenConflict, context=context)


class TokenExpired(ApiError):
    def __init__(self, message='', context=None):
        error = 'Token expired. ' + message
        super().__init__(error, *ErrorCode.TokenExpired, context=context)


# Internal Errors, do not show these error to client.
class InternalException(Exception):
    def __init__(self, message, inner_ex=None):
        self.inner_exception = inner_ex
        self.inner_exception_trace = None
        if inner_ex:
            self.inner_exception_trace = traceback.format_exc()
        super().__init__(message)

    def __str__(self):
        if self.inner_exception:
            return 'Error: {0}\nInner exception:\n{1}'.format(self.message, self.inner_exception_trace)
        else:
            return 'Error: {0}'.format(self.message)
