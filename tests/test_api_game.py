"""
Tests for the various game classes.

License: GPLv3
"""
import json
from unittest import mock

import pytest
import regex
from pinochle import config, game

# pylint: disable=wrong-import-order
from werkzeug import exceptions

UUID_REGEX_TEXT = r"^([a-f\d]{8}(-[a-f\d]{4}){3}-[a-f\d]{12}?)$"
UUID_REGEX = regex.compile(UUID_REGEX_TEXT)


# Pylint doesn't pick up on this fixture.
# pylint: disable=redefined-outer-name
@pytest.fixture(scope="module")
def testapp():
    """
    Fixture to create an in-memory database and make it available only for the set of
    tests in this file. The database is not recreated between tests so tests can
    interfere with each other. Changing the fixture's scope to "package" or "session"
    makes no difference in the persistence of the database between tests in this file.
    A scope of "class" behaves the same way as "function".

    :yield: The application being tested with the temporary database.
    :rtype: FlaskApp
    """
    # print("Entering testapp...")
    with mock.patch(
        "pinochle.config.sqlite_url", "sqlite://"  # In-memory
    ), mock.patch.dict(
        "pinochle.server.connex_app.app.config",
        {"SQLALCHEMY_DATABASE_URI": "sqlite://"},
    ):
        app = config.connex_app.app

        config.db.create_all()

        # print("Testapp, yielding app")
        yield app


def test_game_create(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game' page is requested (POST)
    THEN check that the response is a UUID
    """
    # print(f"{config.sqlite_url=}")
    app = testapp

    with app.test_client() as test_client:
        # Attempt to access the create game api
        response = test_client.post("/api/game")
        assert response.status == "201 CREATED"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        game_id = response_data.get("game_id")
        assert game_id != ""
        assert UUID_REGEX.match(game_id)

    # Verify the database agrees.
    db_response = game.read_one(game_id)
    assert db_response is not None
    assert game_id == db_response.get("game_id")


def test_game_delete(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game' page is requested (DELETE)
    THEN check that the response is a UUID
    """
    # print(f"{config.sqlite_url=}")
    app = testapp

    # Create a new game
    db_response, status = game.create()
    assert status == 201
    assert db_response is not None
    game_id = db_response.get("game_id")

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


def test_game_read_all(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game' page is requested (GET)
    THEN check that the response is a list of UUID and contains the expected information
    """
    # print(f"{config.sqlite_url=}")
    create_games = 5

    # Clear out ALL previous test data.
    config.db.drop_all()
    config.db.create_all()
    app = testapp

    game_ids = []
    for __ in range(create_games):
        # Create two new games
        db_response, status = game.create()
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
            assert UUID_REGEX.match(item.get("game_id"))

    # Verify the database agrees.
    db_response = game.read_all()  # List of dicts
    assert db_response is not None
    for item in db_response:
        assert item["game_id"] in game_ids


def test_game_read_one(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}' page is requested (GET)
    THEN check that the response is a UUID and contains the expected information
    """
    # print(f"{config.sqlite_url=}")
    app = testapp

    # Create a new game
    db_response, status = game.create()
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
        assert UUID_REGEX.match(r_game_id)

    # Verify the database agrees.
    db_response = game.read_one(game_id)
    assert db_response is not None
    assert game_id == db_response.get("game_id")
