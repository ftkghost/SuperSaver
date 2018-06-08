import logging
import logging.handlers
from sca.sca_settings import SCA_SERVICE_LOGGER_NAME


def _get_socket_logger(source):
    logger = logging.getLogger(SERVICE_LOGGER_NAME)
    for handler in logger.handlers:
        if isinstance(handler, logging.handlers.SocketHandler):
            handler.closeOnError = True
    return logging.LoggerAdapter(logger, {'source': source})


def get_service_logger():
    return _get_socket_logger('web')


def get_backend_logger():
    return _get_socket_logger('backend')


def get_tools_logger():
    return _get_socket_logger('tools')
