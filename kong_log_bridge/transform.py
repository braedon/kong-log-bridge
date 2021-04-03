import hashlib
import json
import rfc3339

from base64 import urlsafe_b64encode


HASH_BYTES = 16
CONVERT_TS_PATHS = ['service.created_at', 'service.updated_at',
                    'route.created_at', 'route.updated_at',
                    'started_at', 'tries[].balancer_start']


def update_path(dct, path, update):
    """
    Update a dict structure (e.g. JSON), using a path to specify what value to update.

    The `path` specifies a hierarchy of (string) dictionary keys to traverse, separated by periods.
    Suffixing a key with `[]` indicates the value of that key is an list, and should be iterated.

    e.g. `foo.bar[].baz`

    The `update` can be simply the new value, or a function that takes the old value and returns the
    new value.

    Dicts and lists along the path are copied before being updated, and the updated dict structure
    is returned.
    """

    if not isinstance(dct, dict):
        return dct

    if callable(update):
        update_fn = update
    else:
        def update_fn(value):
            return update

    field, sub_path = path.split('.', 1) if '.' in path else (path, None)

    array_field = False
    if field.endswith('[]'):
        field = field[:-2]
        array_field = True

    if field not in dct:
        return dct

    value = dct[field]

    if array_field and not isinstance(value, list):
        return dct

    if sub_path:
        if array_field:
            updated_value = [update_path(v, sub_path, update_fn) for v in value]
        else:
            updated_value = update_path(value, sub_path, update_fn)

    else:
        if array_field:
            updated_value = [update_fn(v) for v in value]
        else:
            updated_value = update_fn(value)

    updated_dct = dct.copy()
    updated_dct[field] = updated_value
    return updated_dct


def convert_ts(ts):
    """
    Convert a UNIX timestamp to a RFC3339 datetime string

    If the timestamp is greater than 99,999,999,999 (5138-11-16T09:46:39+00:00) it's assumed to be
    in milliseconds rather than seconds.
    """

    if ts is None:
        return None

    if ts > 99_999_999_999:
        ts = ts / 1000

    return rfc3339.timestamptostr(ts)


def hash_value(value, digest_size=HASH_BYTES):
    """
    Hash a string with blake2b, and encode as a URL safe base64 string

    If `value` is an int/float, it will be automatically converted to a string using str().

    If `value` is a list/dict, it will be automatically converted to a compact JSON string.
    """

    if value is None:
        return None

    if isinstance(value, str):
        # Strings can be hashed unchanged
        pass
    elif isinstance(value, (int, float)):
        value = str(value)
    elif isinstance(value, (dict, list)):
        value = json.dumps(value, separators=(',', ':'))
    else:
        raise NotImplementedError(f'Can\'t hash value of type {type(value).__name__}')

    value_bytes = value.encode('utf-8')
    hash_bytes = hashlib.blake2b(value_bytes, digest_size=digest_size).digest()
    return urlsafe_b64encode(hash_bytes).decode('utf-8').replace('=', '')


def hash_authorization(value):
    """ Hash the credentials of a Authorization header, or list of Authorization headers"""

    if value is None:
        return None

    if isinstance(value, list):
        return [hash_authorization(authorization) for authorization in value]

    if ' ' not in value:
        return hash_value(value)

    auth_type, credentials = value.split(' ', 1)
    return f'{auth_type} {hash_value(credentials)}'


def _hash_cookie(value):
    if '=' not in value:
        return hash_value(value)

    cookie_name, cookie_value = value.split('=', 1)
    return f'{cookie_name}={hash_value(cookie_value)}'


def hash_cookies(value):
    """Hash the cookie value of each cookie in a Cookie header, or list of Cookie headers"""

    if value is None:
        return None

    if isinstance(value, list):
        return [hash_cookies(cookies) for cookies in value]

    cookies = value.split('; ')
    return '; '.join(_hash_cookie(cookie) for cookie in cookies)


def hash_set_cookie(value):
    """Hash the cookie value of each cookie in a Set-Cookie header, or list of Set-Cookie headers"""

    if value is None:
        return None

    if isinstance(value, list):
        return [hash_set_cookie(set_cookie) for set_cookie in value]

    if '; ' in value:
        cookie, cookie_options = value.split('; ', 1)
        return f'{_hash_cookie(cookie)}; {cookie_options}'

    else:
        return _hash_cookie(value)


def transform_log(log,
                  do_convert_ts=False,
                  do_hash_ip=False,
                  do_hash_auth=False,
                  do_hash_cookie=False,
                  hash_paths=None,
                  null_paths=None,
                  expose_ips=None):

    if expose_ips is None:
        expose_ips = []

    if convert_ts:
        for path in CONVERT_TS_PATHS:
            log = update_path(log, path, convert_ts)

    if do_hash_ip:
        # Extract client IP in case we need to expose it later.
        client_ip = log.get('client_ip')

        log = update_path(log, 'client_ip', hash_value)

        if client_ip:
            # Check if IP hash is in the exposure list.
            client_ip_hash = log.get('client_ip')
            if client_ip_hash in expose_ips:
                log['raw_client_ip'] = client_ip

    if do_hash_auth:
        log = update_path(log, 'request.headers.authorization', hash_authorization)

    if do_hash_cookie:
        log = update_path(log, 'request.headers.cookie', hash_cookies)
        log = update_path(log, 'response.headers.set-cookie', hash_set_cookie)

    if hash_paths:
        for path in hash_paths:
            log = update_path(log, path, hash_value)

    if null_paths:
        for path in null_paths:
            log = update_path(log, path, None)

    return log
