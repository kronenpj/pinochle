import os
from unittest import mock

import connexion
import flask
import pytest
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from pinochle.config import db, connex_app

# Suppress invalid redefined-outer-name messages from pylint.
# pragma pylint: disable=redefined-outer-name

@pytest.fixture(scope="module")
def app():
    """
    Fixture to create an in-memory database and make it available only for the set of
    tests in this file. The database is not recreated between tests so tests can
    interfere with each other. Changing the fixture's scope to "package" or "session"
    makes no difference in the persistence of the database between tests in this file.
    A scope of "class" behaves the same way as "function".

    :yield: The application being tested with the temporary database.
    :rtype: FlaskApp
    """
    # print("Entering conftest.app...")
    with mock.patch.dict(
        "pinochle.server.connex_app.app.config",
        {"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"},
    ):
        app = connex_app.app

        # URL = make_url("sqlite:///:memory:")
        # db = SQLAlchemy(app, engine_options="sqlite:///:memory:")
        # config.db = db
        db.create_all()

        # print("conftest.app, yielding app")
        yield app


# Got these from another project and started tweaking them
# Then I realized that this still wouldn't address the problems
# I was having wrapping my mind around how to adjust the DB URL
# when SQLAlchemy made it read-only in 1.4.x.

# @pytest.fixture
# def f_app(request):
#     # app = flask.Flask(request.module.__name__)

#     # Create the connexion application instance
#     basedir = os.path.abspath(os.path.dirname(__file__) + "/../src/pinochle/")
#     connex_app = connexion.FlaskApp(__name__, specification_dir=basedir)
#     connex_app.add_api("swagger.yml")

#     # Get the underlying Flask app instance
#     app = connex_app.app
#     app.testing = True
#     app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
#     app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#     return app


# @pytest.fixture
# def f_db(app):
#     temp = SQLAlchemy()
#     temp.init_app(app)
#     temp.create_all()

#     yield temp

#     temp.drop_all()


# @pytest.fixture
# def f_ma(app):
#     return Marshmallow(app)
