"""
This scores a PinochleDeck or a PinochleStack (not a list).

License: GPLv3
"""

from . import const
from .stack import PinochleStack


def score(deck: PinochleStack) -> int:
    """
    Scores a deck of cards using trick rules.

    :param deck: The deck to be scored.
    :type deck: PinochleDeck
    :return: Deck's score
    :rtype: int
    """

    score = 0

    for face in const.TRICK_SCORES:
        card_l = deck.find(face)
        score += len(card_l) * const.TRICK_SCORES[face]

    return score
