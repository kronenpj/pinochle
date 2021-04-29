"""
Tests for the Pinochle game play routines.

License: GPLv3
"""
from random import choice

from pinochle import play_pinochle, roundteams, teamplayers
from pinochle.models import utils

# pragma: pytest: disable=wrong-import-order
import test_utils


def test_deal_to_players_w_kitty(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    # Retrieve the round's kitty hand
    round_info = utils.query_round(round_id=round_id)
    kitty_hand = str(round_info.hand_id)

    # Deal the cards
    play_pinochle.deal_pinochle(player_ids=player_ids, kitty_len=4, kitty_id=kitty_hand)

    # Inspect the results.
    kitty_cards = utils.query_hand_list(kitty_hand)
    assert len(kitty_cards) == 4
    for __, p_id in enumerate(player_ids):
        temp_player = utils.query_player(p_id)
        cards = utils.query_hand_list(temp_player.hand_id)
        assert len(cards) == 11


def test_deal_to_players_no_kitty(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    # Deal the cards
    play_pinochle.deal_pinochle(player_ids=player_ids)

    # Inspect the results.
    for __, p_id in enumerate(player_ids):
        temp_player = utils.query_player(p_id)
        cards = utils.query_hand_list(temp_player.hand_id)
        assert len(cards) == 12
