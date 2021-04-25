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
    # Create a new game
    game_id = test_utils.create_game(kitty_size=4)

    # Create a new round
    round_id = test_utils.create_round(game_id)

    # Create new teams
    team_ids = []
    for __ in range(len(test_utils.TEAM_NAMES)):
        team_id = test_utils.create_team(choice(test_utils.TEAM_NAMES))
        team_ids.append(team_id)

    # Create new players
    player_ids = []
    for __ in range(len(test_utils.PLAYER_NAMES)):
        player_id = test_utils.create_player(choice(test_utils.PLAYER_NAMES))
        player_ids.append(player_id)

    # Create the roundteam association for the teams.
    roundteams.create(round_id=round_id, teams=team_ids)

    # Retrieve the round's kitty hand
    round_info = utils.query_round(round_id=round_id)
    kitty_hand = str(round_info.hand_id)

    # Create the team player associations.
    p_index = 0
    for team_id in team_ids:
        teamplayers.create(
            team_id=team_id, player_id={"player_id": player_ids[p_index]}
        )
        p_index += 1
        teamplayers.create(
            team_id=team_id, player_id={"player_id": player_ids[p_index]}
        )
        p_index += 1

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
    # Create a new game
    game_id = test_utils.create_game(kitty_size=0)

    # Create a new round
    round_id = test_utils.create_round(game_id)

    # Create a new teams
    team_ids = []
    for __ in range(len(test_utils.TEAM_NAMES)):
        team_id = test_utils.create_team(choice(test_utils.TEAM_NAMES))
        team_ids.append(team_id)

    # Create new players
    player_ids = []
    for __ in range(len(test_utils.PLAYER_NAMES)):
        player_id = test_utils.create_player(choice(test_utils.PLAYER_NAMES))
        player_ids.append(player_id)

    # Create the roundteam association for the teams.
    roundteams.create(round_id=round_id, teams=team_ids)

    # Create the team player associations.
    p_index = 0
    for team_id in team_ids:
        teamplayers.create(
            team_id=team_id, player_id={"player_id": player_ids[p_index]}
        )
        p_index += 1
        teamplayers.create(
            team_id=team_id, player_id={"player_id": player_ids[p_index]}
        )
        p_index += 1

    # Deal the cards
    play_pinochle.deal_pinochle(player_ids=player_ids)

    # Inspect the results.
    for __, p_id in enumerate(player_ids):
        temp_player = utils.query_player(p_id)
        cards = utils.query_hand_list(temp_player.hand_id)
        assert len(cards) == 12
