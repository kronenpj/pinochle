"""
Tests for the various game classes.

License: GPLv3
"""
import json
from unittest import mock

import pytest
import regex
from pinochle import game, player, round_, config, team
from werkzeug import exceptions

UUID_REGEX_TEXT = r"^([a-f\d]{8}(-[a-f\d]{4}){3}-[a-f\d]{12}?)$"
UUID_REGEX = regex.compile(UUID_REGEX_TEXT)

team_names = ["Us", "Them"]
player_names = ["Thing1", "Thing2", "Red", "Blue"]
n_teams = len(team_names)
n_players = len(player_names)
n_kitty = 4


# Pylint doesn't pick up on this fixture.
# pylint: disable=redefined-outer-name
@pytest.fixture(scope="module")
def testapp():
    """
    Fixture to create an in-memory database and make it available only for the set of 
    tests in this file. The database is not recreated between tests so tests can 
    interfere with each other. Changing the fixture's scope to "package" or "session" 
    makes no difference in the persistence of the database between tests. A scope of 
    "class" behaves the same way as "function".

    :yield: The application being tested with the temporary database.
    :rtype: FlaskApp
    """
    # print("Entering testapp...")
    with mock.patch(
        "pinochle.config.sqlite_url", f"sqlite://"  # In-memory
    ), mock.patch.dict(
        "pinochle.server.connex_app.app.config",
        {"SQLALCHEMY_DATABASE_URI": f"sqlite://"},
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
    WHEN the '/api/game' page is requested (POST)
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
    try:
        db_response = game.read_one(game_id)
    except exceptions.NotFound:
        pass
    assert "Did not throw expected exception." is int


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
    for _ in range(create_games):
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
    WHEN the '/api/game' page is requested (GET)
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


def test_round_create(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game' page is requested (POST)
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


def test_players_create(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/player' page is requested (POST)
    THEN check that the response is a UUID and contains the expected information
    """
    # print(f"{config.sqlite_url=}")
    app = testapp

    with app.test_client() as test_client:
        # Create a new player
        player_name = "Thing1"

        # Attempt to access the create player api
        post_data = {
            "player": player_name,
        }
        response = test_client.post(
            "/api/player", data=json.dumps(post_data), content_type="application/json",
        )
        assert response.status == "201 CREATED"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        player_id = response_data.get("player_id")
        assert player_id != ""
        assert UUID_REGEX.match(player_id)

        # Verify the database agrees.
        db_response = player.read_one(player_id)
        assert db_response is not None
        assert player_id == db_response.get("player_id")
        assert db_response.get("score") == 0
        assert player_name == db_response.get("name")


def test_team_create(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/team' page is requested (POST)
    THEN check that the response is a UUID and contains the expected information
    """
    # print(f"{config.sqlite_url=}")
    app = testapp

    with app.test_client() as test_client:
        # Create a new player
        team_name = "Team1"

        # Attempt to access the create player api
        post_data = {
            "team": team_name,
        }
        response = test_client.post(
            "/api/team", data=json.dumps(post_data), content_type="application/json",
        )
        assert response.status == "201 CREATED"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        team_id = response_data.get("team_id")
        assert team_id != ""
        assert UUID_REGEX.match(team_id)

        # Verify the database agrees.
        db_response = team.read_one(team_id)
        assert db_response is not None
        assert team_id == db_response.get("team_id")
        assert db_response.get("score") == 0
        # print(f"{db_response}")
        assert team_name == db_response.get("name")


def test_team_add_player(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/team' page is requested (POST)
    THEN check that the response is a UUID and contains the expected information
    """
    # print(f"{config.sqlite_url=}")
    app = testapp

    # Create a new team and player
    player_name = "Thing2"
    team_name = "Team2"

    # Create a new player
    db_response, status = player.create({"player": player_name})
    assert status == 201
    assert db_response is not None
    player_id = db_response.get("player_id")

    # Create a new team
    db_response, status = team.create({"team": team_name})
    assert status == 201
    assert db_response is not None
    team_id = db_response.get("team_id")

    with app.test_client() as test_client:

        # Attempt to access the create player api
        post_data = {
            "player_id": player_id,
        }
        response = test_client.post(
            f"/api/team/{team_id}",
            data=json.dumps(post_data),
            content_type="application/json",
        )
        assert response.status == "201 CREATED"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        team_id = response_data.get("team_id")
        assert team_id != ""
        assert UUID_REGEX.match(team_id)

        # Verify the database agrees.
        db_response = team.read_one(team_id)
        assert db_response is not None
        assert team_id == db_response.get("team_id")
        assert db_response.get("score") == 0
        assert team_name == db_response.get("name")
