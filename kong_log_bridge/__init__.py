import json
import simplejson

from bottle import Bottle, abort, request, response

from .transform import transform_log


def json_default_error_handler(http_error):
    response.content_type = 'application/json'
    return json.dumps({'error': http_error.body}, separators=(',', ':'))


def construct_app(es_client, es_index, **kwargs):
    app = Bottle()
    app.default_error_handler = json_default_error_handler

    @app.get('/status')
    def status():
        return 'OK'

    @app.post('/logs')
    def logs():
        if request.headers.get('Content-Type') != 'application/json':
            abort(415, 'Require "Content-Type: application/json"')

        try:
            log = request.json
        except simplejson.JSONDecodeError:
            abort(400, 'POST data is not valid JSON')

        if not isinstance(log, dict):
            abort(400, 'POST body must be a JSON object')

        log = transform_log(log,
                            do_convert_ts=kwargs['convert_ts'],
                            do_hash_ip=kwargs['hash_ip'],
                            do_hash_auth=kwargs['hash_auth'],
                            do_hash_cookie=kwargs['hash_cookie'],
                            hash_paths=kwargs['hash_path'],
                            null_paths=kwargs['null_path'])

        es_client.index(index=es_index, body=log, request_timeout=30)

        response.status = 204

    return app
