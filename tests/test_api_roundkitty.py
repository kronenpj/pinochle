"""
Tests for the various game classes.

License: GPLv3
"""
import json
from unittest import mock

import pytest
import regex
from pinochle import config, game, hand, round_, roundkitty
from pinochle.models import Round

UUID_REGEX_TEXT = r"^([a-f\d]{8}(-[a-f\d]{4}){3}-[a-f\d]{12}?)$"
UUID_REGEX = regex.compile(UUID_REGEX_TEXT)

CARD_LIST = ["club_9", "diamond_ace", "heart_jack", "spade_10"]


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


def test_roundkitty_read(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    # print(f"{config.sqlite_url=}")
    app = testapp

    # Create a new game
    db_response, status = game.create()
    assert status == 201
    assert db_response is not None
    game_id = db_response.get("game_id")
    assert UUID_REGEX.match(game_id)

    # Create a new round
    db_response, status = round_.create(game_id)
    assert status == 201
    assert db_response is not None
    round_id = db_response.get("round_id")
    assert UUID_REGEX.match(round_id)

    # Retrieve the generated hand_id (as a UUID object).
    hand_id = Round.query.filter(Round.round_id == round_id).all()[0].hand_id

    # Populate Hand with cards.
    for card in CARD_LIST:
        hand.addcard(str(hand_id), card)

    with app.test_client() as test_client:
        # Attempt to access the create round api
        response = test_client.get(f"/api/round/{round_id}/kitty")
        assert response.status == "200 OK"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        cards = response_data.get("cards")
        assert cards is not None
        assert cards != ""
        assert cards == CARD_LIST

    # Verify the database agrees.
    db_response = hand.read_one(hand_id)
    assert db_response is not None
    assert hand_id == db_response.get("hand_id")
    assert db_response.get("cards") == CARD_LIST


def test_roundkitty_delete(testapp):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (DELETE)
    THEN check that the response is successful
    """
    # print(f"{config.sqlite_url=}")
    app = testapp

    # Create a new game
    db_response, status = game.create()
    assert status == 201
    assert db_response is not None
    game_id = db_response.get("game_id")
    assert UUID_REGEX.match(game_id)

    # Create a new round
    db_response, status = round_.create(game_id)
    assert status == 201
    assert db_response is not None
    round_id = db_response.get("round_id")
    assert UUID_REGEX.match(round_id)

    # Retrieve the generated hand_id (as a UUID object).
    hand_id = Round.query.filter(Round.round_id == round_id).all()[0].hand_id
    hand_id = str(hand_id)

    # Populate Hand with cards.
    for card in CARD_LIST:
        hand.addcard(hand_id, card)

    # Verify the database agrees.
    db_response = hand.read_one(hand_id)
    assert db_response is not None
    assert hand_id == db_response.get("hand_id")
    assert db_response.get("cards") == CARD_LIST

    with app.test_client() as test_client:
        # Attempt to access the delete round api
        response = test_client.delete(f"/api/round/{round_id}/kitty")
        assert response.status == "204 NO CONTENT"

        # Attempt to retrieve the now-deleted round id
        response = test_client.get(f"/api/round/{round_id}/kitty")
        assert response.status == "200 OK"

        assert response.data is not None
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        cards = response_data.get("cards")
        assert cards is not None
        assert cards == []

    # Verify the database agrees.
    db_response = roundkitty.read(round_id)
    assert db_response == {"cards": []}
    db_response = round_.read_one(round_id)
    assert db_response.get("hand_id") is None
