"""
Tests for the various game classes.

License: GPLv3
"""
import json
from unittest import mock

import pytest
import regex
from pinochle import config, player

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
