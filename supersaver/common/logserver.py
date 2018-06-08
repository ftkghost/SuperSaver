import os
import struct
import pickle
import logging
import logging.config
import logging.handlers
from socketserver import StreamRequestHandler, ThreadingTCPServer

# Ref: https://docs.python.org/3.5/howto/logging-cookbook.html?highlight=threadingtcpserver

# Log server configurations

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, 'logs'))
if not os.path.isdir(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_SERVER_HOST = 'localhost'
LOG_SERVER_PORT = logging.handlers.DEFAULT_TCP_LOGGING_PORT
LOG_SERVER_LOGGER_NAME = 'log_server.log'
LOG_SERVER_INTERNAL_LOG_FILE = os.path.join(LOG_DIR, 'log_server_internal.log')

INCOMING_SOURCE_LOGGER_NAME = 'sca.service.logger'
INCOMING_SOURCE_LOG_FILE = os.path.join(LOG_DIR, 'sca-service.log')
print("<Note>: Make sure the incoming source logger name '{0}' is same as the client side logger name.".format(INCOMING_SOURCE_LOGGER_NAME))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        # See: http://docs.python.org/library/logging.html#logrecord-attributes
        'simple': {
            'format': '%(levelname)s\t%(asctime)s\t%(filename)s\t%(funcName)s\t%(lineno)d\t%(message)s'
        },
        'verbose': {
            'format': (
                '%(levelname)s\t%(asctime)s\t%(ip)s-%(source)s\t%(process)d:%(thread)d\t'
                '%(filename)s\t%(funcName)s\t%(lineno)d\t%(message)s'
            )
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        # FIXME: Remember backup logs
        'incoming_source_log_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': INCOMING_SOURCE_LOG_FILE,
            'when': 'H',
            'interval': 12,
            'backupCount': 60,  # Save logs for latest 60/(24/12) = 30 days
            'encoding': 'utf-8',
            'delay': True,
            'utc': True,
            'formatter': 'verbose',
        },
        'log_server_log_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_SERVER_INTERNAL_LOG_FILE,
            'maxBytes': 52428800,  # 50 MB
            'encoding': 'utf-8',
            'delay': True,
            'formatter': 'simple',
        }
    },
    'loggers': {
        INCOMING_SOURCE_LOGGER_NAME: {
            'handlers': ['incoming_source_log_handler'],
            'level': 'DEBUG',
        },
        LOG_SERVER_LOGGER_NAME: {
            'handlers': ['log_server_log_handler'],
            'level': 'DEBUG',
        }
    }
}


class LogRecordStreamHandler(StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while 1:
            try:
                chunk = self.connection.recv(4)
                if len(chunk) < 4:
                    break
                slen = struct.unpack(">L", chunk)[0]
                chunk = self.connection.recv(slen)
                while len(chunk) < slen:
                    chunk = chunk + self.connection.recv(slen - len(chunk))
                obj = self.unpickle(chunk)
                record = logging.makeLogRecord(obj)
                self.handleLogRecord(record)
            except:
                logger = logging.getLogger(LOG_SERVER_LOGGER_NAME)
                logger.exception("Log failed.")

    def unpickle(self, data):
        return pickle.loads(data)

    def handleLogRecord(self, record):
        # if a name is specified, we use the named logger rather than the one
        # implied by the record.

        logger = logging.getLogger(record.name)

        # N.B. EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering. If you want
        # to do filtering, do it at the client end to save wasting
        # cycles and network bandwidth!
        try:
            # ignore port
            ip_address, port = self.connection.getpeername()
        except:
            ip_address = 'unknown'
        record.ip = ip_address  # LoggerAdapter does not have method handler()
        logger.handle(record)


class LogRecordSocketReceiver(ThreadingTCPServer):
    """Simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = 1

    def __init__(
            self, host=LOG_SERVER_HOST, port=LOG_SERVER_PORT,
            handler=LogRecordStreamHandler):
        ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1

    def serve_until_stopped(self):
        import select
        abort = 0
        while not abort:
            try:
                rd, wr, ex = select.select([self.socket.fileno()], [], [], self.timeout)
                if rd:
                    self.handle_request()
                abort = self.abort
            except:
                logger = logging.getLogger(LOG_SERVER_LOGGER_NAME)
                logger.exception('Critical log server failure.')
                # Flush all logs
                logging.shutdown()
                raise


def main():
    logging.config.dictConfig(LOGGING)
    tcp_server = LogRecordSocketReceiver()

    logger = logging.getLogger(LOG_SERVER_LOGGER_NAME)
    logger.info("TCP log server started.")
    tcp_server.serve_until_stopped()
    logger.info("TCP log server stopped.")


if __name__ == "__main__":
    main()
