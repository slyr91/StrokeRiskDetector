import os

from . import db, estimator, auth, index
from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        # DATABASE=os.environ.get('DATABASE_URL', 'postgres://postgres:?abc1234@localhost:5432/stroke_app')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(index.bp)
    app.add_url_rule('/', endpoint='index')

    with app.app_context():
        estimator.init_estimator()

    return app
