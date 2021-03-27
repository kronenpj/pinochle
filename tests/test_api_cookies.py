"""
Tests for the various round classes.

License: GPLv3
"""
import json
import uuid
from random import choice

import pytest
from pinochle import gameround, round_, roundteams, teamplayers
from pinochle.cards.const import SUITS
from pinochle.models import utils
from pinochle.models.core import db

# pylint: disable=wrong-import-order
from werkzeug import exceptions

import test_utils

# from pinochle.models.utils import dump_db


def test_create_game_id_cookie(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/setcookie/game_id/<ident>' page is requested (GET)
    THEN check that the response contains the expected information
    """
    # Create a new game
    game_id = test_utils.create_game(kitty_size=0)

    with app.test_client() as test_client:
        # Attempt to access the set cookie API
        response = test_client.get(f"/api/setcookie/game_id/{game_id}")
        assert response.status == "200 OK"
        print(f"response.headers={response.headers}")
        assert f"game_id={game_id}" in response.headers["Set-Cookie"]

        response = test_client.get("/api/getcookie/game_id")
        assert response.status == "200 OK"
        response_str = response.get_data(as_text=True)
        assert "game_id" in response_str
        assert game_id in response_str
        print(f"response.headers={response.headers}")
        assert f"game_id={game_id}" in response.headers["Set-Cookie"]


def test_create_player_id_cookie(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/setcookie/player_id/<ident>' page is requested (GET)
    THEN check that the response contains the expected information
    """
    # Create a new player
    player_id = test_utils.create_player("PlayerName")

    with app.test_client() as test_client:
        # Attempt to access the set cookie API
        response = test_client.get(f"/api/setcookie/player_id/{player_id}")
        assert response.status == "200 OK"
        print(f"response.headers={response.headers}")
        assert f"player_id={player_id}" in response.headers["Set-Cookie"]

        response = test_client.get("/api/getcookie/player_id")
        assert response.status == "200 OK"
        response_str = response.get_data(as_text=True)
        assert "player_id" in response_str
        assert player_id in response_str
        print(f"response.headers={response.headers}")
        assert f"player_id={player_id}" in response.headers["Set-Cookie"]



def test_create_game_id_cookie_bad(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/setcookie/game_id/<ident>' page is requested (GET)
    THEN check that the response contains the expected information
    """
    # Create a new game
    game_id = str(uuid.uuid4())

    with app.test_client() as test_client:
        # Attempt to access the set cookie API
        response = test_client.get(f"/api/setcookie/game_id/{game_id}")
        assert response.status == "404 NOT FOUND"
        print(f"response.headers={response.headers}")
        assert "Set-Cookie" not in response.headers

        response = test_client.get("/api/getcookie/game_id")
        assert response.status == "404 NOT FOUND"
        response_str = response.get_data(as_text=True)
        assert "game_id" not in response_str
        assert game_id not in response_str
        print(f"response.headers={response.headers}")
        assert "Set-Cookie" not in response.headers


def test_create_player_id_cookie_bad(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/setcookie/player_id/<ident>' page is requested (GET)
    THEN check that the response contains the expected information
    """
    # Create a new player
    player_id = str(uuid.uuid4())

    with app.test_client() as test_client:
        # Attempt to access the set cookie API
        response = test_client.get(f"/api/setcookie/player_id/{player_id}")
        assert response.status == "404 NOT FOUND"
        print(f"response.headers={response.headers}")
        assert "Set-Cookie" not in response.headers

        response = test_client.get("/api/getcookie/player_id")
        assert response.status == "404 NOT FOUND"
        response_str = response.get_data(as_text=True)
        assert "player_id" not in response_str
        assert player_id not in response_str
        print(f"response.headers={response.headers}")
        assert "Set-Cookie" not in response.headers
