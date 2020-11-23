"""
This orchestrates the phases of a game.

License: GPLv3
"""

import uuid
from . import const
from .stack import PinochleStack


class Game:
    """
    Class to encapsulate game state.

    :return: [description]
    :rtype: object
    """
    game_id: uuid.UUID
    players: List[Player]

    return score
