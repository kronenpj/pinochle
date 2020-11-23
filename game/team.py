"""
This represents a player.

License: GPLv3
"""

import uuid
from typing import List

from pinochle import const
from pinochle.deck import PinochleDeck
from pinochle.stack import PinochleStack
from game.player import Player


class Team:
    """
    Class to encapsulate a team and associated attributes.
    """

    __collection: PinochleDeck = PinochleDeck(build=False)
    __name: str
    __players: List[Player]
    __team_id: uuid.UUID

    def __init__(self, **kwargs):
        self.__team_id = kwargs.get("team_id", uuid.uuid4())
        self.__name = kwargs.get("name", "team")
        self.__players = kwargs.get("players", list())

    def __repr__(self) -> str:
        """
        Returns a string representation of the ``Team`` instance.

        :returns:
            A string representation of the Team instance.

        """
        return "\nTeam(team_id=%r, name=%r, collection=\n  %r, players=\n  %r)" % (
            self.__team_id,
            self.__name,
            self.__collection,
            self.__players,
        )

    @property
    def collection(self) -> PinochleDeck:
        return self.__collection

    @collection.setter
    def collection(self, temp: PinochleDeck) -> None:
        self.__collection = temp

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, temp: str) -> None:
        self.__name = temp

    @property
    def players(self) -> List[Player]:
        return self.__players

    @players.setter
    def players(self, temp: List[Player]) -> None:
        self.__players = temp

    @property
    def team_id(self) -> uuid.UUID:
        return self.__team_id

    @team_id.setter
    def team_id(self, temp: uuid.UUID) -> None:
        self.__team_id = temp
