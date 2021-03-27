"""
Tests for the various round classes.

License: GPLv3
"""
import json
import uuid
from random import choice

import pytest
from pinochle import gameround, round_, roundteams, teamplayers
from pinochle.models import utils
from pinochle.models.core import db

# pylint: disable=wrong-import-order
from werkzeug import exceptions

import test_utils

# from pinochle.models.utils import dump_db


def test_update_bid_valid(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/play/{round_id}/submit_bid' page is requested (PUT)
    THEN check that the response contains the expected information
    """
    # Create a new game
    game_id = test_utils.create_game(kitty_size=0)

    # Create a new round
    round_id = test_utils.create_round(game_id)

    # Create new players
    player_ids = []
    for __ in range(len(test_utils.PLAYER_NAMES)):
        player_id = test_utils.create_player(choice(test_utils.PLAYER_NAMES))
        player_ids.append(player_id)

    # Populate the bid
    bid = 21
    player_id = choice(player_ids)
    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.put(
            f"/api/play/{round_id}/submit_bid?player_id={player_id}&bid={bid}"
        )
        assert response.status == "200 OK"
        response_str = response.get_data(as_text=True)
        assert "bid_winner" in response_str
        assert "bid" in response_str
        response_data = json.loads(response_str)
        db_bid = response_data.get("bid")
        db_player = response_data.get("bid_winner")
        assert db_bid == bid
        assert db_player == player_id
        assert isinstance(db_bid, int)
        print(f"score={db_bid}")

def test_update_bid_low(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/play/{round_id}/submit_bid' page is requested (PUT)
    THEN check that the response contains the expected information
    """
    # Create a new game
    game_id = test_utils.create_game(kitty_size=0)

    # Create a new round
    round_id = test_utils.create_round(game_id)

    # Create new players
    player_ids = []
    for __ in range(len(test_utils.PLAYER_NAMES)):
        player_id = test_utils.create_player(choice(test_utils.PLAYER_NAMES))
        player_ids.append(player_id)

    # Populate the bid
    bid = -1
    player_id = choice(player_ids)
    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.put(
            f"/api/play/{round_id}/submit_bid?player_id={player_id}&bid={bid}"
        )
        assert response.status == "409 CONFLICT"
        response_str = response.get_data(as_text=True)
        assert "low" in response_str

        # Verify the database is unchanged
        temp_round = utils.query_round(round_id)
        assert temp_round.bid == 20
        assert temp_round.bid_winner is None
        print(f"score={temp_round.bid}")


def test_update_bid_invalid_player(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/play/{round_id}/submit_bid' page is requested (PUT)
    THEN check that the response contains the expected information
    """
    # Create a new game
    game_id = test_utils.create_game(kitty_size=0)

    # Create a new round
    round_id = test_utils.create_round(game_id)

    # Create new players
    bid = 21
    player_id = str(uuid.uuid4())
    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.put(
            f"/api/play/{round_id}/submit_bid?player_id={player_id}&bid={bid}"
        )
        assert response.status == "404 NOT FOUND"
        response_str = response.get_data(as_text=True)
        assert "Player" in response_str and "not found" in response_str

        # Verify the database is unchanged
        temp_round = utils.query_round(round_id)
        assert temp_round.bid == 20
        assert temp_round.bid_winner is None
        print(f"score={temp_round.bid}")
