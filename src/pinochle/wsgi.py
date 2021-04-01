#!/usr/bin/env python3

import json

import geventwebsocket
from flask import abort, make_response, redirect, render_template, request
from flask_sockets import Sockets

from . import app_factory, custom_log
from .__main__ import GLOBAL_LOG_LEVEL
from .models import utils


application = app_factory.create_app()  # pragma: no cover
app = application
# Create non-blueprint-defined endpoints.


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
