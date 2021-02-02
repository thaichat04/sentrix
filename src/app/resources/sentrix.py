import json

from flask import Response, request, abort

from app import app


@app.route('/version', methods=['GET'])
def version():
    return Response(json.dumps({'version': '0'}), status=200, mimetype="application/json")


@app.route('/v0/model', methods=['GET'])
def model():
    info = {
        'name': app.classifier.model.name,
        'config': app.classifier.model.config.to_dict()
    }
    return Response(json.dumps(info), status=200, mimetype="application/json")


@app.route('/v0/classify', methods=['POST'])
def fit():
    input_ = request.form.get('input')
    if not input:
        abort(400)
    return Response(json.dumps(app.classifier(input_)), status=200, mimetype="application/json")
