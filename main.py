from gevent import monkey; monkey.patch_all()

import bottle
import click
import gevent
import kong_log_bridge
import logging
import sys
import time

from elasticsearch import Elasticsearch
from gevent.pool import Pool

from utils import log_exceptions, nice_shutdown
from utils.logging import configure_logging, wsgi_log_middleware

from kong_log_bridge import construct_app

CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help']
}

log = logging.getLogger(__name__)

# Use an unbounded pool to track gevent greenlets so we can
# wait for them to finish on shutdown.
gevent_pool = Pool()


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--convert-ts', default=False, is_flag=True,
              help='Convert UNIX timestamps to RFC3339 datetime strings.')
@click.option('--convert-qs-bools', default=False, is_flag=True,
              help='Convert `True` boolean values in request querystrings to empty strings.')
@click.option('--hash-ip', default=False, is_flag=True,
              help='Hash the client ip address.')
@click.option('--hash-auth', default=False, is_flag=True,
              help='Hash the Authorization request header.')
@click.option('--hash-cookie', default=False, is_flag=True,
              help='Hash the Cookie request header and Set-Cookie response header.')
@click.option('--hash-path', multiple=True,
              help='A path to a field to hash. '
                   'Specify multiple paths by providing the option multiple times.')
@click.option('--null-path', multiple=True,
              help='A path to a field to set to null. '
                   'Specify multiple paths by providing the option multiple times.')
@click.option('--limit-request-headers', default=100,
              help='Limit the number of request headers (default=100)')
@click.option('--limit-request-querystring', default=100,
              help='Limit the number of request querystring parameters (default=100)')
@click.option('--expose-ip', multiple=True,
              help='Hash of an IP to expose i.e. include the raw IP in logs. '
                   'Specify multiple IP hashes by providing the option multiple times.')
@click.option('--es-node', '-e', required=True, multiple=True,
              help='Address of a node in a Elasticsearch cluster to send logs to. '
                   'Specify multiple nodes by providing the option multiple times. '
                   'A port can be provided if non-standard (9200) e.g. es1:9999.')
@click.option('--es-index', default='<kong-requests-{now/d}>',
              help='Elasticsearch Kong request log index. (default=<kong-requests-{now/d}>)')
@click.option('--es-ca-certs',
              help='Path to a CA certificate bundle. '
                   'Can be absolute, or relative to the current working directory. '
                   'If not specified, Elasticsearch SSL certificate verification is disabled.')
@click.option('--es-client-cert',
              help='Path to a SSL client certificate. '
                   'Can be absolute, or relative to the current working directory. '
                   'If not specified, Elasticsearch SSL client authentication is disabled.')
@click.option('--es-client-key',
              help='Path to a SSL client key. '
                   'Can be absolute, or relative to the current working directory. '
                   'Must be specified if "--es-client-cert" is provided.')
@click.option('--es-basic-user',
              help='Username for basic authentication with Elasticsearch nodes. '
                   'If not specified, Elasticsearch basic authentication is disabled.')
@click.option('--es-basic-password',
              help='Password for basic authentication with Elasticsearch nodes. '
                   'Must be specified if "--es-basic-user" is provided.')
@click.option('--es-max-connections', default=10,
              help='Maximum simultaneous connections to Elasticsearch. (default=10)')
@click.option('--port', '-p', default=8080,
              help='Port to serve API on (default=8080)')
@click.option('--shutdown-sleep', default=10,
              help='How many seconds to sleep during graceful shutdown. (default=10)')
@click.option('--shutdown-wait', default=10,
              help='How many seconds to wait for active connections to close during graceful '
                   'shutdown (after sleeping). (default=10)')
@click.option('--json', '-j', default=False, is_flag=True,
              help='Log in json')
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
              help='Detail level to log. (default: INFO)')
@click.option('--verbose', '-v', default=False, is_flag=True,
              help='Turn on verbose (DEBUG) logging. Overrides --log-level.')
@log_exceptions(exit_on_exception=True)
def main(**options):

    def shutdown():
        kong_log_bridge.SERVER_READY = False

        def wait():
            # Sleep for a few seconds to allow for race conditions between sending
            # the SIGTERM and load balancers stopping sending traffic here.
            log.info('Shutdown: Sleeping %(sleep_s)s seconds.',
                     {'sleep_s': options['shutdown_sleep']})
            time.sleep(options['shutdown_sleep'])

            log.info('Shutdown: Waiting up to %(wait_s)s seconds for connections to close.',
                     {'wait_s': options['shutdown_sleep']})
            gevent_pool.join(timeout=options['shutdown_wait'])

            log.info('Shutdown: Exiting.')
            sys.exit()

        # Run in greenlet, as we can't block in a signal hander.
        gevent.spawn(wait)

    configure_logging(json=options['json'], verbose=options['verbose'],
                      log_level=options['log_level'])

    # Elasticsearch logs all requests at (at least) INFO level. Disable if log level isn't DEBUG.
    if not (options['log_level'] == 'DEBUG' or options['verbose']):
        logging.getLogger('elasticsearch').setLevel(logging.WARNING)

    if options['es_basic_user'] and not options['es_basic_password']:
        click.BadOptionUsage('es_basic_user', 'Username provided with no password.')
    elif not options['es_basic_user'] and options['es_basic_password']:
        click.BadOptionUsage('es_basic_password', 'Password provided with no username.')
    elif options['es_basic_user']:
        http_auth = (options['es_basic_user'], options['es_basic_password'])
    else:
        http_auth = None

    if not options['es_ca_certs'] and options['es_client_cert']:
        click.BadOptionUsage('es_client_cert', '--es-client-cert can only be used when --es-ca-certs is provided.')
    elif not options['es_ca_certs'] and options['es_client_key']:
        click.BadOptionUsage('es_client_key', '--es-client-key can only be used when --es-ca-certs is provided.')
    elif options['es_client_cert'] and not options['es_client_key']:
        click.BadOptionUsage('es_client_cert', '--es-client-key must be provided when --es-client-cert is used.')
    elif not options['es_client_cert'] and options['es_client_key']:
        click.BadOptionUsage('es_client_key', '--es-client-cert must be provided when --es-client-key is used.')

    if options['es_ca_certs']:
        es_client = Elasticsearch(options['es_node'],
                                  verify_certs=True,
                                  ca_certs=options['es_ca_certs'],
                                  client_cert=options['es_client_cert'],
                                  client_key=options['es_client_key'],
                                  http_auth=http_auth,
                                  maxsize=options['es_max_connections'])
    else:
        es_client = Elasticsearch(options['es_node'],
                                  verify_certs=False,
                                  http_auth=http_auth,
                                  maxsize=options['es_max_connections'])

    app = construct_app(es_client, **options)
    app = wsgi_log_middleware(app)

    with nice_shutdown(shutdown):
        bottle.run(app,
                   host='0.0.0.0', port=options['port'],
                   server='gevent', spawn=gevent_pool,
                   # Disable default request logging - we're using middleware
                   quiet=True, error_log=None)


if __name__ == '__main__':
    main(auto_envvar_prefix='KONG_LOG_BRIDGE_OPT')
