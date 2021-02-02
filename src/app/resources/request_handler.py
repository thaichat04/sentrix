import logging
import threading
import time

from werkzeug.serving import WSGIRequestHandler


class RequestHandler(WSGIRequestHandler):
    _lock = threading.Lock()
    _in_flight_requests = 0
    _last_request = threading.Condition(_lock)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle_one_request(self):
        with RequestHandler._lock:
            RequestHandler._in_flight_requests += 1
        try:
            super().handle_one_request()
        finally:
            with RequestHandler._lock:
                RequestHandler._in_flight_requests -= 1
                if RequestHandler._in_flight_requests == 1:
                    RequestHandler._last_request.notify()

    @staticmethod
    def wait_until_last_request_completes(timeout_seconds=60):
        limit = time.time() + timeout_seconds
        nb_requests = None
        while time.time() <= limit:
            with RequestHandler._lock:
                if nb_requests is None:
                    nb_requests = RequestHandler._in_flight_requests - 1
                if RequestHandler._in_flight_requests == 1:
                    break
                RequestHandler._last_request.wait(timeout=timeout_seconds)
        if time.time() > limit:
            logging.warning('timeout ({} seconds) while waiting for {} requests to complete'
                            .format(timeout_seconds, RequestHandler._in_flight_requests))
        time.sleep(2)
        return nb_requests
