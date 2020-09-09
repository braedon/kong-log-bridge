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


@contextmanager
def nice_shutdown(shutdown=sys.exit, shutdown_signals=(signal.SIGINT, signal.SIGTERM)):
    """
    Logs shutdown signals nicely, and calls a shutdown function.

    Installs new handlers for the shutdown signals (SIGINT and SIGTERM by default).
    The original handlers are restored before returning.
    """

    shutting_down = False

    def sig_handler(signum, _):
        nonlocal shutting_down

        if shutting_down:
            log.warning('Received signal %(signal)s while shutting down. Aborting.',
                        {'signal': signal.Signals(signum).name})
            sys.exit()

        shutting_down = True

        log.info('Received signal %(signal)s. Shutting down.',
                 {'signal': signal.Signals(signum).name})
        shutdown()

    # Setup new shutdown handlers, storing the old ones for later.
    old_handlers = {}
    for sig in shutdown_signals:
        old_handlers[sig] = signal.signal(sig, sig_handler)

    try:
        yield  # Wrapped code block run here

    finally:
        # Restore the old handlers
        for sig, old_handler in old_handlers.items():
            signal.signal(sig, old_handler)
