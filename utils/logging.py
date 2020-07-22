import logging
from jog import JogFormatter
from time import perf_counter

REQUEST_LOG_FORMAT = '%(remote_address)s %(request_protocol)s %(request_method)s %(request_path)s %(status_code)d %(elapsed_time)dms %(content_length)dB'
REQUEST_ERROR_LOG_FORMAT = '%(remote_address)s %(request_protocol)s %(request_method)s %(request_path)s'


def wsgi_log_middleware(application, request_logger=None):
    """WSGI middleware to provide structured logging for requests."""

    if request_logger is None:
        request_logger = logging.getLogger('wsgi_request')
    application = application

    def wsgi_log_wrapper(environ, start_response):
        start = perf_counter()

        log_vals = {
            'remote_address': environ.get('REMOTE_ADDR'),
            'request_protocol': environ.get('SERVER_PROTOCOL'),
            'request_method': environ.get('REQUEST_METHOD'),
            'request_path': environ.get('PATH_INFO'),
        }

        status_codes = []
        content_lengths = []

        # Wrap start_response to enable extracting the status code,
        # content-length header, and exc_info
        def custom_start_response(status, response_headers, exc_info=None):
            # Call the actual start_response first, as it may error if it has
            # been called incorrectly. We only want to store values from
            # successful calls.
            retval = start_response(status, response_headers, exc_info)

            status_codes.append(int(status.partition(' ')[0]))
            for name, value in response_headers:
                if name.lower() == 'content-length':
                    content_lengths.append(int(value))
                    break

            # NOTE: We're not supposed to hold a reference to exc_info:
            #       https://www.python.org/dev/peps/pep-3333/#the-start-response-callable
            #       Have to log the exception here, rather than once the request is done.
            if exc_info:
                try:
                    request_logger.exception(REQUEST_ERROR_LOG_FORMAT, log_vals,
                                             exc_info=exc_info)
                finally:
                    exc_info = None

            return retval

        retval = application(environ, custom_start_response)

        # NOTE: This won't include data written via the write() function
        #       returned by start_response() if no `content-length` header
        #       was provided.
        content_length = content_lengths[-1] if content_lengths else len(b''.join(retval))

        log_vals.update({
            'status_code': status_codes[-1],
            'elapsed_time': int((perf_counter() - start) * 1000),
            'content_length': content_length,
        })
        request_logger.info(REQUEST_LOG_FORMAT, log_vals)

        return retval

    return wsgi_log_wrapper


def configure_logging(json=False, verbose=False, log_level='INFO'):
    log_handler = logging.StreamHandler()
    log_format = '[%(asctime)s] %(name)s.%(levelname)s %(threadName)s %(module)s.%(funcName)s %(filename)s:%(lineno)s %(message)s'
    formatter = JogFormatter(log_format) if json else logging.Formatter(log_format)
    log_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.DEBUG if verbose else getattr(logging, log_level),
        handlers=[log_handler]
    )
    logging.captureWarnings(True)
