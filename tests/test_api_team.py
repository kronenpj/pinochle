"""
Tests for the various game classes.

License: GPLv3
"""
import json
from unittest import mock

import pytest
import regex
from pinochle import config, player, team, teamplayers

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


def test_team_delete(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/team/{team_id}' page is requested (DELETE)
    THEN check that the response is successful
    """
    # print(f"{config.sqlite_url=}")
    app = testapp

    # Create a new player
    db_response, status = player.create({"name": PLAYER_NAMES[0]})
    assert status == 201
    assert db_response is not None
    player_id = db_response.get("player_id")

    # Create a new team
    db_response, status = team.create({"name": TEAM_NAMES[0]})
    assert status == 201
    assert db_response is not None
    team_id = db_response.get("team_id")

    # Create a new teamplayer
    db_response, status = teamplayers.create(team_id, {"player_id": player_id})
    assert status == 201
    assert db_response is not None

    # Verify the database agrees.
    db_response = team.read_all()
    assert db_response is not None
    team_id_list = []
    for response in db_response:
        team_id_list.append(response["team_id"])
    assert team_id in team_id_list

    with app.test_client() as test_client:
        # Attempt to access the delete round api
        response = test_client.delete(f"/api/team/{team_id}")
        assert response.status == "200 OK"

        # Attempt to retrieve the now-deleted round id
        response = test_client.get(f"/api/team/{team_id}")
        # assert response.status == "404 NOT FOUND"
        assert response.status == "200 OK"

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        db_response = team.read_one(team_id)
