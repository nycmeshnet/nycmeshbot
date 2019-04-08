import os, json
from flask import Flask, request, Response, jsonify, current_app
from app.acuity import bp
from app.acuity import handlers


@bp.route('/acuity', methods=['POST'])
def acuity():
    handler = handlers.AcuityHandlers(current_app.config)
    if request.headers.get('X-Acuity-Signature'):
        data = request.form
        if data.get('action') in ["scheduled","canceled","rescheduled","changed"]:
            handler.parse_event(data.get('action'), data.get('id'), 'install-team')

        #print(data)

    return Response(), 200
