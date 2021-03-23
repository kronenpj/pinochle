"""
Graciously borrowed from https://github.com/SuryaSankar/flask_pattern_minimal_with_auth
and adapted for use with connexion and my (likely) odd way of constructing the pinochle
project.
"""
import os

import connexion
from flask import abort, redirect, render_template  # pragma: no cover

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
        print(
            f"NOTE: You are using a SQLite database: sqlite:///{app.config['DB_NAME']}"
        )
        print("Using a SQLite database in production is not recommended.")
        print(f"Add 'instance/application.cfg.py' to {basedir} to override defaults.")
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///{db}".format(
            db=app.config["DB_NAME"]
        )
    db.init_app(app)

    # This is harmless if the database already exists.
    db.create_all(app=app)

    # Create a URL route in our application for "/*"
    @app.route("/<script>")  # pragma: no cover
    def python_scripts(script):  # pylint: disable=unused-variable
        """
        This function responds to the browser URL
        localhost:5000/*
        :return:        the requested file or 404.
        """
        if ".py" in script or "favicon.ico" in script:
            return redirect(f"/static/{script}")
        elif ".html" in script:
            return render_template(f"{script}")
        else:
            return abort(404)

    # Create a URL route in our application for "/"
    @app.route("/")  # pragma: no cover
    def index():  # pylint: disable=unused-variable
        """
        This function responds to the browser URL
        localhost:5000/
        :return:        the rendered template 'index.html'
        """
        return render_template("index.html")

    return app
