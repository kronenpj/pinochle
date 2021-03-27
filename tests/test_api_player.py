"""
Tests for the various player classes.

License: GPLv3
"""
import json
import uuid
from random import choice

import pytest
from pinochle import hand, player
from pinochle.models import utils
from pinochle.models.core import db
from pinochle.models.player import Player

# pylint: disable=wrong-import-order
from werkzeug import exceptions

import test_utils

# from pinochle.models.utils import dump_db


def test_players_create(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/player' page is requested (POST)
    THEN check that the response is a UUID and contains the expected information
    """
    with app.test_client() as test_client:
        # Create a new player
        player_name = choice(test_utils.PLAYER_NAMES)

        # Attempt to access the create player api
        post_data = {
            "name": player_name,
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
        assert test_utils.UUID_REGEX.match(player_id)

        # Verify the database agrees.
        db_response = player.read_one(player_id)
        assert db_response is not None
        assert player_id == db_response.get("player_id")
        assert db_response.get("meld_score") == 0
        assert player_name == db_response.get("name")


def test_players_read_one(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/player/{player_id}' page is requested (GET)
    THEN check that the response is a UUID and contains the expected information
    """
    player_ids = {}
    # Create a new player
    for player_name in test_utils.PLAYER_NAMES:
        # Create a new game
        player_id = test_utils.create_player(player_name)
        assert test_utils.UUID_REGEX.match(player_id)
        player_ids[player_id] = player_name

    with app.test_client() as test_client:
        # Attempt to access the read player api
        for player_id in player_ids:
            response = test_client.get(f"/api/player/{player_id}")
            assert response.status == "200 OK"
            assert response.get_data(as_text=True) is not None
            # This is a JSON formatted STRING
            response_str = response.get_data(as_text=True)
            response_data = json.loads(response_str)
            player_name = response_data.get("name")
            assert player_name is not None
            assert player_name != ""
            assert player_name == player_ids[player_id]

            # Verify the database agrees.
            db_response = player.read_one(player_id)
            assert db_response is not None
            assert player_id == db_response.get("player_id")
            assert db_response.get("meld_score") == 0
            assert player_name == db_response.get("name")


def test_players_delete_one(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/player/{player_id}' page is requested (DELETE)
    THEN check that the response contains the expected information
    """
    player_ids = {}
    # Create a new player
    for player_name in test_utils.PLAYER_NAMES:
        # Create a new game
        db_response, status = player.create({"name": player_name})
        assert status == 201
        assert db_response is not None
        player_id = db_response.get("player_id")
        assert test_utils.UUID_REGEX.match(player_id)
        player_ids[player_id] = player_name

    with app.test_client() as test_client:
        # Attempt to access the delete player api
        for player_id in player_ids:
            response = test_client.delete(f"/api/player/{player_id}")
            assert response.status == "200 OK"
            assert response.get_data(as_text=True) is not None
            # This is a JSON formatted STRING
            response_str = response.get_data(as_text=True)
            assert response_str is not None
            assert response_str != ""
            assert player_id in response_str

            # Verify the database agrees.
            with pytest.raises(exceptions.NotFound):
                db_response = player.read_one(player_id)


def test_players_read_all(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/player' page is requested (GET)
    THEN check that the response contains the expected information
    """
    # Clear out ALL previous test data.
    db.drop_all()
    db.create_all()

    player_ids = {}
    # Create a new player
    for player_name in test_utils.PLAYER_NAMES:
        # Create a new game
        db_response, status = player.create({"name": player_name})
        assert status == 201
        assert db_response is not None
        player_id = db_response.get("player_id")
        assert test_utils.UUID_REGEX.match(player_id)
        player_ids[player_id] = player_name

    with app.test_client() as test_client:
        # Attempt to access the read player api
        response = test_client.get("/api/player")
        assert response.status == "200 OK"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        assert len(test_utils.PLAYER_NAMES) == len(response_data)

        for response_item in response_data:
            player_uuid = response_item.get("player_id")
            assert player_uuid is not None
            assert player_uuid != ""
            assert player_uuid in list(player_ids.keys())
            player_name = response_item.get("name")
            assert player_name is not None
            assert player_name != ""
            assert player_name in list(player_ids.values())

            # Verify the database agrees.
            db_response = player.read_one(player_uuid)
            assert db_response is not None
            assert player_uuid == db_response.get("player_id")
            assert db_response.get("meld_score") == 0
            assert player_name == db_response.get("name")


def test_players_read_hand(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/player/{player_id}/hand' page is requested (GET)
    THEN check that the response is a list of strs
    """
    # Create a new player
    player_name = choice(test_utils.PLAYER_NAMES)
    player_id = test_utils.create_player(player_name)
    assert test_utils.UUID_REGEX.match(player_id)
    player_data = utils.query_player(player_id=player_id)

    card_qty = 5
    card_choice = []
    for _ in range(card_qty):
        temp_card = choice(test_utils.CARD_LIST)
        card_choice.append(temp_card)
        player.addcard(player_id=player_id, card={"card": temp_card})

    with app.test_client() as test_client:
        # Attempt to access the read player api
        response = test_client.get(f"/api/player/{player_id}/hand")
        assert response.status == "200 OK"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        assert len(response_data) == card_qty

        # Verify the database agrees.
        db_response = hand.read_one(player_data.hand_id)
        assert db_response is not None
        assert card_choice == db_response["cards"]


def test_players_add_card(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/player/{player_id}' page is requested (GET)
    THEN check that the response is a UUID and contains the expected information
    """
    # Create a new player
    player_name = choice(test_utils.PLAYER_NAMES)
    player_id = test_utils.create_player(player_name)
    assert test_utils.UUID_REGEX.match(player_id)
    card_choice = choice(test_utils.CARD_LIST)

    with app.test_client() as test_client:
        # Attempt to access the read player api
        put_data = {"card": card_choice}
        response = test_client.put(
            f"/api/player/{player_id}/hand",
            data=json.dumps(put_data),
            content_type="application/json",
        )
        assert response.status == "201 CREATED"

        # Verify the database agrees.
        p_player = Player.query.filter(Player.player_id == player_id).one_or_none()
        # Did we find a player?
        assert p_player is not None
        hand_id = p_player.hand_id

        db_response = hand.read_one(hand_id)
        assert db_response is not None
        assert card_choice in db_response["cards"]


def test_players_delete_card(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/player/{player_id}' page is requested (GET)
    THEN check that the response is a UUID and contains the expected information
    """
    # Create a new player
    player_name = choice(test_utils.PLAYER_NAMES)
    player_id = test_utils.create_player(player_name)
    assert test_utils.UUID_REGEX.match(player_id)
    card_choice = choice(test_utils.CARD_LIST)
    hand_id = test_utils.query_player_hand_id(player_id=player_id)
    hand.addcard(hand_id=hand_id, card=card_choice)

    # Verify the database agrees.
    db_response = hand.read_one(hand_id)
    assert db_response is not None
    assert card_choice in db_response["cards"]

    with app.test_client() as test_client:
        # Attempt to access the read player api
        response = test_client.delete(f"/api/player/{player_id}/hand/{card_choice}")
        assert response.status == "200 OK"

        # Verify the database agrees.
        p_player = Player.query.filter(Player.player_id == player_id).one_or_none()
        # Did we find a player?
        assert p_player is not None
        hand_id = p_player.hand_id

        db_response = hand.read_one(hand_id)
        assert db_response is None


def test_players_read_one_missing(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/player/{player_id}' page is requested (GET)
    THEN check that the response is a UUID and contains the expected information
    """
    player_id = str(uuid.uuid4())

    with app.test_client() as test_client:
        # Attempt to access the read player api
        response = test_client.get(f"/api/player/{player_id}")
        assert response.status == "404 NOT FOUND"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        player_name = response_data.get("name")
        assert player_name is None

        # Verify the database agrees.
        with pytest.raises(exceptions.NotFound):
            db_response = player.read_one(player_id)
            assert db_response is not None


def test_players_delete_one_missing(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/player/{player_id}' page is requested (DELETE)
    THEN check that the response contains the expected information
    """
    player_id = str(uuid.uuid4())

    with app.test_client() as test_client:
        # Attempt to access the delete player api
        response = test_client.delete(f"/api/player/{player_id}")
        assert response.status == "404 NOT FOUND"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        assert f"Player not found for Id {player_id}" not in response_str

        # Verify the database agrees.
        with pytest.raises(exceptions.NotFound):
            db_response = player.read_one(player_id)
            assert db_response is not None


def test_players_read_all_empty(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/player' page is requested (GET)
    THEN check that the response contains the expected information
    """
    # Clear out ALL previous test data.
    db.drop_all()
    db.create_all()

    with app.test_client() as test_client:
        # Attempt to access the read player api
        response = test_client.get("/api/player")
        assert response.status == "200 OK"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        assert len(response_data) == 0

        for response_item in response_data:
            player_uuid = response_item.get("player_id")
            assert player_uuid is None

            # Verify the database agrees.
            db_response = player.read_one(player_uuid)
            assert db_response is None
            assert player_uuid == db_response.get("player_id")
