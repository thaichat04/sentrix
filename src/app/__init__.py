import importlib
import logging
import pkgutil

from flask import Flask

import app.resources
# create flask app and initialize observability stuff
from app.conf.conf import conf
from app.model.load import initialize_model
from app.observability.init import initialize_observability
from app.resources.json_exceptions import initialize_error_handlers
from app.resources.request_handler import RequestHandler

app = Flask(__name__)

initialize_observability(conf['observability'], app=app)

logging.info('starting server')

# set deploy id and database connection pools
app.deploy_id = conf['deploy_id']
app.conf = conf
app.classifier = initialize_model(conf)

# initialize resources
for importer, modname, ispkg in pkgutil.walk_packages(path=resources.__path__):
    importlib.import_module('.' + modname, package='app.resources')

# start listening
host = conf['site']['host']
port = conf['site']['port']
logging.info('server is listening on {}:{}'.format(host, port))

initialize_error_handlers(app)

app.run(host=host, port=port, threaded=True, request_handler=RequestHandler)
