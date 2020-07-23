import unittest

from kong_log_bridge.transform import transform_log


class Test(unittest.TestCase):
    maxDiff = None

    def test_transform(self):
        test_log = {
            "latencies": {
                "request": 191,
                "kong": 0,
                "proxy": 191
            },
            "service": {
                "host": "example.default.80.svc",
                "created_at": 1595260351,
                "connect_timeout": 60000,
                "id": "adc094b9-1359-5576-8973-5f5aac508101",
                "protocol": "http",
                "name": "example.default.80",
                "read_timeout": 60000,
                "port": 80,
                "path": "/",
                "updated_at": 1595260351,
                "write_timeout": 60000,
                "retries": 5
            },
            "request": {
                "querystring": {},
                "size": "1430",
                "uri": "/login",
                "url": "https://example.com:8443/login",
                "headers": {
                    "host": "example.com",
                    "content-type": "application/x-www-form-urlencoded",
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "authorization": "Bearer some_token",
                    "cookie": "__Host-example_login_csrf-zK9kT=some_login_csrf",
                    "upgrade-insecure-requests": "1",
                    "connection": "keep-alive",
                    "referer": "https://example.com/login?continue=https%3A%2F%2Fexample.com%2Foauth2%2Fauthorize%3Fresponse_type%3Dcode%26client_id%3Dexample_client%26scope%3Dopenid%26state%3Dp2DOUg5DvzyFFxE9D%26nonce%3DFjKXc-cZLMHf3ohZQ_HQZQ%26redirect_uri%3Dhttps%253A%252F%252Fexample.com%252Fapp%252Foidc%252Fcallback%26new_login%3Dtrue&client_id=example_client",
                    "accept-language": "en-US,en;q=0.5",
                    "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:79.0) Gecko/20100101 Firefox/79.0",
                    "content-length": "478",
                    "origin": "https://example.com",
                    "dnt": "1",
                    "accept-encoding": "gzip, deflate, br"
                },
                "method": "POST"
            },
            "client_ip": "1.2.3.4",
            "tries": [
                {
                    "balancer_latency": 0,
                    "port": 8080,
                    "balancer_start": 1595326603251,
                    "ip": "10.244.1.139"
                }
            ],
            "upstream_uri": "/login",
            "response": {
                "headers": {
                    "content-type": "text/html; charset=UTF-8",
                    "connection": "close",
                    "referrer-policy": "no-referrer, strict-origin-when-cross-origin",
                    "expect-ct": "max-age=86400, enforce",
                    "strict-transport-security": "max-age=63072000; includeSubDomains; preload",
                    "x-xss-protection": "1; mode=block",
                    "x-kong-proxy-latency": "0",
                    "x-frame-options": "DENY",
                    "content-security-policy": "default-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; block-all-mixed-content; img-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'",
                    "content-length": "1252",
                    "feature-policy": "accelerometer 'none'; ambient-light-sensor 'none'; autoplay 'none'; battery 'none'; camera 'none'; display-capture 'none'; document-domain 'none'; encrypted-media 'none'; execution-while-not-rendered 'none'; execution-while-out-of-viewport 'none'; fullscreen 'none'; geolocation 'none'; gyroscope 'none'; layout-animations 'none'; legacy-image-formats 'none'; magnetometer 'none'; microphone 'none'; midi 'none'; navigation-override 'none'; oversized-images 'none'; payment 'none'; picture-in-picture 'none'; publickey-credentials 'none'; sync-xhr 'none'; usb 'none'; wake-lock 'none'; xr-spatial-tracking 'none'",
                    "via": "kong/2.0.2",
                    "set-cookie": [
                        "__Host-example_auth=some_auth; HttpOnly; Max-Age=86400; Path=/; SameSite=lax; Secure",
                        "__Host-example_csrf=some_csrf; HttpOnly; Max-Age=86400; Path=/; SameSite=strict; Secure"
                    ],
                    "x-kong-upstream-latency": "191",
                    "date": "Tue, 21 Jul 2020 10:16:44 GMT",
                    "x-content-type-options": "nosniff"
                },
                "status": 200,
                "size": "3552"
            },
            "route": {
                "created_at": 1595260351,
                "path_handling": "v0",
                "id": "b01758b0-be33-5274-adfd-e53704dc2e4c",
                "service": {
                    "id": "adc094b9-1359-5576-8973-5f5aac508101"
                },
                "name": "example.default.00",
                "strip_path": False,
                "preserve_host": True,
                "regex_priority": 0,
                "updated_at": 1595260351,
                "paths": [
                    "/"
                ],
                "https_redirect_status_code": 426,
                "protocols": [
                    "http",
                    "https"
                ],
                "hosts": [
                    "example.com"
                ]
            },
            "started_at": 1595326603250
        }
        expected = {
            "latencies": {
                "request": 191,
                "kong": 0,
                "proxy": 191
            },
            "service": {
                "host": "example.default.80.svc",
                "created_at": "2020-07-20T15:52:31+00:00",
                "connect_timeout": 60000,
                "id": "adc094b9-1359-5576-8973-5f5aac508101",
                "protocol": "http",
                "name": "example.default.80",
                "read_timeout": 60000,
                "port": 80,
                "path": "/",
                "updated_at": "2020-07-20T15:52:31+00:00",
                "write_timeout": 60000,
                "retries": 5
            },
            "request": {
                "querystring": {},
                "size": "1430",
                "uri": "/login",
                "url": "https://example.com:8443/login",
                "headers": {
                    "host": "example.com",
                    "content-type": "application/x-www-form-urlencoded",
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "authorization": "Bearer 0Mmt7PwMgQ9Z7oYvP4ypoQ",
                    "cookie": "__Host-example_login_csrf-zK9kT=7xe0gvFR3iHPwx-B6ZIu8A",
                    "upgrade-insecure-requests": "1",
                    "connection": "keep-alive",
                    "referer": "https://example.com/login?continue=https%3A%2F%2Fexample.com%2Foauth2%2Fauthorize%3Fresponse_type%3Dcode%26client_id%3Dexample_client%26scope%3Dopenid%26state%3Dp2DOUg5DvzyFFxE9D%26nonce%3DFjKXc-cZLMHf3ohZQ_HQZQ%26redirect_uri%3Dhttps%253A%252F%252Fexample.com%252Fapp%252Foidc%252Fcallback%26new_login%3Dtrue&client_id=example_client",
                    "accept-language": "en-US,en;q=0.5",
                    "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:79.0) Gecko/20100101 Firefox/79.0",
                    "content-length": "478",
                    "origin": "https://example.com",
                    "dnt": "1",
                    "accept-encoding": "gzip, deflate, br"
                },
                "method": "POST"
            },
            "client_ip": "Pk7QhG5N_LBhKQyqtwiOSQ",
            "tries": [
                {
                    "balancer_latency": 0,
                    "port": 8080,
                    "balancer_start": "2020-07-21T10:16:43+00:00",
                    "ip": "10.244.1.139"
                }
            ],
            "upstream_uri": "/login",
            "response": {
                "headers": {
                    "content-type": "text/html; charset=UTF-8",
                    "connection": "close",
                    "referrer-policy": "no-referrer, strict-origin-when-cross-origin",
                    "expect-ct": "max-age=86400, enforce",
                    "strict-transport-security": "max-age=63072000; includeSubDomains; preload",
                    "x-xss-protection": "1; mode=block",
                    "x-kong-proxy-latency": "0",
                    "x-frame-options": "DENY",
                    "content-security-policy": "default-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; block-all-mixed-content; img-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'",
                    "content-length": "1252",
                    "feature-policy": "accelerometer 'none'; ambient-light-sensor 'none'; autoplay 'none'; battery 'none'; camera 'none'; display-capture 'none'; document-domain 'none'; encrypted-media 'none'; execution-while-not-rendered 'none'; execution-while-out-of-viewport 'none'; fullscreen 'none'; geolocation 'none'; gyroscope 'none'; layout-animations 'none'; legacy-image-formats 'none'; magnetometer 'none'; microphone 'none'; midi 'none'; navigation-override 'none'; oversized-images 'none'; payment 'none'; picture-in-picture 'none'; publickey-credentials 'none'; sync-xhr 'none'; usb 'none'; wake-lock 'none'; xr-spatial-tracking 'none'",
                    "via": "kong/2.0.2",
                    "set-cookie": [
                        "__Host-example_auth=vsXTPw-wyNDQcioekyXCcw; HttpOnly; Max-Age=86400; Path=/; SameSite=lax; Secure",
                        "__Host-example_csrf=0-UmIYo1jhPDgnW5pHsEHw; HttpOnly; Max-Age=86400; Path=/; SameSite=strict; Secure"
                    ],
                    "x-kong-upstream-latency": "191",
                    "date": "Tue, 21 Jul 2020 10:16:44 GMT",
                    "x-content-type-options": "nosniff"
                },
                "status": 200,
                "size": "3552"
            },
            "route": {
                "created_at": "2020-07-20T15:52:31+00:00",
                "path_handling": "v0",
                "id": "b01758b0-be33-5274-adfd-e53704dc2e4c",
                "service": {
                    "id": "adc094b9-1359-5576-8973-5f5aac508101"
                },
                "name": "example.default.00",
                "strip_path": False,
                "preserve_host": True,
                "regex_priority": 0,
                "updated_at": "2020-07-20T15:52:31+00:00",
                "paths": [
                    "/"
                ],
                "https_redirect_status_code": 426,
                "protocols": [
                    "http",
                    "https"
                ],
                "hosts": [
                    "example.com"
                ]
            },
            "started_at": "2020-07-21T10:16:43+00:00"
        }

        result = transform_log(test_log,
                               do_convert_ts=True,
                               do_hash_ip=True,
                               do_hash_auth=True,
                               do_hash_cookie=True)
        self.assertEqual(expected, result)

    def test_transform_bad_auth(self):
        test_log = {
            "request": {
                "headers": {
                    "authorization": "some_token",
                },
            },
        }
        expected = {
            "request": {
                "headers": {
                    "authorization": "0Mmt7PwMgQ9Z7oYvP4ypoQ",
                },
            },
        }

        result = transform_log(test_log,
                               do_hash_auth=True)
        self.assertEqual(expected, result)

    def test_transform_bad_cookie(self):
        test_log = {
            "request": {
                "headers": {
                    "cookie": "__Host-example_login_csrf-zK9kT-some_login_csrf",
                },
            },
            "response": {
                "headers": {
                    "set-cookie": [
                        "__Host-example_auth/some_auth; HttpOnly; Max-Age=86400; Path=/; SameSite=lax; Secure",
                        "__Host-example_csrf|some_csrf; HttpOnly; Max-Age=86400; Path=/; SameSite=strict; Secure"
                    ],
                },
            },
        }
        expected = {
            "request": {
                "headers": {
                    "cookie": "BPvPOrxZNo_DhGCLTtcO_A",
                },
            },
            "response": {
                "headers": {
                    "set-cookie": [
                        "ceNEbDKXcwmC6WjnoB3xNw; HttpOnly; Max-Age=86400; Path=/; SameSite=lax; Secure",
                        "AwdYctEnVuXiVepXBiXu-w; HttpOnly; Max-Age=86400; Path=/; SameSite=strict; Secure"
                    ],
                },
            },
        }

        result = transform_log(test_log,
                               do_hash_cookie=True)
        self.assertEqual(expected, result)

    def test_hash_paths(self):
        test_log = {
            'foo': [
                {'bar': 'a', 'baz': 'a'},
                {'bar': 'a', 'baz': 'b'},
                {'bar': 1, 'baz': 'c'},
                {'bar': 1.1, 'baz': 'd'},
                {'bar': ['a'], 'baz': 'e'},
                {'bar': {'a': 'b'}, 'baz': 'f'},
            ],
        }
        expected = {
            'foo': [
                {'bar': 'J8NebpNzh38p5WJGTkZJfg', 'baz': 'a'},
                {'bar': 'J8NebpNzh38p5WJGTkZJfg', 'baz': 'b'},
                {'bar': 'zqOHijNLJARp0Vn_hAtkNA', 'baz': 'c'},
                {'bar': 'oduRJWsoVhEUGjoLDP2igA', 'baz': 'd'},
                {'bar': '9TsxVbMCmC4Za3ZFt7YUsQ', 'baz': 'e'},
                {'bar': 'WJqukeZh_5Vhv1BN0Cam4Q', 'baz': 'f'},
            ],
        }

        result = transform_log(test_log,
                               hash_paths=['foo[].bar'])
        self.assertEqual(expected, result)

    def test_null_paths(self):
        test_log = {
            'foo': [
                {'bar': 'a', 'baz': 'a'},
                {'bar': 1, 'baz': 'b'},
                {'bar': 1.1, 'baz': 'c'},
                {'bar': ['a'], 'baz': 'd'},
                {'bar': {'a': 'b'}, 'baz': 'e'},
            ],
        }
        expected = {
            'foo': [
                {'bar': None, 'baz': 'a'},
                {'bar': None, 'baz': 'b'},
                {'bar': None, 'baz': 'c'},
                {'bar': None, 'baz': 'd'},
                {'bar': None, 'baz': 'e'},
            ],
        }

        result = transform_log(test_log,
                               null_paths=['foo[].bar'])
        self.assertEqual(expected, result)
