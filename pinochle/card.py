"""
This module contains the ``PinochleCard`` class.
Each ``PinochleCard`` instance represents a single playing card
of a given value and suit.

License: GPLv3
Derived from: https://github.com/Trebek/pydealer
Original author: Alex Crawford
Modernized and modified for Pinochle by Paul Kronenwetter
"""
# ===============================================================================
# PyDealer - Card Class
# -------------------------------------------------------------------------------
# Version: 1.4.0
# Updated: 10-01-2015
# Author: Alex Crawford
# License: GPLv3
# ===============================================================================

"""
This module contains the ``Card`` class. Each ``Card`` instance represents a
single playing card, of a given value and suit.

"""


# ===============================================================================
# Imports
# ===============================================================================

from typing import Union
from . import const

# ===============================================================================
# PinochleCard Class
# ===============================================================================


class PinochleCard:
    """
    The PinocleCard class, each instance representing a single playing card.

    :arg str value:
        The card value.
    :arg str suit:
        The card suit.

    """

    value: Union[str, None] = None
    suit: Union[str, None] = None

    def __init__(self, value: str, suit: Union[str, None]):
        """
        PinochleCard constructor method.

        :arg str value:
            The card value.
        :arg str suit:
            The card suit.

        """
        if (
            str(value).capitalize() not in const.VALUES
            or str(suit).capitalize() not in const.SUITS
        ):
            raise ValueError
        self.value: str = str(value).capitalize()
        self.suit: str = str(suit).capitalize() if suit else suit
        self.abbrev: str = card_abbrev(self.value, self.suit)
        self.name: str = card_name(self.value, self.suit)

    def __eq__(self, other):
        """
        Allows for PinochleCard value/suit equality comparisons.

        :arg PinochleCard other:
            The other card to compare to.

        :returns:
            ``True`` or ``False``.

        """
        return (
            isinstance(other, PinochleCard)
            and self.value == other.value
            and self.suit == other.suit
        )

    def __ne__(self, other):
        """
        Allows for PinochleCard value/suit equality comparisons.

        :arg PinochleCard other:
            The other card to compare to.

        :returns:
            ``True`` or ``False``.

        """
        return (
            isinstance(other, PinochleCard)
            and self.value != other.value
            or self.suit != other.suit
        )

    def __ge__(self, other):
        """
        Allows for PinochleCard ranking comparisons. Uses DEFAULT_RANKS for comparisons.

        :arg PinochleCard other:
            The other card to compare to.

        :returns:
            ``True`` or ``False``.

        """
        if isinstance(other, PinochleCard):
            return (
                const.DEFAULT_RANKS["values"][self.value]
                > const.DEFAULT_RANKS["values"][other.value]
            ) or (
                const.DEFAULT_RANKS["values"][self.value]
                >= const.DEFAULT_RANKS["values"][other.value]
                and const.DEFAULT_RANKS["suits"][self.suit]
                >= const.DEFAULT_RANKS["suits"][other.suit]
            )

        return False

    def __gt__(self, other):
        """
        Allows for PinochleCard ranking comparisons. Uses DEFAULT_RANKS for comparisons.

        :arg PinochleCard other:
            The other card to compare to.

        :returns:
            ``True`` or ``False``.

        """
        if isinstance(other, PinochleCard):
            return (
                const.DEFAULT_RANKS["values"][self.value]
                > const.DEFAULT_RANKS["values"][other.value]
            ) or (
                const.DEFAULT_RANKS["values"][self.value]
                >= const.DEFAULT_RANKS["values"][other.value]
                and const.DEFAULT_RANKS["suits"][self.suit]
                > const.DEFAULT_RANKS["suits"][other.suit]
            )

        return False

    def __hash__(self):
        """
        Returns the hash value of the ``PinochleCard`` instance.

        :returns:
            A unique number, or hash for the PinochleCard.

        """
        return hash((self.value, self.suit))

    def __repr__(self):
        """
        Returns a string representation of the ``PinochleCard`` instance.

        :returns:
            A string representation of the PinochleCard instance.

        """
        return "PinochleCard(value=%r, suit=%r)" % (self.value, self.suit)

    def __str__(self):
        """
        Returns the full name of the ``PinochleCard`` instance.

        :returns:
            The card name.

        """
        return "%s" % (self.name)

    def eq(self, other, ranks=None):
        """
        Compares the card against another card, ``other``, and checks whether
        the card is equal to ``other``, based on the given rank dict.

        :arg PinochleCard other:
            The second PinochleCard to compare.
        :arg dict ranks:
            The ranks to refer to for comparisons.

        :returns:
            ``True`` or ``False``.

        """
        ranks = ranks or const.DEFAULT_RANKS
        if isinstance(other, PinochleCard):
            if ranks.get("suits"):
                return (
                    ranks["values"][self.value] == ranks["values"][other.value]
                    and ranks["suits"][self.suit] == ranks["suits"][other.suit]
                )

            return ranks[self.value] == ranks[other.value]

        return False

    def ge(self, other, ranks=None):
        """
        Compares the card against another card, ``other``, and checks whether
        the card is greater than or equal to ``other``, based on the given rank
        dict.

        :arg PinochleCard other:
            The second PinochleCard to compare.
        :arg dict ranks:
            The ranks to refer to for comparisons.

        :returns:
            ``True`` or ``False``.

        """
        ranks = ranks or const.DEFAULT_RANKS
        if isinstance(other, PinochleCard):
            if ranks.get("suits"):
                return ranks["values"][self.value] > ranks["values"][other.value] or (
                    ranks["values"][self.value] >= ranks["values"][other.value]
                    and ranks["suits"][self.suit] >= ranks["suits"][other.suit]
                )

            return ranks[self.value] >= ranks[other.value]

        return False

    def gt(self, other, ranks=None):
        """
        Compares the card against another card, ``other``, and checks whether
        the card is greater than ``other``, based on the given rank dict.

        :arg PinochleCard other:
            The second PinochleCard to compare.
        :arg dict ranks:
            The ranks to refer to for comparisons.

        :returns:
            ``True`` or ``False``.

        """
        ranks = ranks or const.DEFAULT_RANKS
        if isinstance(other, PinochleCard):
            if ranks.get("suits"):
                return ranks["values"][self.value] > ranks["values"][other.value] or (
                    ranks["values"][self.value] >= ranks["values"][other.value]
                    and ranks["suits"][self.suit] > ranks["suits"][other.suit]
                )

            return ranks[self.value] > ranks[other.value]

        return False

    def le(self, other, ranks=None):
        """
        Compares the card against another card, ``other``, and checks whether
        the card is less than or equal to ``other``, based on the given rank
        dict.

        :arg PinochleCard other:
            The second PinochleCard to compare.
        :arg dict ranks:
            The ranks to refer to for comparisons.

        :returns:
            ``True`` or ``False``.

        """
        ranks = ranks or const.DEFAULT_RANKS
        if isinstance(other, PinochleCard):
            if ranks.get("suits"):
                return ranks["values"][self.value] <= ranks["values"][other.value] or (
                    ranks["values"][self.value] <= ranks["values"][other.value]
                    and ranks["suits"][self.suit] <= ranks["suits"][other.suit]
                )

            return ranks[self.value] <= ranks[other.value]

        return False

    def lt(self, other, ranks=None):
        """
        Compares the card against another card, ``other``, and checks whether
        the card is less than ``other``, based on the given rank dict.

        :arg PinochleCard other:
            The second PinochleCard to compare.
        :arg dict ranks:
            The ranks to refer to for comparisons.

        :returns:
            ``True`` or ``False``.

        """
        ranks = ranks or const.DEFAULT_RANKS
        if isinstance(other, PinochleCard):
            if ranks.get("suits"):
                return ranks["values"][self.value] < ranks["values"][other.value] or (
                    ranks["values"][self.value] <= ranks["values"][other.value]
                    and ranks["suits"][self.suit] < ranks["suits"][other.suit]
                )

            return ranks[self.value] < ranks[other.value]

        return False

    def ne(self, other, ranks=None):
        """
        Compares the card against another card, ``other``, and checks whether
        the card is not equal to ``other``, based on the given rank dict.

        :arg PinochleCard other:
            The second PinochleCard to compare.
        :arg dict ranks:
            The ranks to refer to for comparisons.

        :returns:
            ``True`` or ``False``.

        """
        ranks = ranks or const.DEFAULT_RANKS
        if isinstance(other, PinochleCard):
            if ranks.get("suits"):
                return (
                    ranks["values"][self.value] != ranks["values"][other.value]
                    or ranks["suits"][self.suit] != ranks["suits"][other.suit]
                )

            return ranks[self.value] != ranks[other.value]

        return False


# ===============================================================================
# Helper Functions
# ===============================================================================


def card_abbrev(value: str, suit: Union[str, None]) -> str:
    """
    Constructs an abbreviation for the card, using the given
    value, and suit.

    :arg str value:
        The value to use.
    :arg str suit:
        The suit to use.

    :returns:
        A newly constructed abbreviation, using the given value
        & suit

    """
    if value == "Joker":
        return "JKR"
    if value == "10":
        return "10%s" % (suit[0])

    return "%s%s" % (value[0], suit[0])


def card_name(value: str, suit: Union[str, None]) -> str:
    """
    Constructs a name for the card, using the given value,
    and suit.

    :arg str value:
        The value to use.
    :arg str suit:
        The suit to use.

    :returns:
        A newly constructed name, using the given value & suit.

    """
    if value == "Joker":
        return "Joker"

    return "%s of %s" % (value, suit)
