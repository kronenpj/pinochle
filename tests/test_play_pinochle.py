"""
Tests for the Pinochle game play routines.

License: GPLv3
"""
import uuid
from random import choice
from unittest.mock import ANY, call

import pytest
from pinochle import play_pinochle, player
from pinochle.models import utils
from pinochle.models.hand import Hand
from pinochle.ws_messenger import WebSocketMessenger as WSM

# pylint: disable=wrong-import-order
from werkzeug import exceptions

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


def test_all_players_bidding(app, patch_geventws):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    # Gather the players still bidding.
    player_list = play_pinochle.players_still_bidding(round_id)
    assert len(player_list) == 0

    # Set all to bidding
    play_pinochle.set_players_bidding(player_ids)
    player_list = play_pinochle.players_still_bidding(round_id)
    assert len(player_list) == 4

    # Gather the players still bidding.
    play_pinochle.set_player_pass(str(choice(player_list)))
    player_list = play_pinochle.players_still_bidding(round_id)
    assert len(player_list) == 3


def test_player_bid_submission(app, patch_geventws):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    # Set all to bidding
    play_pinochle.set_players_bidding(player_ids)

    # Submit a bid
    play_pinochle.submit_bid(round_id, choice(player_ids), 21)
    player_list = play_pinochle.players_still_bidding(round_id)
    assert len(player_list) == 4

    # One player passes
    play_pinochle.submit_bid(round_id, choice(player_list), -1)
    player_list = play_pinochle.players_still_bidding(round_id)
    assert len(player_list) == 3

    # Another player passes
    play_pinochle.submit_bid(round_id, choice(player_list), -1)
    player_list = play_pinochle.players_still_bidding(round_id)
    assert len(player_list) == 2

    # Last player passes
    play_pinochle.submit_bid(round_id, choice(player_list), -1)
    player_list = play_pinochle.players_still_bidding(round_id)
    assert len(player_list) == 1
    a_game = utils.query_game(game_id)
    a_round = utils.query_round(round_id)
    assert a_game.state == 1
    assert a_round.bid == 21
    assert str(a_round.bid_winner) == player_list[0]


def test_submit_trump_not_bid_winner(app, patch_geventws):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    # Set all to bidding
    play_pinochle.set_players_bidding(player_ids)
    # Submit a valid bid for one player
    winner = choice(player_ids)
    play_pinochle.submit_bid(round_id, winner, 21)
    # Set three to pass, meaning one wins the bid.
    player_list = [x for x in player_ids if x != winner]
    # This didn't work:
    # map(lambda x: play_pinochle.submit_bid(round_id, x, -1), player_list)
    for item in player_list:
        play_pinochle.submit_bid(round_id, item, -1)

    assert len(play_pinochle.players_still_bidding(round_id)) == 1

    a_round = utils.query_round(round_id)
    with pytest.raises(exceptions.Conflict):
        play_pinochle.set_trump(round_id, choice(player_list), "diamond")

    play_pinochle.set_trump(round_id, winner, "spade")
    a_round = utils.query_round(round_id)
    assert a_round.bid == 21
    assert a_round.trump == "spade"


def test_submit_bid_invalid_round(app, patch_geventws):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    # Set all to bidding
    play_pinochle.set_players_bidding(player_ids)

    # Submit a bid
    with pytest.raises(exceptions.NotFound):
        invalid_round = str(uuid.uuid4())
        play_pinochle.submit_bid(invalid_round, choice(player_ids), 21)


def test_meld_submissions(app, patch_ws_messenger_to_MM):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    for team_id in team_ids:
        assert utils.query_team(team_id).score == 0

    for player_id in player_ids:
        player.update(player_id, {"meld_score": choice([5, 10, 15, 20])})
        play_pinochle.finalize_meld(round_id, player_id)

    for team_id in team_ids:
        assert utils.query_team(team_id).score > 0
        assert utils.query_team(team_id).score % 5 == 0

    calls = [
        call(
            game_id,
            {
                "action": "team_score",
                "team_id": team_ids[0],
                "score": ANY,
                "meld_score": ANY,
            },
        ),
        call(
            game_id,
            {
                "action": "team_score",
                "team_id": team_ids[1],
                "score": ANY,
                "meld_score": ANY,
            },
        ),
    ]
    WSM.websocket_broadcast.assert_has_calls(calls, any_order=True)


def test_choose_winning_trick_card_follow_suit(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    t_UUID = "059f907f-ab46-4fe3-8b09-6387940404ef"
    t_trump = "Hearts"
    t_card_list = ["club_queen", "club_king", "club_10", "club_9"]
    t_hand_list = []

    for card in t_card_list:
        t_hand = Hand()
        t_hand.card = card
        t_hand.hand_id = t_UUID
        t_hand_list.append(t_hand)

    t_card = play_pinochle.find_winning_trick_card(t_hand_list, t_trump)
    assert t_card == "club_10"

    t_trump = "Clubs"
    t_card = play_pinochle.find_winning_trick_card(t_hand_list, t_trump)
    assert t_card == "club_10"


def test_choose_winning_trick_card_not_follow_suit(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    t_UUID = "059f907f-ab46-4fe3-8b09-6387940404ef"
    t_trump = "Hearts"
    t_card_list = ["club_queen", "heart_king", "spade_10", "diamond_ace"]
    t_hand_list = []

    for card in t_card_list:
        t_hand = Hand()
        t_hand.card = card
        t_hand.hand_id = t_UUID
        t_hand_list.append(t_hand)

    t_card = play_pinochle.find_winning_trick_card(t_hand_list, t_trump)
    assert t_card == "heart_king"

    t_trump = "Clubs"
    t_card = play_pinochle.find_winning_trick_card(t_hand_list, t_trump)
    assert t_card == "club_queen"


def test_choose_winning_trick_card_crafted(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    t_UUID = "059f907f-ab46-4fe3-8b09-6387940404ef"
    t_trump = "Hearts"
    t_card_list = ["diamond_9", "heart_king", "spade_10", "diamond_ace"]
    t_hand_list = []

    for card in t_card_list:
        t_hand = Hand()
        t_hand.card = card
        t_hand.hand_id = t_UUID
        t_hand_list.append(t_hand)

    t_card = play_pinochle.find_winning_trick_card(t_hand_list, t_trump)
    assert t_card == "heart_king"

    t_trump = "Clubs"
    t_card = play_pinochle.find_winning_trick_card(t_hand_list, t_trump)
    assert t_card == "diamond_ace"

    # Swap first and second cards.
    # Deck is now heart_king, diamond_9, spade_10, diamond_ace
    t_hand_list[0], t_hand_list[1] = t_hand_list[1], t_hand_list[0]

    t_trump = "Clubs"
    t_card = play_pinochle.find_winning_trick_card(t_hand_list, t_trump)
    assert t_card == "heart_king"

    t_trump = "Diamonds"
    t_card = play_pinochle.find_winning_trick_card(t_hand_list, t_trump)
    assert t_card == "diamond_ace"

    # Swap first and third cards.
    # Deck is now spade_10, diamond_9, heart_king, diamond_ace
    t_hand_list[0], t_hand_list[2] = t_hand_list[2], t_hand_list[0]

    t_trump = "Clubs"
    t_card = play_pinochle.find_winning_trick_card(t_hand_list, t_trump)
    assert t_card == "spade_10"

    t_trump = "Hearts"
    t_card = play_pinochle.find_winning_trick_card(t_hand_list, t_trump)
    assert t_card == "heart_king"
