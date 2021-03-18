"""
Graciously borrowed from https://github.com/SuryaSankar/flask_pattern_minimal_with_auth
and adapted for use with connexion and my (likely) odd way of constructing the pinochle
project.
"""
import os

import connexion

# pragma: pylint: disable=unused-import
from . import models
from .models.core import db


def create_app(register_blueprints=True):
    # Create the connexion application instance
    basedir = os.path.abspath(os.path.dirname(__file__))
    connex_app = connexion.App(__name__, specification_dir=basedir)
    app = connex_app.app

    if register_blueprints:
        connex_app.add_api("swagger.yml")

    app.config.from_object("pinochle.default_config")
    try:
        app.config.from_pyfile("instance/application.cfg.py")
    except FileNotFoundError:
        # print("The application.cfg.py file was not found. Using defaults.")
        pass

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Handle the special way SQLite3 works.
    if app.config["SQLALCHEMY_DB_PREFIX"] != "sqlite":
        app.config[
            "SQLALCHEMY_DATABASE_URI"
        ] = "{db_prefix}://{user}:{passwd}@{server}/{db}".format(
            db_prefix=app.config["SQLALCHEMY_DB_PREFIX"],
            user=app.config["DB_USERNAME"],
            passwd=app.config["DB_PASSWORD"],
            server=app.config["DB_SERVER"],
            db=app.config["DB_NAME"],
        )
    else:
        print(f"NOTE: You are using a SQLite database: sqlite:///{app.config['DB_NAME']}")
        print("Using a SQLite database in production is not recommended.")
        print(f"Add 'instance/application.cfg.py' to {basedir} to override defaults.")
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///{db}".format(
            db=app.config["DB_NAME"]
        )
    db.init_app(app)

    # This is harmless if the database already exists.
    db.create_all(app=app)

    return app
