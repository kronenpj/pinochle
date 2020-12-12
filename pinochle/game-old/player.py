"""
Class to represent a player.

License: GPLv3
"""

import uuid

from pinochle.deck import PinochleDeck


class Player:
    """
    Class to encapsulate a player and their attributes.

    Class properties:
        name: The player's name
        hand: The player's deck / hand
        score: Player's cumulative score for this game
    """

    __hand: PinochleDeck
    __name: str
    __player_id: uuid.UUID
    __score: int = 0

    def __init__(self, **kwargs):
        self.__player_id = kwargs.get("player_id", uuid.uuid4())
        self.__name = kwargs.get("name", "player")
        self.__hand = kwargs.get("hand", PinochleDeck(build=False))

    def __repr__(self) -> str:
        """
        Returns a string representation of the ``Player`` instance.

        :returns:
            A string representation of the Player instance.

        """
        return "Player(player_id=%r, name=%r, score=%r, hand=%r)" % (
            self.__player_id,
            self.__name,
            self.__score,
            self.__hand,
        )

    def repr(self) -> str:
        """
        Returns a string representation of the ``Player`` instance.

        :returns:
            A string representation of the Player instance.

        """
        return "\nPlayer(player_id=%r, name=%r, score=%r, hand=\n  %r)" % (
            self.__player_id,
            self.__name,
            self.__score,
            self.__hand,
        )

    @property
    def hand(self) -> PinochleDeck:
        return self.__hand

    @hand.setter
    def hand(self, temp: PinochleDeck) -> None:
        self.__hand = temp

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, temp: str):
        self.__name = temp

    @property
    def player_id(self) -> uuid.UUID:
        return self.__player_id

    @player_id.setter
    def player_id(self, f_uuid: uuid.UUID) -> None:
        self.__player_id = f_uuid

    @property
    def score(self) -> int:
        return self.__score

    @score.setter
    def score(self, temp: int) -> None:
        self.__score = temp
