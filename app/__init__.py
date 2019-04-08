from importlib import import_module
import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask, request, current_app
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    #from app.errors import bp as errors_bp
    #app.register_blueprint(errors_bp)

    #from app.auth import bp as auth_bp
    #app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.acuity import bp as acuity_bp
    app.register_blueprint(acuity_bp)

    if not app.debug and not app.testing:
        if app.config['LOG_TO_STDOUT'] == "True":
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists(os.path.dirname(__file__) + '/logs'):
                os.mkdir(os.path.dirname(__file__) + '/logs')
            file_handler = RotatingFileHandler(os.path.dirname(__file__) + '/logs/nycmeshbot.log',
                                               maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('NYCMeshBot startup')

    return app
