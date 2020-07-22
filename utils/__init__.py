import functools
import logging
import signal
import sys

from contextlib import contextmanager

log = logging.getLogger(__name__)


def log_exceptions(exit_on_exception=False):
    """
    Logs any exceptions raised.

    By default, exceptions are then re-raised. If set to exit on exception,
    sys.exit(1) is called instead.
    """

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                if exit_on_exception:
                    log.exception('Unrecoverable exception encountered. Exiting.')
                    sys.exit(1)
                else:
                    log.exception('Exception encountered.')
                    raise

        return wrapper

    return decorator


def nice_shutdown(shutdown_signals=(signal.SIGINT, signal.SIGTERM)):
    """
    Logs shutdown signals nicely.

    Installs handlers for the shutdown signals (SIGINT and SIGTERM by default)
    that log the signal that has been received, and then raise SystemExit.
    The original handlers are restored before returning.
    """

    def sig_handler(signum, _):
        log.info('Received signal %(signal)s.',
                 {'signal': signal.Signals(signum).name})
        # Raise SystemExit to bypass (most) try/except blocks.
        sys.exit()

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Setup new shutdown handlers, storing the old ones for later.
            old_handlers = {}
            for sig in shutdown_signals:
                old_handlers[sig] = signal.signal(sig, sig_handler)

            try:
                return func(*args, **kwargs)

            finally:
                # Restore the old handlers
                for sig, old_handler in old_handlers.items():
                    signal.signal(sig, old_handler)

        return wrapper

    return decorator


@contextmanager
def graceful_cleanup(func, *args, **kwargs):
    """
    Context manager to help gracefully clean up after a code block.

    The graceful cleanup function is run if the code block has exited without
    an error. This could be it returning normally, or raising SystemExit with
    a falsy (non-error) code.
    """

    try:
        yield  # Wrapped code block run here
    except SystemExit as e:
        # A truthy exit code indicates an error, so we should reraise.
        if e.code:
            raise

    log.debug('Non-error exit. Running graceful cleanup function.')
    func(*args, **kwargs)
