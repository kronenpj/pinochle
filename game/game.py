"""
This encapsulates data and aspects of a game.

License: GPLv3
"""

import uuid
from typing import List

from game.player import Player
from game.team import Team


class Game:
    """
    Class to encapsulate game state.
    """

    __game_id: uuid.UUID
    __players: List[Player]
    __teams: List[Team]
    __bid: int
    __trump: str

    def __init__(self, **kwargs):
        self.__bid = kwargs.get("bid", int)
        self.__game_id = kwargs.get("game_id", uuid.uuid4())
        self.__players = kwargs.get("players", list())
        self.__teams = kwargs.get("teams", list())
        self.__trump = kwargs.get("trump", str)

    def __repr__(self) -> str:
        """
        Returns a string representation of the ``Game`` instance.

        :returns:
            A string representation of the Game instance.

        """
        return "Game(game_id=%r, bid=%r,\nteams=%r\ntrump=%r, players=\n  %r)" % (
            self.__game_id,
            self.__bid,
            self.__teams,
            self.__trump,
            self.__players,
        )

    @property
    def game_id(self) -> uuid.UUID:
        return self.__game_id

    @game_id.setter
    def game_id(self, temp: uuid.UUID) -> None:
        self.__game_id = temp

    @property
    def players(self) -> List[Player]:
        return self.__players

    @players.setter
    def players(self, temp: List[Player]) -> None:
        self.__players = temp

    @property
    def teams(self) -> List[Team]:
        return self.__teams

    @teams.setter
    def teams(self, temp: List[Team]) -> None:
        self.__teams = temp

    @property
    def bid(self) -> int:
        return self.__bid

    @bid.setter
    def bid(self, temp: int) -> int:
        self.__bid = temp

    @property
    def trump(self) -> str:
        return self.__trump

    @trump.setter
    def trump(self, temp: str) -> str:
        self.__trump = temp
