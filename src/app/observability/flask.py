import logging

import time
from flask import request
from prometheus_client import start_http_server
from werkzeug.exceptions import HTTPException

from app.observability.correlation_id import get_correlation_id, set_correlation_id
from app.observability.prometheus import prometheus


def initialize_flask(conf, app):
    # setup hooks to handle flask requests and responses
    def _before_request():
        request.started = time.perf_counter()
        get_correlation_id()

    def _after_request(response):
        endpoint = str(request.url_rule)
        prometheus.request_duration.labels(request.method, endpoint).observe(time.perf_counter() - request.started)
        prometheus.request_count.labels(request.method, endpoint, response.status_code).inc()
        set_correlation_id(response.headers)
        return response

    def uncaught_error_handler(error):
        if not isinstance(error, HTTPException):
            raise error
        response = app.make_response(app.finalize_request(error, from_error_handler=True))
        return _after_request(response)

    app.before_request(_before_request)
    app.after_request(_after_request)
    app.register_error_handler(Exception, uncaught_error_handler)

    try:
        start_http_server(conf['metrics']['port'], conf['metrics']['host'])
    except:
        logging.warning('cannot start metrics server; metrics will not be available', exc_info=True)
