"""
This orchestrates the phases of a game.

License: GPLv3
"""

import uuid
from copy import deepcopy
from typing import List, Union

from pinochle import custom_log
from pinochle.cards import const
from pinochle.cards.deck import PinochleDeck
from pinochle.cards.stack import PinochleStack
from pinochle.models import Game, Hand, Player, Team


def create_new_game(teams: List[Team]) -> Game:
    """
    Create a new game from user inputs.
    """
    mylog = custom_log.get_logger()

    first_hand: Hand = Hand(teams=teams)

    return Game(hands=[first_hand])


def append_new_hand_to_game(game: Game, teams: Union[None, List[Team]] = None) -> None:
    """
    Add a new hand to an existing game, using the same teams from the last hand. This occurs due to a side-effect and not from a return value.
    """
    mylog = custom_log.get_logger()

    last_hand_index = len(game.hands) - 1  # Zero-based index
    last_hand_seq = game.hands[last_hand_index].hand_seq

    if teams is None:
        last_team = deepcopy(game.hands[last_hand_index].teams)
    else:
        last_team = deepcopy(teams)

    for team_idx, _ in enumerate(last_team):
        for player_idx, _ in enumerate(last_team[team_idx].players):
            last_team[team_idx].collection = PinochleDeck(build=False)
            last_team[team_idx].players[player_idx].hand = PinochleDeck(build=False)

    new_hand = Hand(teams=last_team)
    new_hand.hand_seq = last_hand_seq + 1
    game.hands.append(new_hand)
