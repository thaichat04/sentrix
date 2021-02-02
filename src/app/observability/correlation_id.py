import logging
import uuid

from flask import has_request_context, request

CORRELATION_HEADER_NAME = 'X-Correlation-Id'


def get_correlation_id():
    correlation_id = None
    if has_request_context():
        correlation_id = getattr(request, 'correlation_id', None)
        if not correlation_id:
            correlation_id = request.headers.get(CORRELATION_HEADER_NAME)
            if not correlation_id:
                correlation_id = str(uuid.uuid4())
            request.correlation_id = correlation_id
    return correlation_id


def set_correlation_id(headers):
    if has_request_context():
        headers[CORRELATION_HEADER_NAME] = request.correlation_id


class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        correlation_id = get_correlation_id()
        if correlation_id:
            # use camel case for consistency with java
            record.correlationId = correlation_id
        else:
            record.correlationId = ''
        return True
