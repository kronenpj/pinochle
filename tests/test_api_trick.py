"""
Tests for the various trick classes.

License: GPLv3
"""

import pytest
from pinochle import trick
from pinochle.cards.const import SUITS
from pinochle.models import utils

# pylint: disable=wrong-import-order
from werkzeug import exceptions

import test_utils

# from pinochle.models.utils import dump_db


def test_trick_create(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/trick' page is requested (POST)
    THEN check that the response is a UUID and contains the expected information
    """
    # Create a new game
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    a_trick, _ = trick.create(round_id)
    trick_id = a_trick["trick_id"]

    t_trick = utils.query_trick_for_round_id(round_id)

    # Verify the database agrees.
    db_response = trick.read_one(a_trick["trick_id"])
    assert db_response is not None
    assert trick_id == db_response.get("trick_id")
    assert round_id == db_response.get("round_id")
