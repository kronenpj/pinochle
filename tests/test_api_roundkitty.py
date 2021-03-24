"""
Tests for the various round/kitty classes.

License: GPLv3
"""
import json
import uuid

import pytest
from pinochle import hand, round_, roundkitty
from pinochle.models.round_ import Round

# pylint: disable=wrong-import-order
from werkzeug import exceptions

import test_utils

# from pinochle.models.utils import dump_db


def test_roundkitty_read(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    # Create a new game
    game_id = test_utils.create_game(4)

    # Create a new round
    round_id = test_utils.create_round(game_id)
    assert test_utils.UUID_REGEX.match(round_id)

    # Retrieve the generated hand_id (as a UUID object).
    hand_id = Round.query.filter(Round.round_id == round_id).all()[0].hand_id

    # Populate Hand with cards.
    for card in test_utils.CARD_LIST:
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
        assert cards == test_utils.CARD_LIST

    # Verify the database agrees.
    db_response = hand.read_one(hand_id)
    assert db_response is not None
    assert hand_id == db_response.get("hand_id")
    assert db_response.get("cards") == test_utils.CARD_LIST



def test_roundkitty_read2(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    # Create a new game
    game_id = test_utils.create_game(4)

    # Create a new round
    round_id = test_utils.create_round(game_id)
    assert test_utils.UUID_REGEX.match(round_id)

    # Retrieve the generated hand_id (as a UUID object).
    hand_id = Round.query.filter(Round.round_id == round_id).all()[0].hand_id

    # Populate Hand with cards.
    hand.addcards(str(hand_id), test_utils.CARD_LIST)

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
        assert cards == test_utils.CARD_LIST

    # Verify the database agrees.
    db_response = hand.read_one(hand_id)
    assert db_response is not None
    assert hand_id == db_response.get("hand_id")
    assert db_response.get("cards") == test_utils.CARD_LIST


def test_roundkitty_delete(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (DELETE)
    THEN check that the response is successful
    """
    # Create a new game
    game_id = test_utils.create_game(4)
    assert test_utils.UUID_REGEX.match(game_id)

    # Create a new round
    round_id = test_utils.create_round(game_id)
    assert test_utils.UUID_REGEX.match(round_id)

    # Retrieve the generated hand_id (as a UUID object).
    hand_uuid = Round.query.filter(Round.round_id == round_id).all()

    assert hand_uuid is not None
    assert hand_uuid != []
    hand_id = str(hand_uuid[0].hand_id)
    print(f"round_id={round_id} hand_id={hand_id}")

    # Populate Hand with cards.
    for card in test_utils.CARD_LIST:
        hand.addcard(hand_id, card)

    # Verify the database agrees.
    db_response = hand.read_one(hand_id)
    assert db_response is not None
    assert hand_id == db_response.get("hand_id")
    assert db_response.get("cards") == test_utils.CARD_LIST

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


def test_roundkitty_read_missing(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    # Create a new round
    round_id = str(uuid.uuid4())

    # Retrieve the generated hand_id (as a UUID object).
    hand_id = str(uuid.uuid4())

    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.get(f"/api/round/{round_id}/kitty")
        assert response.status == "204 NO CONTENT"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        assert response.get_data(as_text=True) == ""

    # Verify the database agrees.
    db_response = hand.read_one(hand_id)
    assert db_response is None


def test_roundkitty_delete_missing(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (DELETE)
    THEN check that the response is successful
    """
    # Create a new round
    round_id = str(uuid.uuid4())

    # Retrieve the generated hand_id (as a UUID object).
    hand_id = str(uuid.uuid4())

    # Verify the database agrees.
    db_response = hand.read_one(hand_id)
    assert db_response is None

    with app.test_client() as test_client:
        # Attempt to access the delete round api
        response = test_client.delete(f"/api/round/{round_id}/kitty")
        assert response.status == "204 NO CONTENT"

        # Attempt to retrieve the now-deleted round id
        response = test_client.get(f"/api/round/{round_id}/kitty")
        assert response.status == "204 NO CONTENT"

        assert response.data is not None
        response_str = response.get_data(as_text=True)
        assert response_str == ""

    # Verify the database agrees.
    db_response = roundkitty.read(round_id)
    assert db_response is None
    with pytest.raises(exceptions.NotFound):
        round_.read_one(round_id)
