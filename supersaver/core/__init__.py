from logging import getLogger

__internal__ = {
    'logger': getLogger('core.internal')
}


def setup_logger(logger):
    __internal__['logger'] = logger


def get_logger():
    return __internal__['logger']