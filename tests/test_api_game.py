"""
Tests for the various game classes.

License: GPLv3
"""
import json
import uuid
from unittest.mock import MagicMock

import pytest
from werkzeug import exceptions

from pinochle import game
from pinochle.models.core import db
from pinochle.play_pinochle import GAME_MODES

from . import test_utils

# from pinochle.models.utils import dump_db


def test_game_create(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game' page is requested (POST)
    THEN check that the response is a UUID
    """
    with app.test_client() as test_client:
        # Attempt to access the create game api
        response = test_client.post("/api/game?kitty_size=4")
        assert response.status == "201 CREATED"
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        assert response_str is not None
        response_data = json.loads(response_str)

        game_id = response_data["game_id"]
        assert game_id != ""
        assert test_utils.UUID_REGEX.match(game_id)

    # Verify the database agrees.
    db_response = game.read_one(game_id)
    assert db_response is not None
    assert game_id == db_response.get("game_id")
    assert db_response.get("kitty_size") == 4
    assert db_response.get("state") == 0


def test_game_delete(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game' page is requested (DELETE)
    THEN check that the response is a UUID
    """
    # Create a new game
    game_id = test_utils.create_game(0)

    with app.test_client() as test_client:
        # Attempt to access the delete game api
        response = test_client.delete(f"/api/game/{game_id}")
        assert response.status == "200 OK"

        # Attempt to retrieve the now-deleted game id
        response = test_client.get(f"/api/game/{game_id}")
        assert response.status == "404 NOT FOUND"

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        db_response = game.read_one(game_id)
        assert db_response is not None


def test_game_update_kitty_size(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}' page is requested (PUT)
    THEN check that the response is a UUID
    """
    new_kitty = 10
    # Create a new game
    game_id = test_utils.create_game(0)

    with app.test_client() as test_client:
        # Attempt to access the delete game api
        response = test_client.put(f"/api/game/{game_id}?kitty_size={new_kitty}")
        assert response.status == "200 OK"

    # Verify the database agrees.
    db_response = game.read_one(game_id)
    assert db_response is not None
    assert game_id == db_response.get("game_id")
    assert new_kitty == db_response.get("kitty_size")


def test_game_update_state(app, patch_geventws):  # pylint: disable=unused-argument
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}?state' page is requested (PUT)
    THEN check that the response is valid
    """
    game.send_game_state_message = MagicMock()

    # Create a new game
    game_id = test_utils.create_game(0)

    # Verify the database agrees.
    db_response = game.read_one(game_id)
    initial_state = db_response.get("state")
    assert initial_state == 0
    state = initial_state + 1

    with app.test_client() as test_client:
        # Attempt to access the advance state game api
        response = test_client.put(f"/api/game/{game_id}?state=true")
        assert response.status == "200 OK"

    # Make sure the WS message went out
    game.send_game_state_message.assert_called_with(game_id, state)
    # Verify the database agrees.
    db_response = game.read_one(game_id)
    assert db_response is not None
    assert game_id == db_response.get("game_id")
    assert state == db_response.get("state")


def test_game_update_state_wrap(app, patch_geventws):  # pylint: disable=unused-argument
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}?state' page is requested (PUT)
    THEN check that the response is valid
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    # Set state to the last one available.
    test_utils.set_game_state(game_id, len(GAME_MODES))

    # Verify the database agrees.
    db_response = game.read_one(game_id)
    initial_state = db_response.get("state")
    assert len(GAME_MODES) == initial_state

    with app.test_client() as test_client:
        # Attempt to access the delete game api
        response = test_client.put(f"/api/game/{game_id}?state=true")
        assert response.status == "200 OK"

    # Verify the database agrees.
    db_response = game.read_one(game_id)
    assert db_response is not None
    assert game_id == db_response.get("game_id")
    assert db_response.get("state") == 1


def test_game_update_state_no_change(
    app, patch_geventws
):  # pylint: disable=unused-argument
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}?state' page is requested (PUT)
    THEN check that the response is valid
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    # Set state to the last one available.
    test_utils.set_game_state(game_id, len(GAME_MODES))

    # Verify the database agrees.
    db_response = game.read_one(game_id)
    initial_state = db_response.get("state")
    assert len(GAME_MODES) == initial_state

    with app.test_client() as test_client:
        # Attempt to access the delete game api
        response = test_client.put(f"/api/game/{game_id}?state=false")
        assert response.status == "200 OK"

    # Verify the database agrees.
    db_response = game.read_one(game_id)
    assert db_response is not None
    assert game_id == db_response.get("game_id")
    assert db_response.get("state") == initial_state


def test_game_update_invalid_game(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}' page is requested (PUT)
    THEN check that the response is a UUID
    """
    # Create a new game
    game_id = str(uuid.uuid4())

    with app.test_client() as test_client:
        new_kitty = 12
        # Attempt to access the set kitty size game api
        response = test_client.put(f"/api/game/{game_id}?kitty_size={new_kitty}")
        assert response.status == "404 NOT FOUND"

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        game.read_one(game_id)


def test_game_read_all(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game' page is requested (GET)
    THEN check that the response is a list of UUID and contains the expected information
    """
    create_games = 5

    # Clear out ALL previous test data.
    db.drop_all()
    db.create_all()

    game_ids = []
    for __ in range(create_games):
        # Create two new games
        db_response, status = game.create(4)
        assert status == 201
        assert db_response is not None
        game_id = db_response.get("game_id")
        game_ids.append(game_id)
    assert len(game_ids) == create_games

    with app.test_client() as test_client:
        # Attempt to access the GET game api
        response = test_client.get("/api/game")
        assert response.status == "200 OK"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        r_game_id = response_data  # List of dicts
        assert len(r_game_id) >= create_games
        for item in r_game_id:
            assert item["game_id"] != ""
            assert item["game_id"] in game_ids
            assert test_utils.UUID_REGEX.match(item.get("game_id"))

    # Verify the database agrees.
    db_response = game.read_all()  # List of dicts
    assert db_response is not None
    for item in db_response:
        assert item["game_id"] in game_ids


def test_game_read_one(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}' page is requested (GET)
    THEN check that the response is a UUID and contains the expected information
    """
    # Create a new game
    db_response, status = game.create(4)
    assert status == 201
    assert db_response is not None
    game_id = db_response.get("game_id")

    with app.test_client() as test_client:
        # Attempt to access the create round api
        response = test_client.get(f"/api/game/{game_id}")
        assert response.status == "200 OK"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        r_game_id = response_data.get("game_id")
        assert r_game_id != ""
        assert r_game_id == game_id
        assert test_utils.UUID_REGEX.match(r_game_id)

    # Verify the database agrees.
    db_response = game.read_one(game_id)
    assert db_response is not None
    assert game_id == db_response.get("game_id")


def test_game_read_one_missing(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}' page is requested (GET) with non-existent game_id
    THEN check that the response is correct
    """
    game_id = str(uuid.uuid4())

    with app.test_client() as test_client:
        # Attempt to access the create round api
        response = test_client.get(f"/api/game/{game_id}")
        assert response.status == "404 NOT FOUND"

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        db_response = game.read_one(game_id)
        assert db_response is not None


def test_game_delete_missing(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}' page is requested (DELETE) with non-existent game_id
    THEN check that the response is correct
    """
    # Create a new game
    game_id = str(uuid.uuid4())

    with app.test_client() as test_client:
        # Attempt to access the delete game api
        response = test_client.delete(f"/api/game/{game_id}")
        assert response.status == "404 NOT FOUND"

        # Attempt to retrieve the now-deleted game id
        response = test_client.get(f"/api/game/{game_id}")
        assert response.status == "404 NOT FOUND"

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        db_response = game.read_one(game_id)
        assert db_response is not None


def test_game_read_all_empty(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}' page is requested (GET)
    THEN check that the response is empty
    """
    # Clear out ALL previous test data.
    db.drop_all()
    db.create_all()

    with app.test_client() as test_client:
        # Attempt to access the create round api
        response = test_client.get("/api/game")
        assert response.status == "200 OK"
        assert response.get_data(as_text=True) == "[]\n"

    # Verify the database agrees.
    db_response = game.read_all()
    assert db_response is not None
    assert db_response == []
