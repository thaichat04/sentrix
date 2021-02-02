from flask import jsonify
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import default_exceptions


def _handler(error):
    response = jsonify(message=str(error.description) if hasattr(error, 'description') else str(error),
                       cause=type(error.__cause__).__name__ if error.__cause__ else None)
    response.status_code = error.code if isinstance(error, HTTPException) else 500
    return response


def _register(app, exception_type):
    app.errorhandler(exception_type)(_handler)


def initialize_error_handlers(app):
    _register(app, HTTPException)
    for exception_type in default_exceptions.values():
        _register(app, exception_type)
