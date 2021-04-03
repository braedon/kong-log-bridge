Kong Request Log Bridge
====
Transform Kong request logs and forward them to Elasticsearch. Redact request logs for improved privacy and security, and index them directly into Elasticsearch, without the need for complex and heavyweight tools like Logstash.

[Source Code](https://github.com/braedon/kong-log-bridge) | [Docker Image](https://hub.docker.com/r/braedon/kong-log-bridge)

# Usage
The service is distributed as a docker image. Released versions can be found on Docker Hub (note that no `latest` version is provided):

```bash
> sudo docker pull braedon/kong-log-bridge:<version>
```

The docker image exposes a REST API on port `8080`. It is configured by passing options after the image name:
```bash
> sudo docker run --rm --name kong-log-bridge \
    -p <host port>:8080 \
    braedon/kong-log-bridge:<version> \
        -e <elasticsearch node> \
        --convert-ts \
        --hash-ip \
        --hash-auth \
        --hash-cookie
```
Run with the `-h` flag to see details on all the available options.

Note that all options can be set via environment variables. The environment variable names are prefixed with `KONG_LOG_BRIDGE_OPT`, e.g. `KONG_LOG_BRIDGE_OPT_CONVERT_TS=true` is equivalent to `--convert-ts`. CLI options take precedence over environment variables.

## Input
Kong JSON request logs can be `POST`ed to the `/logs` endpoint. This is designed for logs to be sent by the [Kong HTTP Log plugin](https://docs.konghq.com/hub/kong-inc/http-log/). See the Kong documentation for details on how to enable and configure the plugin.

This is currently the only supported input method, but more may be added in the future.

## Transformation
Request logs are passed through unchanged by default, but you probably want to enable at least one transformation.

### Timestamp Conversion `--convert-ts`
Kong request logs include a number of UNIX timestamps (some in milliseconds rather than seconds). These are not human readable, and require explicit mappings to be used in Elasticsearch. Enabling this option will convert these timestamps to [RFC3339 date-time strings](https://www.ietf.org/rfc/rfc3339.txt) for readability and automatic Elasticsearch mapping.

Fields converted:
```
 - service.created_at
 - service.updated_at
 - route.created_at
 - route.updated_at
 - started_at
 - tries[].balancer_start
```

### Client IP Hashing `--hash-ip`
This option enables hashing the `client_ip` field to avoid storing sensitive user IP addresses.

Specific raw IP addresses can be exposed with the `--expose-ip` option. This option adds a `raw_client_ip` field to logs for requests from the specified IP address hash. This option should only be used where accessing the raw IP is strictly necessary, e.g. to investigate an IP that's sending malicious requests.

### Authorization Hashing `--hash-auth`
This option enables hashing the `credentials` part of the [`Authorization` request header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Authorization) (`request.headers.authorization` field) to avoid storing credentials/tokens.

```
Authorization: Bearer some_secret_token -> Bearer 7ftgstREEBqhHrQNgj6MVA
```

### Cookie Hashing `--hash-cookie`
This option enables hashing the `value` part of the [`Cookie` request header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cookie) (`request.headers.cookie` field) and [`Set-Cookie` response header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie) (`response.headers.set-cookie` field) to avoid storing sensitive cookies.

```
Cookie: some_cookie=some_session -> some_cookie=q1EXmTUdD0Bvm8_jHrQizw
Set-Cookie: some_cookie=some_session; Secure; HttpOnly; SameSite=Lax -> some_cookie=q1EXmTUdD0Bvm8_jHrQizw; Secure; HttpOnly; SameSite=Lax
```

### Field Hashing and Nulling `--hash-path`/`--null-path`
Arbitrary request log fields can be hashed or converted to null by specifying their path with these options. Provide the desired option multiple times to specify multiple paths.

Paths describe how to traverse the JSON structure of the request logs to find a field. They consist of a hierarchy of object fields to traverse from the root JSON object, separated by periods (`.`). The `[]` suffix on a field indicates its value is an array, and should be iterated.

e.g. `--hash-path tries[].ip` will hash the `ip` of every upstream "try" in the `tries` array.

Paths don't need to end at specific value - they can specify an entire object or array.

e.g. `--null-path request.headers` will convert the entire `request.headers` object to null, effectively removing it from the log.

If a path doesn't match any field in a given request log it will be ignored.

## Output
Transformed logs are indexed in Elasticsearch.

This is currently the only supported output method, but more may be added in the future.

### Elasticsearch Nodes `-e`/`--es-node` (required)
The address of at least one Elasticsearch node must be provided via this option. The port should be included if non-standard (`9200`). Provide the option multiple times to specify multiple nodes in a cluster.

### Elasticsearch Index `-es-index`
The Elasticsearch index to send logs to. [Elasticsearch index date math](https://www.elastic.co/guide/en/elasticsearch/reference/current/date-math-index-names.html) can be used. Defaults to `<kong-requests-{now/d}>`.

### Elasticsearch Security
A number of options exist to support Elasticsearch server and client SSL, and basic authentication. See the `-h` output for details.

# Development
To run directly from the git repo, run the following in the root project directory:
```bash
> pip3 install -r requirements.txt
> python3 main.py [OPTIONS]
```
To run tests (as usual, from the root project directory), use:
```bash
> python3 -m unittest
```
Note that these tests currently only cover the log transformation functionality - there are no automated system tests as of yet.

To build a docker image directly from the git repo, run the following in the root project directory:
```bash
> sudo docker build -t <your repository name and tag> .
```

To develop in a docker container, first build the image, and then run the following in the root project directory:
```bash
> sudo docker run --rm -it --name kong-log-bridge --entrypoint bash -v $(pwd):/app <your repository name and tag>
```
This will mount all the files inside the container, so editing tests or application code will be synced live. You can run the tests with `python -m unittest`.

Send me a PR if you have a change you want to contribute!
