"""
Tests for the various game classes.

License: GPLv3
"""
import json
from unittest import mock

import pytest
import regex
from pinochle import config, game, round_, gameround

# pylint: disable=wrong-import-order
from werkzeug import exceptions

UUID_REGEX_TEXT = r"^([a-f\d]{8}(-[a-f\d]{4}){3}-[a-f\d]{12}?)$"
UUID_REGEX = regex.compile(UUID_REGEX_TEXT)

TEAM_NAMES = ["Us", "Them"]
PLAYER_NAMES = ["Thing1", "Thing2", "Red", "Blue"]
N_TEAMS = len(TEAM_NAMES)
N_PLAYERS = len(PLAYER_NAMES)
N_KITTY = 4


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


def test_round_create(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round' page is requested (POST)
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


def test_game_round_delete(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}/{round_id}' page is requested (DELETE)
    THEN check that the response is successful
    """
    # print(f"{config.sqlite_url=}")
    app = testapp

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


def test_round_read_all(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round' page is requested (GET)
    THEN check that the response is a list of UUID and contains the expected information
    """
    # print(f"{config.sqlite_url=}")
    create_games = 2

    # Clear out ALL previous test data.
    config.db.drop_all()
    config.db.create_all()
    app = testapp

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


def test_round_read_one(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}' page is requested (GET)
    THEN check that the response is a UUID and contains the expected information
    """
    # print(f"{config.sqlite_url=}")
    app = testapp

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
