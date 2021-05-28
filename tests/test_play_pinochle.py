"""
Tests for the Pinochle game play routines.

License: GPLv3
"""
from typing import Dict, List, Tuple
import uuid
from random import choice, shuffle
from unittest.mock import ANY, call

import pytest
from pinochle import play_pinochle, player, round_, trick
from pinochle.cards import utils as card_utils
from pinochle.cards.const import SUITS
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


def test_start_next_trick_normal(app):
    """
    [summary]

    :param app: [description]
    :type app: [type]
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    # Create a trick for this round.
    t_trick, _ = trick.create(round_id)
    t_trick_id = str(t_trick["trick_id"])

    player_id = choice(player_ids)
    t_response = play_pinochle.start_next_trick(round_id, player_id)
    assert t_response
    assert t_response.status_code == 200

    new_trick_id = str(utils.query_trick_for_round_id(round_id))
    assert new_trick_id != t_trick_id


def test_start_next_trick_bad_round(app):
    """
    [summary]

    :param app: [description]
    :type app: [type]
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    round_id = str(uuid.uuid4())

    player_id = choice(player_ids)
    with pytest.raises(exceptions.HTTPException):
        play_pinochle.start_next_trick(round_id, player_id)


def test_start_next_trick_bad_player(app):
    """
    [summary]

    :param app: [description]
    :type app: [type]
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    player_id = str(uuid.uuid4())
    with pytest.raises(exceptions.Conflict):
        play_pinochle.start_next_trick(round_id, player_id)


def test_play_trick_card_normal(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/kitty' page is requested (GET)
    THEN check that the response contains the expected information
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    # Choose a random bid winner.
    winner_player_id = choice(player_ids)
    round_.update(round_id, {"bid_winner": winner_player_id})

    # Set trump for this round.
    round_trump = choice(SUITS).lower().rstrip("s")
    play_pinochle.set_trump(round_id, winner_player_id, round_trump)
    print(f"Trump for this round is: {round_trump}")

    # Create a trick for this round.
    t_trick, _ = trick.create(round_id)
    t_trick_id = str(t_trick["trick_id"])
    trick.update(
        t_trick_id, {"trick_starter": winner_player_id},
    )

    # Gather the hand ids for each player and team.
    player_names = {p_id: utils.query_player(p_id).name for p_id in player_ids}
    player_hand_ids = {
        p_id: test_utils.query_player_hand_id(p_id) for p_id in player_ids
    }
    team_hand_ids = {
        t_id: test_utils.query_team_hand_id(round_id, t_id) for t_id in team_ids
    }

    # Deal cards
    play_pinochle.deal_pinochle(player_ids)

    for p_h_id in player_hand_ids.values():
        assert len(utils.query_hand_list(p_h_id)) == 12
    for t_h_id in team_hand_ids.values():
        assert len(utils.query_hand_list(t_h_id)) == 0

    print("")
    print(f"First trick lead is: {player_names[winner_player_id]}")

    # "Play" tricks until players are out of cards.
    while len(utils.query_hand_list(player_hand_ids[winner_player_id])) > 0:
        t_trick_hand_id = str(utils.query_trick_for_round_id(round_id).hand_id)
        assert t_trick_hand_id
        # Play a single trick.
        (
            t_trick_player_card_dict,
            ordered_player_id_list,
            t_trick_card_list,
        ) = _play_single_trick(round_id, player_ids, player_hand_ids)

        # Determine trick winner via a different algorithm than test target
        t_trick_winner_id = _determine_trick_winner(
            t_trick_player_card_dict,
            round_trump,
            ordered_player_id_list,
            t_trick_card_list,
        )

        assert t_trick_winner_id
        assert t_trick_card_list == [
            x.card for x in utils.query_hand_list(t_trick_hand_id)
        ]

        # Retrieve updated data about the trick from the database.
        trick_winner = str(utils.query_trick(t_trick_id).trick_winner)
        assert trick_winner == t_trick_winner_id
        print(f"{player_names[trick_winner]} won this trick.")

        # Create new trick and start over.
        t_trick, _ = trick.create(round_id)
        t_trick_id = t_trick["trick_id"]
        trick.update(t_trick_id, {"trick_starter": trick_winner})
        winner_player_id = trick_winner
        print("")
        print(f"Next trick lead is: {player_names[winner_player_id]}")

    for t_h_id in team_hand_ids.values():
        assert len(utils.query_hand_list(t_h_id)) >= 0


def _play_single_trick(
    round_id: str, player_ids: List[str], player_hand_ids: Dict[str, str]
) -> Tuple[Dict[str, str], List[str], List[str]]:
    """
    Play a single trick. Each player submits a card to the trick deck. Determination of the winner is performed by the caller.

    :param round_id: Round ID of the round being played.
    :type round_id: str
    :param player_ids: List of Player IDs playing the round.
    :type player_ids: List[str]
    :param player_hand_ids: Correlation of player IDs and their hand IDs.
    :type player_hand_ids: Dict[str, str]
    :return: Data needed to continue processing: player_card_dict, ordered_player_id_list, card_list
    :rtype: Tuple[Dict[str, str], List[str], List[str]]
    """
    # Request the ordered list of players for this round.
    ordered_player_id_list = play_pinochle.reorder_players(
        str(round_id), str(utils.query_trick_for_round_id(round_id).trick_starter)
    )

    # Create a temporary list of 'cards' to keep track of played cards ourselves.
    player_list_len = len(player_ids)
    card_list = ["blank" for x in range(player_list_len)]
    # Same with the card <-> Player ID association
    player_card_dict = {}

    # Throw cards in a random player order. A new, temporary list of player_ids is
    # needed because shuffle does so in-place.
    t_player_ids = player_ids
    shuffle(t_player_ids)
    for p_id in t_player_ids:
        # Capture the *index* of the player in the ordered list so that it can be
        # sent as the UI does.
        t_player_idx = ordered_player_id_list.index(p_id)
        assert 0 <= t_player_idx < player_list_len
        # Choose a card from what remains in the player's hand.
        card = choice(utils.query_hand_list(player_hand_ids[p_id])).card
        play_pinochle.play_trick_card(round_id, p_id, card)
        # Track the trick information locally.
        card_list[t_player_idx] = card
        player_card_dict[p_id] = card

    return (
        player_card_dict,
        ordered_player_id_list,
        card_list,
    )


def _determine_trick_winner(
    trick_player_card_assoc: Dict[str, str],
    round_trump: str,
    ordered_player_id_list: List[str],
    trick_card_list: List[str],
) -> str:
    """
    Determine trick winner via a different algorithm than test target

    :param trick_player_card_assoc: Dictionary associating player_id and the card thrown for this trick.
    :type trick_player_card_assoc: Dict[str]
    :param round_trump: The recorded trump suit for the round.
    :type round_trump: str
    :param ordered_player_id_list: [description]
    :type ordered_player_id_list: [type]
    :param trick_card_list: [description]
    :type trick_card_list: [type]
    :return: [description]
    :rtype: [type]
    """
    t_trump_thrown = {
        p_id: t_card
        for p_id, t_card in trick_player_card_assoc.items()
        if round_trump in t_card
    }
    t_trick_winner_id = ""
    highest_card = ""
    if t_trump_thrown:
        for player_id in ordered_player_id_list:
            if player_id not in t_trump_thrown:
                continue
            value_ = trick_player_card_assoc[player_id]
            if highest_card == "" or highest_card < card_utils.convert_from_svg_name(
                value_
            ):
                highest_card = card_utils.convert_from_svg_name(value_)
                t_trick_winner_id = player_id
    else:
        suit_led = trick_card_list[0][: trick_card_list[0].rfind("_")]
        assert suit_led
        t_suit_led = {
            p_id: t_card
            for p_id, t_card in trick_player_card_assoc.items()
            if suit_led in t_card
        }
        for player_id in ordered_player_id_list:
            if player_id not in t_suit_led:
                continue
            value = t_suit_led[player_id]
            if highest_card == "" or highest_card < card_utils.convert_from_svg_name(
                value
            ):
                highest_card = card_utils.convert_from_svg_name(value)
                t_trick_winner_id = player_id
    return t_trick_winner_id
