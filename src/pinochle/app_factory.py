"""
Graciously borrowed from https://github.com/SuryaSankar/flask_pattern_minimal_with_auth
and adapted for use with connexion and my (likely) odd way of constructing the pinochle
project.
"""
import json
import os

import connexion

# pragma: pylint: disable=unused-import
from . import custom_log, models
from .__main__ import GLOBAL_LOG_LEVEL
from .models import utils
from .models.core import db


def create_app(register_blueprints=True):
    mylog = custom_log.get_logger()
    mylog.setLevel(GLOBAL_LOG_LEVEL)

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
        mylog.info(
            "NOTE: You are using a SQLite database: sqlite:///%s", app.config["DB_NAME"]
        )
        mylog.info("Using a SQLite database in production is not recommended.")
        mylog.info(
            "Add 'instance/application.cfg.py' to %s to override defaults.", basedir
        )
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///{db}".format(
            db=app.config["DB_NAME"]
        )
    db.init_app(app)

    # This is harmless if the database already exists.
    db.create_all(app=app)

    # Create non-openapi-defined endpoints.
    @app.route("/api/setcookie/player_id/<ident>", methods=["GET"])
    def set_playercookie(ident: str):
        """
        Wrapper for setcookie.

        :param ident: [description]
        :type ident: str
        """
        # print(f"Setting player_id cookie for {ident}")
        return setcookie("player_id", ident)

    @app.route("/api/setcookie/game_id/<ident>", methods=["GET"])
    def set_gamecookie(ident: str):
        """
        Wrapper for setcookie.

        :param ident: [description]
        :type ident: str
        """
        # print(f"Setting game_id cookie for {ident}")
        return setcookie("game_id", ident)

    def setcookie(kind: str, ident: str):
        """
        Generate a cookie for the supplied kind and identifier.

        :param kind: [description]
        :type kind: str
        :param ident: [description]
        :type ident: str
        :return: [description]
        :rtype: Response
        """
        # print("In app.setcookie.")
        if kind not in ["game_id", "player_id"]:
            abort(404, "Incorrect parameters.")
        if ident is None:
            abort(404, f"{kind.capitalize()} not supplied.")

        db_response = None
        # print(f"app.setcookie: Setting {kind} cookie with value {ident}")
        if ident == "clear":
            db_response = "clear"
        elif kind == "game_id":
            db_response = utils.query_game(game_id=ident)
        elif kind == "player_id":
            db_response = utils.query_player(player_id=ident)
        if db_response is None:
            abort(404, f"{kind.capitalize()} not registered.")
        resp = make_response("The Cookie has been Set")
        resp.status_code = 200
        if db_response == "clear":
            resp.set_cookie(kind, "", samesite="Strict", expires=0)
        else:
            resp.set_cookie(kind, ident, samesite="Strict")
        # print(f"app.setcookie: resp={resp}")
        return resp

    # Create non-openapi-defined endpoints.
    @app.route("/api/getcookie/<kind>", methods=["GET"])
    def getcookie(kind: str):
        """
        Emit the player_id from the cookie supplied by the browser.

        :kind: [description]
        :type: str
        :return: [description]
        :rtype: Response
        """
        # print("In app.getcookie.")

        if kind not in ["game_id", "player_id"]:
            abort(404, "Incorrect parameters.")

        ident = request.cookies.get(kind)
        if ident is None or ident == "":
            abort(404, "Cookie does not exist.")
        db_response = None
        if kind == "game_id":
            db_response = utils.query_game(game_id=ident)
        elif kind == "player_id":
            db_response = utils.query_player(player_id=ident)
        if db_response is None:
            abort(404, f"{kind.capitalize()} not registered.")
        resp = make_response(json.dumps({"kind": kind, "ident": ident}))
        resp.status_code = 200
        resp.set_cookie(kind, ident, samesite="Strict")
        # print(f"app.getcookie: resp={resp}")
        return resp

    # Create a URL route in our application for "/*"
    @app.route("/<script>", methods=["GET"])  # pragma: no cover
    def python_scripts(script):  # pylint: disable=unused-variable
        """
        This function responds to the browser URL
        localhost:5000/*
        :return:        the requested file or 404.
        """
        if ".py" in script or "favicon.ico" in script:
            return redirect(f"/static/{script}")
        if ".html" in script:
            return render_template(f"{script}")
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
