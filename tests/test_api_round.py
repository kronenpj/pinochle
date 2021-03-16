"""
Tests for the various round classes.

License: GPLv3
"""
import json

import pytest
import regex
from pinochle import game, gameround, round_
from pinochle.config import db

# pylint: disable=wrong-import-order
from werkzeug import exceptions

UUID_REGEX_TEXT = r"^([a-f\d]{8}(-[a-f\d]{4}){3}-[a-f\d]{12}?)$"
UUID_REGEX = regex.compile(UUID_REGEX_TEXT)

TEAM_NAMES = ["Us", "Them"]
PLAYER_NAMES = ["Thing1", "Thing2", "Red", "Blue"]
N_TEAMS = len(TEAM_NAMES)
N_PLAYERS = len(PLAYER_NAMES)
N_KITTY = 4


def test_round_create(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round' page is requested (POST)
    THEN check that the response is a UUID and contains the expected information
    """
    # print(f"{app.config['SQLALCHEMY_DATABASE_URI']=}")

    # Create a new game
    db_response, status = game.create()
    assert status == 201
    assert db_response is not None
    game_id = db_response.get("game_id")

    with app.test_client() as test_client:
        # Attempt to access the create round api
        response = test_client.post(f"/api/game/{game_id}/round")
        assert response.status == "201 CREATED"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        round_id = response_data.get("round_id")
        assert round_id != ""
        assert UUID_REGEX.match(round_id)

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    assert db_response is not None
    assert round_id == db_response.get("round_id")
    assert db_response.get("trump") == "NONE"
    assert db_response.get("bid_winner") is None
    assert isinstance(db_response.get("round_seq"), int)
    assert db_response.get("bid") == 20


def test_game_round_delete(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}/{round_id}' page is requested (DELETE)
    THEN check that the response is successful
    """
    # print(f"{app.config['SQLALCHEMY_DATABASE_URI']=}")

    # Create a new game
    db_response, status = game.create()
    assert status == 201
    assert db_response is not None
    game_id = db_response.get("game_id")

    # Create a new round
    db_response, status = round_.create(game_id)
    assert status == 201
    assert db_response is not None
    round_id = db_response.get("round_id")

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    assert db_response is not None
    db_response = gameround.read_one(game_id, round_id)
    assert db_response is not None

    with app.test_client() as test_client:
        # Attempt to access the delete round api
        response = test_client.delete(f"/api/game/{game_id}/{round_id}")
        assert response.status == "200 OK"

        # Attempt to retrieve the now-deleted round id
        response = test_client.get(f"/api/game/{game_id}/{round_id}")
        assert response.status == "404 NOT FOUND"

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    assert db_response == {}
    # TODO: I don't understand the inconsistency here.
    with pytest.raises(exceptions.NotFound):
        db_response = gameround.read_one(game_id, round_id)


def test_round_read_all(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round' page is requested (GET)
    THEN check that the response is a list of UUID and contains the expected information
    """
    # print(f"{app.config['SQLALCHEMY_DATABASE_URI']=}")
    create_games = 2

    # Clear out ALL previous test data.
    db.drop_all()
    db.create_all()

    game_ids = []
    round_ids = []
    for __ in range(create_games):
        # Create a new game
        db_response, status = game.create()
        assert status == 201
        assert db_response is not None
        game_id = db_response.get("game_id")
        game_ids.append(game_id)

        for __ in range(create_games):
            # Create a new round
            db_response, status = round_.create(game_id)
            assert status == 201
            assert db_response is not None
            round_id = db_response.get("round_id")
            round_ids.append(round_id)
    assert len(game_ids) == create_games
    assert len(round_ids) == create_games * 2

    with app.test_client() as test_client:
        # Attempt to access the GET game api
        response = test_client.get("/api/round")
        assert response.status == "200 OK"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        r_round_id = response_data  # List of dicts
        assert len(r_round_id) >= create_games
        for item in r_round_id:
            assert item["round_id"] != ""
            assert item["round_id"] in round_ids
            assert UUID_REGEX.match(item.get("round_id"))

    # Verify the database agrees.
    db_response = round_.read_all()  # List of dicts
    assert db_response is not None
    for item in db_response:
        assert item["round_id"] in round_ids


def test_round_read_one(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}' page is requested (GET)
    THEN check that the response is a UUID and contains the expected information
    """
    # print(f"{app.config['SQLALCHEMY_DATABASE_URI']=}")

    # Create a new game
    db_response, status = game.create()
    assert status == 201
    assert db_response is not None
    game_id = db_response.get("game_id")

    # Create a new round
    db_response, status = round_.create(game_id)
    assert status == 201
    assert db_response is not None
    round_id = db_response.get("round_id")

    with app.test_client() as test_client:
        # Attempt to access the create round api
        response = test_client.get(f"/api/round/{round_id}")
        assert response.status == "200 OK"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        r_round_id = response_data.get("round_id")
        assert r_round_id != ""
        assert r_round_id == round_id
        assert UUID_REGEX.match(r_round_id)

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    assert db_response is not None
    assert round_id == db_response.get("round_id")
