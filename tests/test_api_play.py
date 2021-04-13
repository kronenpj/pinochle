"""
Tests for the various round classes.

License: GPLv3
"""
import json
import uuid
from random import choice

import pytest
from pinochle import gameround, player, round_, roundteams, teamplayers
from pinochle.cards.const import SUITS
from pinochle.models import utils
from pinochle.models.core import db

# pylint: disable=wrong-import-order
from werkzeug import exceptions

from . import test_utils

# from pinochle.models.utils import dump_db


def test_update_bid(app):
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
        player.update(player_id, {"bidding": True})

    # Create new teams
    team_ids = []
    for __ in range(len(test_utils.TEAM_NAMES)):
        team_id = test_utils.create_team(choice(test_utils.TEAM_NAMES))
        team_ids.append(team_id)

    # Join the players to the teams.
    for idx, player_id in enumerate(player_ids):
        test_utils.create_teamplayer(team_ids[idx % 2], player_id)

    # Join the teams to the round.
    test_utils.create_roundteam(round_id, team_ids)

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
        player.update(player_id, {"bidding": True})

    # Create a new team
    team_ids = []
    for __ in range(len(test_utils.TEAM_NAMES)):
        team_id = test_utils.create_team(choice(test_utils.TEAM_NAMES))
        team_ids.append(team_id)

    # Join the player to the team.
    for idx, player_id in enumerate(player_ids):
        test_utils.create_teamplayer(team_ids[idx % 2], player_id)

    # Join the teams to the round.
    test_utils.create_roundteam(round_id, team_ids)

    # Set the first dealer
    # Maybe...
    temp_list = utils.query_player_ids_for_round(round_id)
    assert len(temp_list) == 4

    # Populate the bid
    bid = -2
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


def test_set_trump(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/play/{round_id}/set_trump' page is requested (PUT)
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
    trump = choice(SUITS).capitalize().rstrip("s")
    player_id = choice(player_ids)
    round_.update(round_id, {"bid_winner": player_id})
    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.put(
            f"/api/play/{round_id}/set_trump?player_id={player_id}&trump={trump}"
        )
        assert response.status == "200 OK"
        response_str = response.get_data(as_text=True)
        assert "trump" in response_str
        response_data = json.loads(response_str)
        db_trump = response_data.get("trump")
        assert db_trump == trump
        print(f"trump={db_trump}")


def test_set_trump_bad_suit(app):
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
    trump = "Unics"
    player_id = choice(player_ids)
    round_.update(round_id, {"bid_winner": player_id})
    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.put(
            f"/api/play/{round_id}/set_trump?player_id={player_id}&trump={trump}"
        )
        assert response.status == "409 CONFLICT"
        response_str = response.get_data(as_text=True)
        assert "Clubs" in response_str

        # Verify the database is unchanged
        temp_round = utils.query_round(round_id)
        assert temp_round.trump == "NONE"
        print(f"trump={temp_round.trump}")


def test_set_trump_invalid_player(app):
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
    trump = choice(SUITS)
    player_id = str(uuid.uuid4())
    round_.update(round_id, {"bid_winner": uuid.uuid4()})
    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.put(
            f"/api/play/{round_id}/set_trump?player_id={player_id}&trump={trump}"
        )
        assert response.status == "404 NOT FOUND"
        response_str = response.get_data(as_text=True)
        assert "not found" in response_str

        # Verify the database is unchanged
        temp_round = utils.query_round(round_id)
        assert temp_round.trump == "NONE"
        print(f"trump={temp_round.trump}")
