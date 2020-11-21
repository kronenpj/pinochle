"""
This module contains the ``PinochleDeck`` class.
Each new ``PinochleDeck`` instance contains a full 48 card Pinochle deck.
The ``PinochleDeck`` class is a subclass of the ``PinochleStack`` class,
with a few extra/overridden methods.

License: GPLv3
Derived from: https://github.com/Trebek/pydealer
Original author: Alex Crawford
Modernized and modified for Pinochle by Paul Kronenwetter
"""

# ===============================================================================
# PyDealer - Deck Class
# -------------------------------------------------------------------------------
# Version: 1.4.0
# Updated: 10-01-2015
# Author: Alex Crawford
# License: GPLv3
# ===============================================================================

"""
This module contains the ``Deck`` class. Each ``Deck`` instance contains a full,
52 card French deck of playing cards upon instantiation. The ``Deck`` class is
a subclass of the ``Stack`` class, with a few extra/differing methods.

"""

import copy
import uuid
from collections import deque

from . import const
from .card import PinochleCard
from .log_decorator import log_decorator
from .stack import PinochleStack


class PinochleDeck(PinochleStack):
    @log_decorator
    def __init__(self, **kwargs):
        """
        PinochleDeck constructor method.

        """
        self._cards = deque(kwargs.get("cards", []))

        self.gameid = kwargs.get("gameid", uuid.uuid4())
        self.rebuild = kwargs.get("rebuild", False)
        self.re_shuffle = kwargs.get("re_shuffle", False)
        self.ranks = kwargs.get("ranks", copy.deepcopy(const.PINOCHLE_RANKS))
        self.decks_used = 0

        if kwargs.get("build", False):
            self.build()

    def __add__(self, other):
        """
        Allows you to add (merge) decks together, with the ``+`` operand.

        :arg other:
            The other Deck to add to the Deck. Can be a ``PinochleStack`` or ``Deck``
            instance.

        :returns:
            A new PinochleDeck instance, with the combined cards.

        """
        try:
            new_deck = PinochleDeck(
                cards=(list(self.cards) + list(other.cards)),
                gameid=self.gameid,
                rebuild=self.rebuild,
                re_shuffle=self.re_shuffle,
                ranks=self.ranks,
                decks_used=self.decks_used,
                build=False,
            )
        except:
            new_deck = PinochleDeck(
                cards=list(self.cards) + other,
                gameid=self.gameid,
                rebuild=self.rebuild,
                re_shuffle=self.re_shuffle,
                ranks=self.ranks,
                decks_used=self.decks_used,
                build=False,
            )

        return new_deck

    def __repr__(self):
        """
        Returns a string representation of the ``PinochleDeck`` instance.

        :returns:
            A string representation of the PinochleDeck instance.

        """
        return "PinochleDeck(cards=%r)" % (self.cards)

    @log_decorator
    def build(self, jokers=False, num_jokers=0):
        """
        Builds a standard pinochle card deck of PinochleCard instances.

        :arg bool jokers:
            Whether or not to include jokers in the deck. - Ignored - Pinochle decks do
            not use Jokers.
        :arg int num_jokers:
            The number of jokers to include. - Ignored - Pinochle decks do not use
            Jokers.

        """
        self.decks_used += 1

        new_deck = []
        new_deck += [
            PinochleCard(value, suit) for value in const.VALUES for suit in const.SUITS
        ]
        self.cards += new_deck

    @log_decorator
    def sort(self, ranks=None):
        """
        Sorts the stack, either by poker ranks, or big two ranks.

        :arg dict ranks:
            The rank dict to reference for sorting. If ``None``, it will
            default to ``PINOCHLE_RANKS``.

        :returns:
            The sorted cards.

        """
        ranks = ranks or self.ranks

        if ranks.get("suits"):
            cards = sorted(
                self.cards,
                key=lambda x: (-ranks["suits"][x.suit], -ranks["values"][x.value])
                if x.suit is not None
                else 0,
            )
            self.cards = cards

    @log_decorator
    def deal(self, num=1, rebuild=False, shuffle=False, end=const.TOP):
        """
        Returns a list of cards, which are removed from the deck.

        :arg int num:
            The number of cards to deal.
        :arg bool rebuild:
            Whether or not to rebuild the deck when cards run out.
        :arg bool shuffle:
            Whether or not to shuffle on rebuild.
        :arg str end:
            The end of the ``PinochleStack`` to add the cards to. Can be ``TOP`` ("top")
            or ``BOTTOM`` ("bottom").

        :returns:
            A given number of cards from the deck.

        """
        _num = num

        rebuild = rebuild or self.rebuild
        re_shuffle = shuffle or self.re_shuffle

        self_size = self.size

        if rebuild or num <= self_size:
            dealt_cards = [None] * num
        elif num > self_size:
            dealt_cards = [None] * self_size

        while num > 0:
            ends = {const.TOP: self.cards.pop, const.BOTTOM: self.cards.popleft}
            n = _num - num
            try:
                card = ends[end]()
                dealt_cards[n] = card
                num -= 1
            except:
                if self.size == 0:
                    if rebuild:
                        self.build()
                        if re_shuffle:
                            self.shuffle()
                    else:
                        break

        return PinochleStack(cards=dealt_cards)


def convert_to_deck(stack):
    """
    Convert a ``PinochleStack`` to a ``Deck``.

    :arg PinochleStack stack:
        The ``PinochleStack`` instance to convert.

    """
    return PinochleDeck(cards=list(stack.cards))
