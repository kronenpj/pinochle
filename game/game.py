"""
This encapsulates data and aspects of a game.

License: GPLv3
"""

import uuid
from typing import List

from game.hand import Hand


class Game:
    """
    Class to encapsulate game state.

    Class properties:
        hands: List of hand classes played during the game.
    """

    __game_id: uuid.UUID
    __hands: List[Hand]

    def __init__(self, **kwargs):
        self.__game_id = kwargs.get("game_id", uuid.uuid4())
        self.__hands = kwargs.get("hands", list())

    def __repr__(self) -> str:
        """
        Returns a string representation of the ``Game`` instance.

        :returns:
            A string representation of the Game instance.

        """
        return "Game(game_id=%r, hands=%r)" % (
            self.__game_id,
            self.__hands,
        )

    def repr(self) -> str:
        """
        Returns a string representation of the ``Game`` instance.

        :returns:
            A string representation of the Game instance.

        """
        return "Game(game_id=%r, hands=\n  %r)" % (
            self.__game_id,
            self.__hands,
        )

    @property
    def game_id(self) -> uuid.UUID:
        return self.__game_id

    @game_id.setter
    def game_id(self, temp: uuid.UUID) -> None:
        self.__game_id = temp

    @property
    def hands(self) -> List[Hand]:
        return self.__hands

    @hands.setter
    def hands(self, temp: List[Hand]) -> None:
        self.__hands = temp
