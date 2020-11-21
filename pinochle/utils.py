"""
Utilities to work with a deck of Pinochle cards.

License: GPLv3
Inspired by: https://github.com/Trebek/pydealer
Modernized and modified for Pinochle by Paul Kronenwetter
"""

import copy

from . import const
from .exceptions import InvalidDeckError, InvalidTrumpError
from .log_decorator import log_decorator
from .card import PinochleCard
from .deck import PinochleDeck


@log_decorator
def populate_deck():
    new_deck = PinochleDeck()
    # Add a deck of cards.
    new_deck.build()
    # Add a second set of cards.
    new_deck.build()

    new_deck.shuffle()
    return new_deck


@log_decorator
def deal_hands(players=4, deck=None, kitty_cards=0):
    if deck is None:
        deck = populate_deck()

    # Create empty hands
    hand = [None] * players
    for index in range(0, players):
        hand[index] = PinochleDeck(
            gameid=deck.gameid,
            rebuild=deck.rebuild,
            re_shuffle=deck.re_shuffle,
            ranks=deck.ranks,
            decks_used=deck.decks_used,
            build=False,
        )
    kitty = PinochleDeck(
        gameid=deck.gameid,
        rebuild=deck.rebuild,
        re_shuffle=deck.re_shuffle,
        ranks=deck.ranks,
        decks_used=deck.decks_used,
        build=False,
    )

    # If the number of players isn't evenly divisible into the size of the
    # deck, force a number of kitty cards, if none are requested.
    if kitty_cards == 0:
        remainder = deck.size % players
        if remainder != 0:
            kitty_cards = remainder

    # Pull out random cards for the kitty, if requested
    if kitty_cards > 0:
        kitty += deck.deal(kitty_cards)
        deck.shuffle()

    # Deal remaining cards equally to each player, one at a time and
    while deck.size > 0:
        for index in range(0, players):
            hand[index] += deck.deal()

    # Make sure everyone has the same size hand
    for index in range(0, players - 1):
        assert hand[index].size == hand[index + 1].size

    return hand, kitty


@log_decorator
def build_cards(jokers=False, num_jokers=0):
    """
    Builds a list containing a single (half) pinochle deck of 24 Card instances. The
    cards are sorted according to ``DEFAULT_RANKS``.

    .. note:
        Adding jokers may break some functions & methods at the moment.

    :arg bool jokers:
        Whether or not to include jokers in the deck. - Ignored - Pinochle decks do not
        use Jokers.
    :arg int num_jokers:
        The number of jokers to include. - Ignored - Pinochle decks do not use Jokers.

    :returns:
        A list containing a single (half) pinochle deck of 24 Card instances.

    """
    new_deck = []

    new_deck += [
        PinochleCard(value, suit) for value in const.VALUES for suit in const.SUITS
    ]

    return new_deck


@log_decorator
def sort_cards(cards, ranks=None):
    """
    Sorts a given list of cards, either by poker ranks, or big two ranks.

    :arg cards:
        The cards to sort.
    :arg dict ranks:
        The rank dict to reference for sorting. If ``None``, it will
        default to ``PINOCHLE_RANKS``.

    :returns:
        The sorted cards.

    """
    ranks = ranks or const.PINOCHLE_RANKS

    if ranks.get("suits"):
        cards = sorted(
            cards,
            key=lambda x: (-ranks["suits"][x.suit], -ranks["values"][x.value])
            if x.suit is not None
            else 0,
        )

    return cards


@log_decorator
def set_trump(trump="", hand=PinochleDeck()) -> PinochleDeck:
    if trump not in const.SUITS:
        raise InvalidTrumpError
    # if hand is not PinochleDeck:
    #     raise InvalidDeckError

    newhand = copy.deepcopy(hand)
    newhand.ranks["suits"][trump] = 10

    print(newhand.ranks)

    return newhand
