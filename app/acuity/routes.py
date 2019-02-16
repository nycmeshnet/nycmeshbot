import os, json
from flask import Flask, request, Response, jsonify, current_app
from app.acuity import bp
from app.acuity import handlers


#app = Flask(__name__)
#with app.app_context():
#    print current_app.name


@bp.route('/acuity', methods=['POST'])
def acuity():
    handler = handlers.AcuityHandlers(current_app.config)
    if request.headers.get('X-Acuity-Signature'):
        data = request.form
        if data.get('action') == "scheduled":
            handler.parse_event(data.get('action'), data.get('id'), 'bottest')
        #print(data)

    return Response(), 200
