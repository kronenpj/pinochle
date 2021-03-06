"""
This scores a PinochleDeck (not a PinochleStack or list), taking into
account trump suits.

License: GPLv3
"""

from typing import Union

from . import custom_log
from .cards import card, const
from .cards.deck import PinochleDeck


def score(deck: PinochleDeck) -> int:
    """
    Scores a deck of cards using meld rules.

    :param deck: The deck to be scored.
    :type deck: PinochleDeck
    :return: Deck's score
    :rtype: int
    """
    mylog = custom_log.get_logger()

    value = _nines(deck)
    value += _marriages(deck)
    value += _jacks(deck)
    value += _queens(deck)
    value += _kings(deck)
    value += _aces(deck)
    value += _run(deck)
    value += _pinochle(deck)

    mylog.info("Score total: %s", value)

    return value


def _trump_suit(deck: PinochleDeck) -> Union[str, None]:
    """
    Score nines in a deck.
    Only nines of trump count for points.

    :param deck: Deck to be scored
    :type deck: PinochleDeck
    :return: Trump suit
    :rtype: str
    """
    mylog = custom_log.get_logger()

    for suit in deck.ranks["suits"]:
        if deck.ranks["suits"][suit] == const.TRUMP_VALUE:
            mylog.info("Determined that %s is trump.", suit)
            return suit
    return None


def _nines(deck: PinochleDeck) -> int:
    """
    Score nines in a deck.
    Only nines of trump count for points.

    :param deck: Deck to be scored
    :type deck: PinochleDeck
    :return: Score for 9s
    :rtype: int
    """
    mylog = custom_log.get_logger()

    value = 0

    trump = _trump_suit(deck)

    # Nines aren't worth meld points until trump is called.
    if trump is None:
        return value

    abbr = card.card_abbrev("9", trump)
    cards = deck.find(abbr)

    if len(cards) > 0:
        value += len(cards)

    mylog.info("Nines score: %d", value)
    return value


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
    mylog = custom_log.get_logger()

    value = 0

    trump = _trump_suit(deck)

    for suit in const.SUITS:
        ksuit = card.card_abbrev("King", suit)
        qsuit = card.card_abbrev("Queen", suit)
        kcards = deck.find(ksuit)
        qcards = deck.find(qsuit)

        temp_score = 2 * min(len(kcards), len(qcards))
        mylog.info("%d Marriages found!", min(len(kcards), len(qcards)))

        # Score marriages as plain until trump is called.
        if trump is not None and suit == trump:
            temp_score = temp_score * 2

        value += temp_score

    mylog.info("Marriages score: %d", value)
    return value


def _jacks(deck: PinochleDeck) -> int:
    """
    Score jacks in a deck.
    Four jacks (one of each suit) scores 4 points.

    :param deck: Deck to be scored
    :type deck: PinochleDeck
    :return: Score for 9s
    :rtype: int
    """
    mylog = custom_log.get_logger()

    value = 0

    array = []
    for suit in const.SUITS:
        a_card = card.card_abbrev("Jack", suit)
        array.append(deck.find(a_card))

    count = 20
    for index in range(len(const.SUITS)):
        count = min(count, len(array[index]))

    if count == 1:
        value += 4
        mylog.info("Single jacks!")
    elif count == 2:
        value += 40
        mylog.info("Double jacks!!")

    mylog.info("Jacks score: %d", value)
    return value


def _queens(deck: PinochleDeck) -> int:
    """
    Score queens in a deck.
    Four queens (one of each suit) scores 6 points.

    :param deck: Deck to be scored
    :type deck: PinochleDeck
    :return: Score for 9s
    :rtype: int
    """
    mylog = custom_log.get_logger()

    value = 0

    array = []
    for suit in const.SUITS:
        a_card = card.card_abbrev("Queen", suit)
        array.append(deck.find(a_card))

    count = 20
    for index in range(len(const.SUITS)):
        count = min(count, len(array[index]))

    if count == 1:
        value += 6
        mylog.info("Single Queens!")
    elif count == 2:
        value += 60
        mylog.info("Double Queens!!")

    mylog.info("Queens score: %d", value)
    return value


def _kings(deck: PinochleDeck) -> int:
    """
    Score kings in a deck.
    Four kings (one of each suit) scores 8 points.

    :param deck: Deck to be scored
    :type deck: PinochleDeck
    :return: Score for 9s
    :rtype: int
    """
    mylog = custom_log.get_logger()

    value = 0

    array = []
    for suit in const.SUITS:
        a_card = card.card_abbrev("King", suit)
        array.append(deck.find(a_card))

    count = 20
    for index in range(len(const.SUITS)):
        count = min(count, len(array[index]))

    if count == 1:
        value += 8
        mylog.info("Single Kings!")
    elif count == 2:
        value += 80
        mylog.info("Double Kings!!")

    mylog.info("Kings score: %d", value)
    return value


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
    mylog = custom_log.get_logger()

    value = 0

    array = []
    for suit in const.SUITS:
        a_card = card.card_abbrev("Ace", suit)
        array.append(deck.find(a_card))

    count = 20
    for index in range(len(const.SUITS)):
        count = min(count, len(array[index]))

    if count == 1:
        value += 10
        mylog.info("Single Aces!")
    elif count == 2:
        value += 100
        mylog.info("Double Aces!!")

    mylog.info("Aces score: %d", value)
    return value


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
    mylog = custom_log.get_logger()

    value = 0
    values = const.VALUES.copy()
    values.remove("9")
    trump = _trump_suit(deck)

    # Can't score a run until trump is called.
    if trump is None:
        return value

    array = []
    for face in values:
        a_card = card.card_abbrev(face, trump)
        array.append(deck.find(a_card))

    count = 20
    for index in range(len(values)):
        count = min(count, len(array[index]))

    value += count * 11

    mylog.info("Run score: %d", value)
    return value


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
    mylog = custom_log.get_logger()

    value = 0

    qspade = card.card_abbrev("Queen", "Spades")
    jdiamond = card.card_abbrev("Jack", "Diamonds")
    qcards = deck.find(qspade)
    jcards = deck.find(jdiamond)

    if min(len(qcards), len(jcards)) == 1:
        value = 4
        mylog.info("Single Pinochle!")
    elif min(len(qcards), len(jcards)) == 2:
        value = 30
        mylog.info("Double Pinochle!!")

    mylog.info("Pinochle score: %d", value)
    return value
