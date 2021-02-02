import warnings
from logging import config, captureWarnings

from app.observability.flask import initialize_flask


def initialize_observability(conf, app=None):
    # logging
    config.dictConfig(conf['logging'])
    captureWarnings(True)
    warnings.simplefilter('ignore')

    if app:
        # flask
        initialize_flask(conf, app)
