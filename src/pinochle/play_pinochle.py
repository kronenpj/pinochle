"""
This is the module that handles Pinochle game play.
"""
import json
import uuid
from typing import List

from flask import abort, make_response
from flask.wrappers import Response

from . import gameround, hand, player, round_, roundteams, score_meld, score_tricks
from .cards import utils as card_utils
from .cards.const import SUITS
from .cards.deck import PinochleDeck
from .cards.utils import convert_to_svg_names, deal_hands
from .models import utils
from .models.game import Game
from .models.gameround import GameRound
from .models.player import Player
from .models.round_ import Round
from .models.roundteam import RoundTeam
from .models.teamplayers import TeamPlayers
from .ws_messenger import WebSocketMessenger as WSM


def deal_pinochle(player_ids: list, kitty_len: int = 0, kitty_id: str = None) -> None:
    """
    Deal a deck of Pinochle cards into player's hands and the kitty.

    :param player_ids: [description]
    :type player_ids: list
    :param kitty_len: [description]
    :type kitty_len: int
    :param kitty_id: [description]
    :type kitty_id: str
    """
    # print(f"player_ids={player_ids}")
    hand_decks, kitty_deck = deal_hands(players=len(player_ids), kitty_cards=kitty_len)

    if kitty_len > 0 and kitty_id is not None:
        hand.addcards(hand_id=kitty_id, cards=convert_to_svg_names(kitty_deck))
    for index, __ in enumerate(player_ids):
        player_info: Player = utils.query_player(player_ids[index])
        hand_id = str(player_info.hand_id)
        hand.addcards(hand_id=hand_id, cards=convert_to_svg_names(hand_decks[index]))


def submit_bid(round_id: str, player_id: str, bid: int):
    """
    This function processes a bid submission for a player.

    :param round_id:   Id of the round to delete
    :param game_id:    Id of the player submitting the bid
    :return:           200 on successful delete, 404 if not found,
                       409 if requirements are not satisfied.
    """
    # print(f"\nround_id={round_id}, player_id={player_id}")
    # Get the round requested
    a_round: Round = utils.query_round(str(round_id))
    a_player: Player = utils.query_player(str(player_id))

    # Did we find a round?
    if a_round is None or a_round == {}:
        abort(404, f"Round {round_id} not found.")

    # Did we find a player?
    if a_player is None or a_player == {}:
        abort(404, f"Player {player_id} not found.")

    # New bid must be higher than current bid.
    if a_round.bid >= bid:
        abort(409, f"Bid {bid} is below current bid {a_round.bid}.")

    return round_.update(round_id, {"bid": bid, "bid_winner": player_id})


def set_trump(round_id: str, player_id: str, trump: str):
    """
    This function processes trump submission by a player.

    :param round_id:   Id of the round to delete
    :param game_id:    Id of the player submitting the bid
    :return:           200 on successful delete, 404 if not found,
                       409 if requirements are not satisfied.
    """
    # print(f"\nround_id={round_id}, player_id={player_id}")
    # Get the round requested
    a_round: Round = utils.query_round(str(round_id))
    a_player: Player = utils.query_player(str(player_id))

    # Did we find a round?
    if a_round is None or a_round == {}:
        abort(404, f"Round {round_id} not found.")

    # Did we find a player?
    if a_player is None or a_player == {}:
        abort(404, f"Player {player_id} not found.")

    # New trump must not be already be set.
    # print("Bid winner=%s, player_id=%s" % (a_round.bid_winner, player_id))
    if str(a_round.bid_winner) != player_id:
        abort(409, f"Bid winner {a_round.bid_winner} must submit trump.")

    trump = trump.capitalize()
    if trump not in SUITS:
        abort(409, f"Trump suit must be one of {SUITS}.")

    return round_.update(round_id, {"trump": trump})


def start(round_id: str):
    """
    This function starts a round if all the requirements are satisfied.

    :param round_id:   Id of the round to commence.
    :return:           200 on successful delete, 404 if not found,
                       409 if requirements are not satisfied.
    """
    # print(f"\nround_id={round_id}")
    # Get the round requested
    a_round: Round = utils.query_round(round_id)
    a_gameround: GameRound = utils.query_gameround_for_round(round_id)

    # Did we find a round?
    if a_round is None or a_round == {}:
        abort(404, f"Round {round_id} not found.")

    # Retrieve the information for the round and teams.
    round_t: list = utils.query_roundteam_list(round_id)

    # Did we find one or more round-team entries?
    if round_t is None or round_t == []:
        abort(409, f"No teams found for round {round_id}.")

    # Retrieve the information for the associated game.
    a_game: Game = utils.query_game(str(a_gameround.game_id))

    # Did we find a game?
    if a_game is None:
        abort(409, f"No game found for round {round_id}.")

    # Retrieve the hand_id for the kitty.
    kitty = str(a_round.hand_id)
    # Clear the kitty before dealing cards into that hand.
    hand.deleteallcards(kitty)

    # Collect the individual players from the round's teams.
    player_hand_id = {}
    for t_team_id in [str(x.team_id) for x in round_t]:
        t_teamplayer_list: List[TeamPlayers] = utils.query_teamplayer_list(t_team_id)
        for team_info in t_teamplayer_list:
            # Generate new hand IDs.
            new_hand_id = str(uuid.uuid4())
            player_hand_id[str(team_info.player_id)] = new_hand_id
            player.update(team_info.player_id, {"hand_id": new_hand_id})

    # print(f"kitty={kitty}")
    # print(f"player_hand_id={player_hand_id}")
    # print(f"player_hand_ids: {list(player_hand_id.keys())}")
    # print(f"player_list_ordered={player_list_ordered}")
    # print(f"player_list_ordered={[utils.query_player(x).name for x in player_list_ordered]}")

    # Time to deal the cards.
    deal_pinochle(
        player_ids=list(player_hand_id.keys()),
        kitty_len=a_game.kitty_size,
        kitty_id=kitty,
    )

    game_id = str(a_gameround.game_id)
    temp_state = utils.query_game(game_id).state
    message = {
        "action": "game_start",
        "game_id": game_id,
        "state": temp_state,
    }
    ws_mess = WSM.get_instance()
    ws_mess.websocket_broadcast(game_id, message)
    return make_response(f"Round {round_id} started.", 200)


def score_hand_meld(round_id: str, player_id: str, cards: str):
    """
    This function scores a player's meld hand given the list of cards.

    :param round_id:   Id of the round to delete
    :param player_id:  Id of the player
    :param cards:      Comma separated list of cards submitted for meld.
    :return:           200 on successful scoring of cards, 404 if not found,
                       409 if scoring isn't successful.
    """
    # print(f"\nscore_hand_meld: round_id={round_id}")
    # Get the round requested
    a_round: Round = utils.query_round(round_id)
    a_player: Player = utils.query_player(player_id)
    game_id: str = str(utils.query_gameround_for_round(round_id).game_id)

    # Did we find a round?
    if a_round is None or a_round == {}:
        abort(404, f"Round {round_id} not found.")

    # Did we find the player?
    if a_player is None or a_player == {}:
        abort(409, f"No player found for {player_id}.")

    # Associate the player with that player's hand.
    player_temp: Player = utils.query_player(player_id=player_id)
    player_hand_id = str(player_temp.hand_id)
    player_hand = utils.query_hand_list(player_hand_id)
    player_hand_list = [x.card for x in player_hand]
    card_list = cards.split(",")

    # print(f"score_hand_meld: player_hand={player_hand_list}")
    # print(f"score_hand_meld: card_list={card_list}")

    for item in card_list:
        if item not in player_hand_list:
            abort(409, f"Card {item} not in player's hand.")

    # Convert from list of SVG card names to PinochleDeck list.
    cardclass_list = card_utils.convert_from_svg_names(card_list)

    # Set trump, if it's been declared (and recorded in the datatbase)
    temp_trump: str = a_round.trump
    provided_deck = PinochleDeck(cards=cardclass_list)

    # Set trump on the newly created deck, if it's been declared
    if temp_trump.capitalize() in SUITS:
        card_utils.set_trump(temp_trump, provided_deck)

    # Score the deck supplied.
    score = score_meld.score(provided_deck)

    player.update(player_id=player_id, data={"meld_score": score})

    # Send card list and meld score to other players via Websocket
    message = {
        "action": "meld_update",
        "game_id": game_id,
        "player_id": player_id,
        "card_list": card_list,
        "meld_score": score,
    }
    ws_mess = WSM.get_instance()
    ws_mess.websocket_broadcast(game_id, message, player_id)
    # print(f"score_hand_meld: score={score}")
    return make_response(json.dumps({"score": score}), 200)


def new_round(game_id:str, current_round:str)-> Response:
    """
    Cycle the game to a new round.

    :param game_id:       The game receiving a new round.
    :type game_id:        str
    :param current_round: The round being retired.
    :type current_round:  str
    :return:              Response to the web request originating the request.
    :rtype:               Response
    """
    # Deactivate soon-to-be previous round.
    prev_gameround: GameRound = utils.query_gameround(game_id, current_round)
    gameround.update(game_id, prev_gameround.round_id, {"active_flag": False})

    # Create new round and gameround
    temp_gameround, __ = round_.create(game_id)
    # Obtain the new round's ID.
    temp_round_id = temp_gameround["round_id"]
    cur_roundteam: List[RoundTeam] = utils.query_roundteam_list(current_round)
    # Tie the current teams to the new round.
    roundteams.create(temp_round_id, [str(t.team_id) for t in cur_roundteam])

    # Start the new round.
    return start(temp_round_id)
