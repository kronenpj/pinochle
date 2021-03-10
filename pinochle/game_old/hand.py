"""
This encapsulates data and aspects of a single hand.

License: GPLv3
"""

import uuid
from typing import List

from pinochle.game_old.player import Player
from pinochle.game_old.team import Team


class Hand:
    """
    Class to encapsulate hand state.

    Class properties:
        bid: The winning bid for this hand.
        bid_winner: Player who won the bid for this hand.
        score: List of scores associated with the team at the same index.
        teams: List of team classes.
        trump: Declared for the hand.
    """

    __bid: int
    __bid_winner: str
    __hand_id: uuid.UUID
    __hand_seq: int
    __score: List[int]  # One score per team
    __teams: List[Team]
    __trump: str

    def __init__(self, **kwargs):
        self.__bid = kwargs.get("bid", 20)
        self.__bid_winner = kwargs.get("bid_winner", "NoOne")
        self.__hand_id = kwargs.get("hand_id", uuid.uuid4())
        self.__hand_seq = kwargs.get("hand_id", 0)
        self.__score = kwargs.get("score", [0])
        self.__teams = kwargs.get("teams", list())
        self.__trump = kwargs.get("trump", str)

    def __repr__(self) -> str:
        """
        Returns a string representation of the ``Hand`` instance.

        :returns:
            A string representation of the Hand instance.

        """
        return "Hand(hand_id=%r, hand_seq=%r, score=%r, bid=%r, bid_winner=%r, teams=%r, trump=%r)" % (
            self.__hand_id,
            self.__hand_seq,
            self.__score,
            self.__bid,
            self.__bid_winner,
            self.__teams,
            self.__trump,
        )

    def repr(self) -> str:
        """
        Returns a string representation of the ``hand`` instance.

        :returns:
            A string representation of the hand instance.

        """
        return "Hand(hand_id=%r, hand_seq=%r, score=%r, bid=%r,\nbid_winner=%r,\nteams=%r\ntrump=%r)" % (
            self.__hand_id,
            self.__hand_seq,
            self.__score,
            self.__bid,
            self.__bid_winner,
            self.__teams,
            self.__trump,
        )

    @property
    def hand_id(self) -> uuid.UUID:
        return self.__hand_id

    @hand_id.setter
    def hand_id(self, temp: uuid.UUID) -> None:
        self.__hand_id = temp

    @property
    def hand_seq(self) -> int:
        return self.__hand_seq

    @hand_seq.setter
    def hand_seq(self, temp: int) -> None:
        self.__hand_seq = temp

    @property
    def score(self) -> List[int]:
        return self.__score

    @score.setter
    def score(self, temp: List[int]) -> None:
        self.__score = temp

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
    def bid_winner(self) -> str:
        return self.__bid_winner

    @bid_winner.setter
    def bid_winner(self, temp: str) -> int:
        self.__bid_winner = temp

    @property
    def trump(self) -> str:
        return self.__trump

    @trump.setter
    def trump(self, temp: str) -> str:
        self.__trump = temp
