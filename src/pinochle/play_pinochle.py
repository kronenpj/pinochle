"""
This is the module that handles Pinochle game play.
"""
import json
import uuid
from typing import List, Optional

from flask import abort, make_response
from flask.wrappers import Response

from . import (
    game,
    gameround,
    hand,
    player,
    round_,
    roundteams,
    score_meld,
    score_tricks,
    team,
    trick,
    setup_logging,
)
from .cards import utils as card_utils
from .cards.const import SUITS
from .cards.deck import PinochleDeck
from .cards.utils import convert_to_svg_names, deal_hands
from .models import utils
from .models.game import Game
from .models.gameround import GameRound
from .models.hand import Hand
from .models.player import Player
from .models.round_ import Round
from .models.roundteam import RoundTeam
from .models.trick import Trick
from .ws_messenger import WebSocketMessenger as WSM

LOG = setup_logging()

# Also contained in cardtable.py
#                0      1        2           3        4       5
GAME_MODES = ["game", "bid", "bidfinal", "reveal", "meld", "trick"]


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
    # TODO: Think about changing this to 'look' more like a traditional deal. One or
    # three cards dealt from the top of the stack, occassionally contribuing one to the
    # kitty, if applicable. It shouldn't make an actual difference, but...

    LOG.debug("player_ids=%s", player_ids)
    hand_decks, kitty_deck = deal_hands(players=len(player_ids), kitty_cards=kitty_len)

    if kitty_len > 0 and kitty_id is not None:
        hand.addcards(hand_id=kitty_id, cards=convert_to_svg_names(kitty_deck))
    for index, __ in enumerate(player_ids):
        player_info: Optional[Player] = utils.query_player(player_ids[index])
        hand_id = str(player_info.hand_id) if player_info else utils.UUID_ZEROS
        hand.addcards(hand_id=hand_id, cards=convert_to_svg_names(hand_decks[index]))


def set_players_bidding(player_ids: list) -> None:
    """
    Update each player's record to indicate they are participating in this round's
    bidding.

    :param player_ids: [description]
    :type player_ids: list
    """
    LOG.debug("player_ids=%s", player_ids)
    for player_id in player_ids:
        player.update(player_id, {"bidding": True})


def set_player_pass(player_id: str) -> None:
    """
    Update supplied player's record to indicate they are no longer participating in this
    round's bidding.

    :param player_id: [description]
    :type player_id: str
    """
    LOG.debug("set_playerplayer_id=%s", player_id)
    player.update(player_id, {"bidding": False})


def players_still_bidding(round_id: str) -> List[str]:
    """
    Returns list of player_ids still bidding in the supplied round.

    :param round_id: [description]
    :type round_id: str
    :return: List of player_ids
    :rtype: List[str]
    """
    player_ids = roundteams.create_ordered_player_list(round_id)
    return [
        player_id for player_id in player_ids if utils.query_player(player_id).bidding
    ]


def submit_bid(round_id: str, player_id: str, bid: int):
    """
    This function processes a bid submission for a player.

    :param round_id:   Id of the round to delete
    :param player_id:  Id of the player submitting the bid
    :return:           200 on successful delete, 404 if not found,
                       409 if requirements are not satisfied.
    """
    LOG.debug("\nround_id=%s, player_id=%s", round_id, player_id)
    # Get the round requested
    a_round: Round = utils.query_round(str(round_id))
    a_player: Optional[Player] = utils.query_player(str(player_id))

    # Did we find a round?
    if a_round is None or a_round == {}:
        abort(404, f"Round {round_id} not found.")

    # Did we find a player?
    if a_player is None or a_player == {}:
        abort(404, f"Player {player_id} not found.")

    if bid != -1 and a_round.bid >= bid:
        # New bid must be higher than current bid.
        abort(409, f"Bid {bid} is below current bid {a_round.bid}.")

    # Determine the next player to bid this round.
    ordered_player_list = players_still_bidding(round_id)
    next_bid_player_idx = determine_next_bidder_player_id(
        player_id, ordered_player_list
    )

    # If the bid is still progressing, continue prompting.
    game_id = str(utils.query_gameround_for_round(round_id).game_id)
    if bid > 0:
        # Prompt that player to bid.
        send_bid_message(
            "bid_prompt",
            game_id,
            ordered_player_list[next_bid_player_idx],
            bid if bid > 0 else a_round.bid,
        )

        return round_.update(round_id, {"bid": bid, "bid_winner": player_id})

    ## Bid == -1
    # If supplied bid is -1, this indicates the player passed.
    set_player_pass(player_id)

    if len(ordered_player_list) == 2:  # Now one since a player passed...
        send_bid_message(
            "bid_winner",
            game_id,
            ordered_player_list[next_bid_player_idx],
            a_round.bid,
        )
        # TODO: Figure out if this can possibly happen more than once. I don't think so,
        # but it would add another set of cards to the player's hand if it did.
        # Add the cards from the kitty, if any, to the player's hand.
        for hand_obj in utils.query_hand_list(str(utils.query_round(round_id).hand_id)):
            hand.addcard(
                str(
                    utils.query_player(ordered_player_list[next_bid_player_idx]).hand_id
                ),
                hand_obj.card,
            )
        # Record the bid winner's ID
        round_.update(
            round_id, {"bid_winner": ordered_player_list[next_bid_player_idx]}
        )
        t_trick, _ = trick.create(round_id)
        trick.update(
            str(t_trick["trick_id"]),
            {"trick_starter": ordered_player_list[next_bid_player_idx]},
        )
        # Step to the next game state.
        game.update(game_id, state=True)
    else:
        send_bid_message(
            "bid_prompt",
            game_id,
            ordered_player_list[next_bid_player_idx],
            bid if bid > 0 else a_round.bid,
        )

    return {}, 200


def finalize_meld(round_id: str, player_id: str):
    """
    This function processes a meld finalize submission for a player.

    :param round_id:   Id of the round to delete
    :param player_id:  Id of the player submitting the meld
    :return:           200 on successful delete, 404 if not found,
                       409 if requirements are not satisfied.
    """
    LOG.debug("finalize_meld: round_id=%s, player_id=%s", round_id, player_id)
    # Get the round requested
    a_round: Round = utils.query_round(str(round_id))
    a_player: Optional[Player] = utils.query_player(str(player_id))

    # Did we find a round?
    if a_round is None or a_round == {}:
        abort(404, f"Round {round_id} not found.")

    # Did we find a player?
    if a_player is None or a_player == {}:
        abort(404, f"Player {player_id} not found.")

    # Gather all the players for this round.
    player_list = utils.query_player_ids_for_round(round_id)

    if player_id not in player_list:
        abort(404, f"Player {player_id} not playing this round.")

    player.update(player_id, {"meld_final": True})

    # Check to see if all players are ready for the next round.
    if all(utils.query_player(x).meld_final for x in player_list):
        # All meld is final
        total_team_scores(round_id)


def total_team_scores(round_id: str):
    """
    All meld is final, total the team scores so far and update the database.

    :param round_id: Round ID in play
    :type round_id: str
    """
    LOG.debug("finalize_bid: Totalling team scores")

    ws_mess = WSM()
    game_id = str(utils.query_gameround_for_round(round_id).game_id)

    # Total each team's meld.
    for t_roundteam in utils.query_roundteam_list(round_id):
        team_id = str(t_roundteam.team_id)
        total = utils.query_team(team_id).score
        meld_score = sum(
            utils.query_player(t_player.player_id).meld_score
            for t_player in utils.query_teamplayer_list(team_id)
        )
        total += meld_score
        team.update(team_id, {"score": total})

        # Communicate team scores:
        message = {
            "action": "team_score",
            "team_id": team_id,
            "score": total,
            "meld_score": meld_score,
        }
        ws_mess.websocket_broadcast(game_id, message)

    # Advance the game mode.
    game.update(game_id, state=True)


def determine_next_bidder_player_id(player_id: str, ordered_player_list: List[str]):
    """
    Determine the next player to bid this round.

    :param player_id: Player ID who bid last
    :type player_id: str
    :param ordered_player_list: Ordered list of players
    :type ordered_player_list: List[str]
    :raises IndexError: [description]
    :return: [description]
    :rtype: [type]
    """
    try:
        next_bid_player_idx = ordered_player_list.index(player_id)
        next_bid_player_idx += 1
        next_bid_player_idx %= len(ordered_player_list)
        return next_bid_player_idx
    except IndexError as err:
        if not ordered_player_list:
            return 0
        raise IndexError(err) from err


def send_bid_message(message_type: str, game_id: str, player_id: str, bid: int):
    """
    Send a websocket message to all players with a bid-related message with the
    information about the next bidder and current bid, or who has won the bid.

    :param message_type: Type of bid messsage
    :type message_type: str
    :param game_id: Game identifier
    :type game_id: str
    :param player_id: Player identifier
    :type player_id: str
    :param bid: Amount of bid
    :type bid: int
    """
    # Prompt the next player to bid.
    ws_mess = WSM()
    message = {
        "action": message_type,
        "player_id": player_id,
        "bid": bid,
    }
    ws_mess.websocket_broadcast(game_id, message)


def set_trump(round_id: str, player_id: str, trump: str):
    """
    This function processes trump submission by a player.

    :param round_id:   Id of the round to delete
    :param game_id:    Id of the player submitting the bid
    :return:           200 on successful delete, 404 if not found,
                       409 if requirements are not satisfied.
    """
    LOG.debug("\nround_id=%s, player_id=%s", round_id, player_id)
    # Get the round requested
    a_round: Round = utils.query_round(str(round_id))
    a_player: Optional[Player] = utils.query_player(str(player_id))

    # Did we find a round?
    if a_round is None or a_round == {}:
        abort(404, f"Round {round_id} not found.")

    # Did we find a player?
    if a_player is None or a_player == {}:
        abort(404, f"Player {player_id} not found.")

    # New trump must not be already be set.
    LOG.debug("Bid winner=%s, player_id=%s", a_round.bid_winner, player_id)
    if str(a_round.bid_winner) != player_id:
        LOG.debug("set_trump: Bid winner %s must submit trump.", a_round.bid_winner)
        abort(409, f"Bid winner {a_round.bid_winner} must submit trump.")

    if "{}s".format(trump.capitalize()) not in SUITS:
        abort(409, f"Trump suit must be one of {SUITS}.")

    ws_mess = WSM()
    message = {
        "action": "trump_selected",
        "trump": trump,
    }
    game_id = str(utils.query_gameround_for_round(round_id).game_id)
    ws_mess.websocket_broadcast(game_id, message)

    # Step to next game state.
    game.update(game_id, state=True)
    return round_.update(round_id, {"trump": trump})


def start(round_id: str):
    """
    This function starts a round if all the requirements are satisfied.

    :param round_id:   Id of the round to commence.
    :return:           200 on successful delete, 404 if not found,
                       409 if requirements are not satisfied.
    """
    LOG.debug("\nround_id=%s", round_id)
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
        for team_info in utils.query_teamplayer_list(t_team_id):
            # Generate new team hand IDs.
            new_hand_id = str(uuid.uuid4())
            player_hand_id[str(team_info.player_id)] = new_hand_id
            player.update(team_info.player_id, {"hand_id": new_hand_id})

    LOG.debug("kitty=%s", kitty)
    LOG.debug("player_hand_id=%s", player_hand_id)
    LOG.debug("player_hand_ids: %s", list(player_hand_id.keys()))

    if not utils.query_trick_for_round_id(round_id):
        # Create new trick for the round
        trick.create(round_id)

    # Time to deal the cards.
    deal_pinochle(
        player_ids=list(player_hand_id.keys()),
        kitty_len=a_game.kitty_size,
        kitty_id=kitty,
    )

    # Reset player's flags to enable bidding.
    set_players_bidding(list(player_hand_id.keys()))

    game_id = str(a_gameround.game_id)

    # Determine the first player to bid this round.
    ordered_player_list = roundteams.create_ordered_player_list(round_id)
    first_bid_player_id = ordered_player_list[
        a_round.round_seq % len(ordered_player_list)
    ]

    ws_mess = WSM()
    message = {
        "action": "bid_prompt",
        "player_id": first_bid_player_id,
        "bid": a_round.bid,
    }
    ws_mess.websocket_broadcast(game_id, message)

    temp_state = utils.query_game(game_id).state
    message = {
        "action": "game_start",
        "game_id": game_id,
        "state": temp_state,
    }
    ws_mess = WSM()
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
    LOG.debug("round_id=%s", round_id)
    # Get the round requested
    a_round: Round = utils.query_round(round_id)
    a_player: Optional[Player] = utils.query_player(player_id)
    game_id: str = str(utils.query_gameround_for_round(round_id).game_id)

    # Did we find a round?
    if a_round is None or a_round == {}:
        abort(404, f"Round {round_id} not found.")

    # Did we find the player?
    if a_player is None or a_player == {}:
        abort(409, f"No player found for {player_id}.")

    score = 0
    card_list = []
    if len(cards) > 2:
        # Associate the player with that player's hand.
        player_temp: Optional[Player] = utils.query_player(player_id=player_id)
        player_hand_id = str(player_temp.hand_id) if player_temp else utils.UUID_ZEROS
        player_hand = utils.query_hand_list(player_hand_id)
        player_hand_list = [x.card for x in player_hand]
        card_list = cards.split(",")

        LOG.debug("score_hand_meld: player_hand=%s", player_hand_list)
        LOG.debug("score_hand_meld: card_list=%s", card_list)

        for item in card_list:
            if item not in player_hand_list:
                abort(409, f"Card {item} not in player's hand.")

        # Convert from list of SVG card names to PinochleDeck list.
        cardclass_list = card_utils.convert_from_svg_names(card_list)

        # Set trump, if it's been declared (and recorded in the datatbase)
        temp_trump: str = "{}s".format(a_round.trump.capitalize())
        provided_deck = PinochleDeck(cards=cardclass_list)

        # Set trump on the newly created deck, if it's been declared
        if temp_trump in SUITS:
            LOG.debug("Called trump %s in %s.", temp_trump, SUITS)
            provided_deck = card_utils.set_trump(temp_trump, provided_deck)

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
    ws_mess = WSM()
    ws_mess.websocket_broadcast(game_id, message, player_id)
    LOG.debug("score_hand_meld: score=%s", score)
    return make_response(json.dumps({"score": score}), 200)


def new_round(game_id: str, current_round: str) -> Response:
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
    prev_seq: int = utils.query_round(current_round).round_seq
    LOG.debug("new_round: prev_seq=%s", prev_seq)
    prev_gameround: GameRound = utils.query_gameround(game_id, current_round)
    gameround.update(game_id, prev_gameround.round_id, {"active_flag": False})

    player_ids = utils.query_player_ids_for_round(str(prev_gameround.round_id))
    for player_id in player_ids:
        player.update(player_id, {"meld_final": False, "meld_score": 0})

    # Create new round and gameround
    temp_gameround, __ = round_.create(game_id)
    # Obtain the new round's ID.
    temp_round_id = temp_gameround["round_id"]
    cur_roundteam: List[RoundTeam] = utils.query_roundteam_list(current_round)
    # Tie the current teams to the new round.
    roundteams.create(temp_round_id, [str(t.team_id) for t in cur_roundteam])
    # Increment the round_seq for the new round
    round_.update(temp_round_id, {"round_seq": prev_seq + 1})
    LOG.debug("new_round: new_seq=%s", utils.query_round(temp_round_id).round_seq)

    # Create new trick for the round
    trick.create(temp_round_id)

    # Start the new round.
    return start(temp_round_id)


def start_next_trick(round_id: str, player_id: str) -> Response:
    """
    Create a new trick setting player_id as the 'bid winner'.

    :param round_id:      The round in play.
    :type round_id:       str
    :param player_id:     The player initiating the continue instruction.
    :type player_id:      str
    :return:              Response to the web request originating the request.
    :rtype:               Response
    """
    LOG.debug("\nIn start_next_trick: round_id=%s", round_id)
    # Get the round requested
    a_round: Round = utils.query_round(round_id)
    round_player_list: List[str] = utils.query_player_ids_for_round(round_id)

    # Did we find a round?
    if a_round is None or a_round == {}:
        abort(404, f"Round {round_id} not found.")

    # Did we find the player?
    if player_id not in round_player_list:
        abort(409, f"No player found for {player_id}.")

    # Create the next trick.
    t_trick, _ = trick.create(round_id)
    trick.update(str(t_trick["trick_id"]), {"trick_starter": player_id})

    # Send notice of new trick to all players via Websocket
    game_id: str = str(utils.query_gameround_for_round(round_id).game_id)
    message = {
        "action": "trick_next",
        "game_id": game_id,
        "player_id": player_id,
    }
    ws_mess = WSM()
    ws_mess.websocket_broadcast(game_id, message)

    return make_response("Start next trick", 200)


def reorder_players(round_id: str, winner_id: str) -> List[str]:
    """
    Create ordered list of players starting with the player_id supplied.

    :param round_id:      The round in play.
    :type round_id:       str
    :param winner_id:     Player ID of the bid or trick winner.
    :type winner_id:      str
    :return: List of player_ids in order starting with the bid or trick winner
    :rtype: List[str]
    """
    round_player_id_list = utils.query_player_ids_for_round(round_id)

    # Locate the index of the winner in the player list
    starting_index = round_player_id_list.index(winner_id)
    LOG.debug("reorder_players: starting_index=%s", starting_index)

    # Generate a list of indices for the players, starting with the
    # player id passed in as winner_id.
    player_list_len = len(round_player_id_list)
    ordered_player_index_list = [
        (x + starting_index) % player_list_len for x in range(player_list_len)
    ]
    return [round_player_id_list[x] for x in ordered_player_index_list]


def play_trick_card(round_id: str, player_id: str, card: str) -> Response:
    """
    Accept a card played by player for current trick.

    :param round_id:      The round in play.
    :type round_id:       str
    :return:              Response to the web request originating the request.
    :rtype:               Response
    """
    LOG.debug("\nplay_trick_card: round_id=%s", round_id)
    # Get the round requested
    a_round: Round = utils.query_round(round_id)
    a_player: Optional[Player] = utils.query_player(player_id)
    game_id: str = str(utils.query_gameround_for_round(round_id).game_id)

    # Did we find a round?
    if a_round is None or a_round == {}:
        abort(404, f"Round {round_id} not found.")

    # Did we find the player?
    if a_player is None or a_player == {}:
        abort(409, f"No player found for {player_id}.")

    # Retrieve trick data
    a_trick: Trick = utils.query_trick_for_round_id(round_id)
    if a_trick is None or a_trick == {}:
        LOG.debug(
            "play_trick_card: utils.query_all_tricks()=%s", utils.query_all_tricks()
        )
        abort(409, f"Trick could not be found for round {round_id}.")

    # Associate the player with that player's hand.
    player_temp: Optional[Player] = utils.query_player(player_id=player_id)
    player_hand_id: str = str(player_temp.hand_id) if player_temp else utils.UUID_ZEROS
    player_hand: List[Hand] = utils.query_hand_list(player_hand_id)
    player_hand_list: List[str] = [x.card for x in player_hand]

    LOG.debug("play_trick_card: player_hand=%s", player_hand_list)

    if card not in player_hand_list:
        abort(409, f"Card {card} not in player's hand.")

    # TODO: Make sure the player hasn't already sent a card for this trick.

    # Determine the order of the players
    ordered_player_id_list: List[str] = reorder_players(
        str(round_id), str(a_trick.trick_starter)
    )

    # Obtain trick hand ID
    trick_hand_id = str(a_trick.hand_id)

    # Add card to trick deck
    hand.addcard(trick_hand_id, card, ordered_player_id_list.index(player_id))
    # Remove card from player's hand
    hand.deletecard(player_hand_id, card)

    # Send played card to other players via Websocket
    message = {
        "action": "trick_card",
        "game_id": game_id,
        "player_id": player_id,
        "card": card,
    }
    ws_mess = WSM()
    ws_mess.websocket_broadcast(game_id, message, player_id)

    # Determine if the trick is complete (all players submitted cards) and if so, declare
    # trick winner.
    trick_hand_list: List[Hand] = utils.query_hand_list(trick_hand_id)

    LOG.debug("play_trick_card: trick_hand_list=%s", trick_hand_list)
    if len(trick_hand_list) == len(ordered_player_id_list):
        LOG.debug("play_trick_card: trick_hand_list=%s", trick_hand_list)
        winning_card: str = find_winning_trick_card(
            trick_hand_list, f"{a_round.trump.capitalize()}s"
        )
        LOG.debug("play_trick_card: Winning card: %s", winning_card)
        winning_card_index = -1
        LOG.debug("play_trick_card: Trick cards: %s", [x.card for x in trick_hand_list])
        LOG.debug(
            "play_trick_card: Determining winning card index for %s:", winning_card
        )
        for index, t_hand in enumerate(trick_hand_list):
            LOG.debug("play_trick_card: index: %s = %s", index, t_hand.card)
            if winning_card == t_hand.card:
                winning_card_index = index
                break
        assert winning_card_index != -1
        LOG.debug("play_trick_card: winning_card_index=%s", winning_card_index)

        # Determine the player_id who won the trick and their team_id.
        winning_player_id: str = ordered_player_id_list[winning_card_index]
        a_roundteam_list = utils.query_roundteam_list(round_id)
        team_id_list = [x.team_id for x in a_roundteam_list]
        winning_team_id = None
        for team_id in team_id_list:
            if winning_player_id in [
                str(x.player_id) for x in utils.query_teamplayer_list(team_id)
            ]:
                winning_team_id = team_id
        assert winning_team_id
        winning_team_hand_id = str(
            utils.query_roundteam(round_id, winning_team_id).hand_id
        )
        LOG.debug("play_trick_card: Winning player: %s", winning_player_id)

        # Copy the cards in the trick hand to the winning player's team's hand.
        for a_hand in trick_hand_list:
            hand.addcard(winning_team_hand_id, a_hand.card)
        # Update the trick winner in the database
        trick.update(str(a_trick.trick_id), {"trick_winner": winning_player_id})

        # Check to see if a player has cards left in their hand.
        if hand.read_one(player_hand_id):
            LOG.debug("play_trick_card: Sending trick_won message.")
            # Send played card to other players via Websocket
            message = {
                "action": "trick_won",
                "game_id": game_id,
                "player_id": winning_player_id,
                "winning_card": winning_card,
            }
            ws_mess = WSM()
            ws_mess.websocket_broadcast(game_id, message)
        else:
            LOG.debug("play_trick_card: Calling notify_round_complete.")
            # The last trick for this round has been played.
            notify_round_complete(game_id, round_id, winning_player_id, winning_team_id)
        LOG.debug("Exiting play_trick_card, when trick is complete.")

    return make_response("Card accepted", 200)


def find_winning_trick_card(trick_card_list: List[Hand], trump: str) -> str:
    """
    Determine the card in the list which wins the trick, based on trump. The card list is
    ordered such that the card that was 'led' is in position 0.

    :param trick_card_list: Ordered list of Hand classes.
    :type trick_card_list: List[Hand]
    :param trump: The suit designated as trump for this round.
    :type trump: str
    :return: The card that won the trick.
    :rtype: str
    """
    # Convert the list of cards (in Hand classes) to PinochleDeck
    temp_deck = card_utils.convert_from_svg_names([x.card for x in trick_card_list])
    trick_deck = card_utils.set_trump(trump, temp_deck)

    # If nothing else beats it, the card led for the trick wins.
    winning_card = trick_deck[0]
    suit_led = winning_card.suit

    for card in trick_deck:
        LOG.debug("card=%s  -  winning_card=%s  -  trump=%s", card, winning_card, trump)
        if winning_card == card:
            LOG.debug("%s == %s", winning_card, card)
            continue
        if card.suit == trump and winning_card.suit != trump:
            LOG.debug(
                "%s == %s and %s != %s", card.suit, trump, winning_card.suit, trump
            )
            winning_card = card
            suit_led = winning_card.suit
            continue
        if card.suit == suit_led and card > winning_card:
            LOG.debug(
                "%s == %s and %s > %s",
                card.suit,
                suit_led,
                card.value,
                winning_card.value,
            )
            winning_card = card
            continue

    return card_utils.convert_to_svg_name(winning_card)


def notify_round_complete(
    game_id: str, round_id: str, winning_player_id: str, winning_team_id: str
):
    """
    The last trick for this round has been played. Tally the scores and notify players.

    :param game_id: ID of the game being played
    :type game_id: str
    :param round_id: ID of the round of that game
    :type round_id: str
    :param winning_player_id: The ID of the player who won the last trick.
    :type winning_player_id: str
    """
    LOG.debug("In notify_round_complete.")
    # Collect data needed for notification.
    a_roundteam_list = utils.query_roundteam_list(round_id)
    team_id_list = [str(x.team_id) for x in a_roundteam_list]
    t_hand_id_list = [str(x.hand_id) for x in a_roundteam_list]

    # Score the team hands
    trick_score = {}
    assert t_hand_id_list
    LOG.debug("notify_round_complete: t_hand_id_list=%s", t_hand_id_list)
    for index, h_id in enumerate(t_hand_id_list):
        hand_h_id = hand.read_one(h_id)
        if hand_h_id:
            trick_score[team_id_list[index]] = score_tricks.score(
                card_utils.convert_from_svg_names(hand_h_id["cards"])
            )
            if str(team_id_list[index]) == str(winning_team_id):
                trick_score[team_id_list[index]] += 1
            LOG.debug(
                "notify_round_complete: Score for team %s: %s",
                team_id_list[index],
                trick_score[team_id_list[index]],
            )
        else:
            LOG.debug("notify_round_complete: Zero score %s/%s", index, h_id)
            trick_score[team_id_list[index]] = 0

    # Update the overall team scores
    # FIXME: Handle case where bid winner's team doesn't make the bid.
    team_scores = {}
    for t_id in team_id_list:
        a_team = utils.query_team(t_id)
        score = a_team.score + trick_score[t_id]
        team.update(t_id, {"score": score})
        team_scores[t_id] = score

    # Notify the players of the final trick score.
    message = {
        "action": "score_round",
        "game_id": game_id,
        "player_id": winning_player_id,
        "team_trick_scores": trick_score,
        "team_scores": team_scores,
    }
    LOG.debug("notify_round_complete: Sending WSM to clients. %s", message)
    ws_mess = WSM()
    ws_mess.websocket_broadcast(game_id, message)
    LOG.debug("Exiting notify_round_complete.")
