"""
This scores a PinochleDeck (not a PinochleStack or list), taking into
account trump suits.

License: GPLv3
"""

from . import card, const
from .deck import PinochleDeck


def score(deck: PinochleDeck) -> int:
    """
    Scores a deck of cards using meld rules.

    :param deck: The deck to be scored.
    :type deck: PinochleDeck
    :return: Deck's score
    :rtype: int
    """

    # This doesn't work until trump is called.
    if _trump_suit(deck) is None:
        return 0

    score = 0

    score += _nines(deck)
    score += _marriages(deck)
    score += _jacks(deck)
    score += _queens(deck)
    score += _kings(deck)
    score += _aces(deck)
    score += _run(deck)
    score += _pinochle(deck)

    return score


def _trump_suit(deck: PinochleDeck) -> str:
    """
    Score nines in a deck.
    Only nines of trump count for points.

    :param deck: Deck to be scored
    :type deck: PinochleDeck
    :return: Score for 9s
    :rtype: int
    """
    for suit in deck.ranks["suits"]:
        if deck.ranks["suits"][suit] == const.TRUMP_VALUE:
            return suit


def _nines(deck: PinochleDeck) -> int:
    """
    Score nines in a deck.
    Only nines of trump count for points.

    :param deck: Deck to be scored
    :type deck: PinochleDeck
    :return: Score for 9s
    :rtype: int
    """
    score = 0

    trump = _trump_suit(deck)
    # print(f"Trump is: {trump}")
    abbr = card.card_abbrev("9", trump)
    cards = deck.find(abbr)

    if len(cards) > 0:
        score += len(cards)

    return score


def _marriages(deck: PinochleDeck) -> int:
    """
    Score marriages in a deck.
    Marriages (king and queen of same suit) score 2 points per,
    double when trump.

    :param deck: Deck to be scored
    :type deck: PinochleDeck
    :return: Score for 9s
    :rtype: int
    """
    score = 0

    trump = _trump_suit(deck)

    for suit in const.SUITS:
        ksuit = card.card_abbrev("King", suit)
        qsuit = card.card_abbrev("Queen", suit)
        kcards = deck.find(ksuit)
        qcards = deck.find(qsuit)

        temp_score = 2 * min(len(kcards), len(qcards))
        if suit == trump:
            temp_score = temp_score * 2
        score = score + temp_score

    return score


def _jacks(deck: PinochleDeck) -> int:
    """
    Score jacks in a deck.
    Four jacks (one of each suit) scores 4 points.

    :param deck: Deck to be scored
    :type deck: PinochleDeck
    :return: Score for 9s
    :rtype: int
    """
    score = 0

    array = []
    for suit in const.SUITS:
        a_card = card.card_abbrev("Jack", suit)
        array.append(deck.find(a_card))

    count = 20
    for index in range(len(const.SUITS)):
        count = min(count, len(array[index]))

    score = score + count * 4

    return score


def _queens(deck: PinochleDeck) -> int:
    """
    Score queens in a deck.
    Four queens (one of each suit) scores 6 points.

    :param deck: Deck to be scored
    :type deck: PinochleDeck
    :return: Score for 9s
    :rtype: int
    """
    score = 0

    array = []
    for suit in const.SUITS:
        a_card = card.card_abbrev("Queen", suit)
        array.append(deck.find(a_card))

    count = 20
    for index in range(len(const.SUITS)):
        count = min(count, len(array[index]))

    score = score + count * 6

    return score


def _kings(deck: PinochleDeck) -> int:
    """
    Score kings in a deck.
    Four kings (one of each suit) scores 8 points.

    :param deck: Deck to be scored
    :type deck: PinochleDeck
    :return: Score for 9s
    :rtype: int
    """
    score = 0

    array = []
    for suit in const.SUITS:
        a_card = card.card_abbrev("King", suit)
        array.append(deck.find(a_card))

    count = 20
    for index in range(len(const.SUITS)):
        count = min(count, len(array[index]))

    score = score + count * 8

    return score


def _aces(deck: PinochleDeck) -> int:
    """
    Score nines in a deck.
    Four aces (one of each suit) scores 10 points,
    eight aces (two of each suit) scores 100 points.

    :param deck: Deck to be scored
    :type deck: PinochleDeck
    :return: Score for 9s
    :rtype: int
    """
    score = 0

    array = []
    for suit in const.SUITS:
        a_card = card.card_abbrev("Ace", suit)
        array.append(deck.find(a_card))

    count = 20
    for index in range(len(const.SUITS)):
        count = min(count, len(array[index]))

    if count == 1:
        score = score + 10
    elif count == 2:
        score = score + 100

    return score


def _run(deck: PinochleDeck) -> int:
    """
    Score runs in a deck.
    One of each J, Q, K, 10, A in the trump suit scores 15 points,
    minus four for the marriage counted already.

    :param deck: Deck to be scored
    :type deck: PinochleDeck
    :return: Score for 9s
    :rtype: int
    """
    score = 0
    values = const.VALUES.copy()
    values.remove("9")
    trump = _trump_suit(deck)

    array = []
    for face in values:
        a_card = card.card_abbrev(face, trump)
        array.append(deck.find(a_card))

    count = 20
    for index in range(len(values)):
        count = min(count, len(array[index]))

    score = score + count * 11

    return score


def _pinochle(deck: PinochleDeck) -> int:
    """
    Score pinochless in a deck.
    A Queen of Spades and a Jack of Diamonds scores 4 points,
    two Queens of Spades and two Jacks of Diamonds scores 35 points.

    :param deck: Deck to be scored
    :type deck: PinochleDeck
    :return: Score for 9s
    :rtype: int
    """
    score = 0

    qspade = card.card_abbrev("Queen", "Spades")
    jdiamond = card.card_abbrev("Jack", "Diamonds")
    qcards = deck.find(qspade)
    jcards = deck.find(jdiamond)

    if min(len(qcards), len(jcards)) == 1:
        score = 4
    elif min(len(qcards), len(jcards)) == 2:
        score = 35

    return score