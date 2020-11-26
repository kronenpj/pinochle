"""
This module contains the ``PinochleStack`` class.
This class is the backbone of the Pinochle game. A ``PinochleStack`` is a generic
"card container", with all of the methods needed to work with the
cards they contain. A ``PinochleStack`` can be used as a hand, a
discard pile, etc.

License: GPLv3
Derived from: https://github.com/Trebek/pydealer
Original author: Alex Crawford
Modernized and modified for Pinochle by Paul Kronenwetter
"""

# ===============================================================================
# PyDealer - Stack Class
# -------------------------------------------------------------------------------
# Version: 1.4.0
# Updated: 10-01-2015
# Author: Alex Crawford
# License: GPLv3
# ===============================================================================

"""
This module contains the ``Stack`` class, which is the backbone of the PyDealer
package. A ``Stack`` is essentially just a generic "card container", with all of
the methods users may need to work with the cards they contain. A ``Stack`` can
be used as a hand, or a discard pile, etc.

"""


# ===============================================================================
# Imports
# ===============================================================================

from copy import deepcopy
import random
from collections import deque

from pinochle import tools
from pinochle.const import BOTTOM, DEFAULT_RANKS, TOP

# ===============================================================================
# PinochleStack Class
# ===============================================================================


class PinochleStack:
    """
    The PinochleStack class, representing a collection of cards. This is the main
    'card container' class, with methods for manipulating it's contents.

    :arg list cards:
        A list of cards to be the initial contents of the PinochleStack.
    :arg dict ranks:
        If ``sort=True``, The rank dict to reference for sorting.
        Defaults to ``DEFAULT_RANKS``.
    :arg bool sort:
        Whether or not to sort the stack upon instantiation.

    """

    def __init__(self, **kwargs):
        """
        PinochleStack constructor method.

        :arg list cards:
            A list of cards to be the initial contents of the PinochleStack.
        :arg dict ranks:
            If ``sort=True``, The rank dict to reference for sorting.
            Defaults to ``DEFAULT_RANKS``.
        :arg bool sort:
            Whether or not to sort the stack upon instantiation.

        """
        self._cards = deque(kwargs.get("cards", []))
        self.ranks = kwargs.get("ranks", deepcopy(DEFAULT_RANKS))

        self._i = 0

        if kwargs.get("sort"):
            self.sort(self.ranks)

    def __add__(self, other):
        """
        Allows users to add (merge) PinochleStack/PinochleDeck instances together, with the
        ``+`` operand. You can also add a list of ``PinochleCard`` instances to a
        PinochleStack/PinochleDeck instance.

        :arg other:
            The other ``PinochleStack``, or ``PinochleDeck`` instance, or list of ``PinochleCard``
            instances to add to the ``PinochleStack``/``PinochleDeck`` instance.

        :returns:
            A new ``PinochleStack`` instance, with the combined cards.

        """
        try:
            new_stack = PinochleStack(cards=(list(self.cards) + list(other.cards)))
        except:
            new_stack = PinochleStack(cards=(list(self.cards) + other))

        return new_stack

    def __contains__(self, card):
        """
        Allows for ``PinochleCard`` instance (not value & suit) inclusion checks.

        :arg Card card:
            The ``PinochleCard`` instance to check for.

        :returns:
            Whether or not the ``PinochleCard`` instance is in the Deck.

        """
        return id(card) in [id(x) for x in self.cards]

    def __delitem__(self, index):
        """
        Allows for deletion of a ``PinochleCard`` instance, using del.

        :arg int index:
            The index to delete.

        """
        del self.cards[index]

    def __eq__(self, other):
        """
        Allows for PinochleStack comparisons. Checks to see if the given ``other``
        contains the same cards, in the same order (based on value & suit,
        not instance).

        :arg other:
            The other ``PinochleStack``/``PinochleDeck`` instance or ``list`` to compare to.

        :returns:
            ``True`` or ``False``.

        """
        if len(self.cards) == len(other):
            for i, card in enumerate(self.cards):
                if card != other[i]:
                    return False
            return True

        return False

    def __getitem__(self, key):
        """
        Allows for accessing, and slicing of cards, using ``PinochleDeck[index]``,
        ``PinochleDeck[start:stop]``, etc.

        :arg int index:
            The index to get.

        :returns:
            The ``PinochleCard`` at the given index.

        """
        self_len = len(self)
        if isinstance(key, slice):
            return [self[i] for i in range(*key.indices(self_len))]
        if isinstance(key, int):
            if key < 0:
                key += self_len
            if key >= self_len:
                raise IndexError("The index ({}) is out of range.".format(key))
            return self.cards[key]

        raise TypeError("Invalid argument type.")

    def __len__(self):
        """
        Allows check the PinochleStack length, with len.

        :returns:
            The length of the stack (self.cards).

        """
        return len(self.cards)

    def __ne__(self, other):
        """
        Allows for PinochleStack comparisons. Checks to see if the given ``other``
        does not contain the same cards, in the same order (based on value &
        suit, not instance).

        :arg other:
            The other ``PinochleStack``/``PinochleDeck`` instance or ``list`` to compare to.

        :returns:
            ``True`` or ``False``.

        """
        if len(self.cards) == len(other):
            for i, card in enumerate(self.cards):
                if card != other[i]:
                    return True
            return False

        return True

    def __repr__(self):
        """
        The repr magic method.

        :returns:
            A representation of the ``PinochleStack`` instance.

        """
        return "PinochleStack(cards=%r)" % (self.cards)

    def __setitem__(self, index, value):
        """
        Assign cards to specific stack indexes, like a list.

        Example:
            stack[16] = card_object

        :arg int index:
            The index to set.
        :arg Card value:
            The Card to set the index to.

        """
        self.cards[index] = value

    def __str__(self):
        """
        Allows users to print a human readable representation of the ``PinochleStack``
        instance, using ``print``.

        :returns:
            A str of the names of the cards in the stack.

        """
        card_names = "".join([x.name + "\n" for x in self.cards]).rstrip("\n")
        return "%s" % (card_names)

    def add(self, cards, end=TOP):
        """
        Adds the given list of ``PinochleCard`` instances to the top of the stack.

        :arg cards:
            The cards to add to the ``PinochleStack``. Can be a single ``PinochleCard``
            instance, or a ``list`` of cards.
        :arg str end:
            The end of the ``PinochleStack`` to add the cards to. Can be ``TOP`` ("top")
            or ``BOTTOM`` ("bottom").

        """
        if end is TOP:
            try:
                self.cards += cards
            except:
                self.cards += [cards]
        elif end is BOTTOM:
            try:
                self.cards.extendleft(cards)
            except:
                self.cards.extendleft([cards])

    @property
    def cards(self):
        """
        The cards property.

        :returns:
            The cards in the PinochleStack/PinochleDeck.

        """
        return self._cards

    @cards.setter
    def cards(self, items):
        """
        The cards property setter. This makes sure that if ``PinochleStack.cards`` is
        set directly, that the items are in a deque.

        :arg items:
            The list of PinochleCard instances, or a PinochleStack/PinochleDeck
            instance to assign to the PinochleStack/PinochleDeck.

        """
        self._cards = deque(items)

    def deal(self, num=1, end=TOP):
        """
        Returns a list of cards, which are removed from the PinochleStack.

        :arg int num:
            The number of cards to deal.
        :arg str end:
            Which end to deal from. Can be ``0`` (top) or ``1`` (bottom).

        :returns:
            The given number of cards from the stack.

        """
        ends = {TOP: self.cards.pop, BOTTOM: self.cards.popleft}

        self_size = self.size

        if num <= self_size:
            dealt_cards = [None] * num
        else:
            num = self_size
            dealt_cards = [None] * self_size

        if self_size:
            for n in range(num):
                try:
                    card = ends[end]()
                    dealt_cards[n] = card
                except:
                    break

            return PinochleStack(cards=dealt_cards)

        return PinochleStack()

    def empty(self, return_cards=False):
        """
        Empties the stack, removing all cards from it, and returns them.

        :arg bool return_cards:
            Whether or not to return the cards.

        :returns:
            If ``return_cards=True``, a list containing the cards removed
            from the PinochleStack.

        """
        cards = list(self.cards)
        self.cards = []

        if return_cards:
            return cards

    def find(self, term, limit=0, sort=False, ranks=None):
        """
        Searches the stack for cards with a value, suit, name, or
        abbreviation matching the given argument, 'term'.

        :arg str term:
            The search term. Can be a card full name, value, suit,
            or abbreviation.
        :arg int limit:
            The number of items to retrieve for each term. ``0`` equals
            no limit.
        :arg bool sort:
            Whether or not to sort the results.
        :arg dict ranks:
            The rank dict to reference for sorting. If ``None``, it will
            default to ``DEFAULT_RANKS``.

        :returns:
            A list of stack indexes for the cards matching the given terms,
            if found.

        """
        ranks = ranks or self.ranks
        found_indexes = []
        count = 0

        if not limit:
            for i, card in enumerate(self.cards):
                if tools.check_term(card, term):
                    found_indexes.append(i)
        else:
            for i, card in enumerate(self.cards):
                if count < limit:
                    if tools.check_term(card, term):
                        found_indexes.append(i)
                        count += 1
                else:
                    break

        if sort:
            found_indexes = tools.sort_card_indexes(self, found_indexes, ranks)

        return found_indexes

    def find_list(self, terms, limit=0, sort=False, ranks=None):
        """
        Searches the stack for cards with a value, suit, name, or
        abbreviation matching the given argument, 'terms'.

        :arg list terms:
            The search terms. Can be card full names, suits, values,
            or abbreviations.
        :arg int limit:
            The number of items to retrieve for each term.
        :arg bool sort:
            Whether or not to sort the results, by poker ranks.
        :arg dict ranks:
            The rank dict to reference for sorting. If ``None``, it will
            default to ``DEFAULT_RANKS``.

        :returns:
            A list of stack indexes for the cards matching the given terms,
            if found.

        """
        ranks = ranks or self.ranks
        found_indexes = []
        count = 0

        if not limit:
            for term in terms:
                for i, card in enumerate(self.cards):
                    if tools.check_term(card, term) and i not in found_indexes:
                        found_indexes.append(i)
        else:
            for term in terms:
                for i, card in enumerate(self.cards):
                    if count < limit:
                        if tools.check_term(card, term) and i not in found_indexes:
                            found_indexes.append(i)
                            count += 1
                    else:
                        break
                count = 0

        if sort:
            found_indexes = tools.sort_card_indexes(self, found_indexes, ranks)

        return found_indexes

    def get(self, term, limit=0, sort=False, ranks=None):
        """
        Get the specified card from the stack.

        :arg term:
            The search term. Can be a card full name, value, suit,
            abbreviation, or stack index.
        :arg int limit:
            The number of items to retrieve for each term.
        :arg bool sort:
            Whether or not to sort the results, by poker ranks.
        :arg dict ranks:
            The rank dict to reference for sorting. If ``None``, it will
            default to ``DEFAULT_RANKS``.

        :returns:
            A list of the specified cards, if found.

        """
        ranks = ranks or self.ranks
        got_cards = []

        try:
            indexes = self.find(term, limit=limit)
            got_cards = [self.cards[i] for i in indexes]
            self.cards = [v for i, v in enumerate(self.cards) if i not in indexes]
        except:
            got_cards = [self.cards[term]]
            self.cards = [v for i, v in enumerate(self.cards) if i is not term]

        if sort:
            got_cards = tools.sort_cards(got_cards, ranks)

        return got_cards

    def get_list(self, terms, limit=0, sort=False, ranks=None):
        """
        Get the specified cards from the stack.

        :arg term:
            The search term. Can be a card full name, value, suit,
            abbreviation, or stack index.
        :arg int limit:
            The number of items to retrieve for each term.
        :arg bool sort:
            Whether or not to sort the results, by poker ranks.
        :arg dict ranks:
            The rank dict to reference for sorting. If ``None``, it will
            default to ``DEFAULT_RANKS``.

        :returns:
            A list of the specified cards, if found.

        """
        ranks = ranks or self.ranks
        got_cards = []

        try:
            indexes = self.find_list(terms, limit=limit)
            got_cards = [
                self.cards[i] for i in indexes if self.cards[i] not in got_cards
            ]
            self.cards = [v for i, v in enumerate(self.cards) if i not in indexes]
        except:
            indexes = []
            for item in terms:
                try:
                    card = self.cards[item]
                    if card not in got_cards:
                        got_cards.append(card)
                        indexes.append(item)
                except:
                    indexes += self.find(item, limit=limit)
                    got_cards += [
                        self.cards[i] for i in indexes if self.cards[i] not in got_cards
                    ]
            self.cards = [v for i, v in enumerate(self.cards) if i not in indexes]

        if sort:
            got_cards = tools.sort_cards(got_cards, ranks)

        return got_cards

    def insert(self, card, index=-1):
        """
        Insert a given card into the stack at a given index.

        :arg Card card:
            The card to insert into the stack.
        :arg int index:
            Where to insert the given card.

        """
        self_size = len(self.cards)

        if index in [0, -1]:
            if index == -1:
                self.cards.append(card)
            else:
                self.cards.appendleft(card)
        elif index != self_size:
            half_x, half_y = self.split(index)
            self.cards = list(half_x.cards) + [card] + list(half_y.cards)

    def insert_list(self, cards, index=-1):
        """
        Insert a list of given cards into the stack at a given index.

        :arg list cards:
            The list of cards to insert into the stack.
        :arg int index:
            Where to insert the given cards.

        """
        self_size = len(self.cards)

        if index in [0, -1]:
            if index == -1:
                self.cards += cards
            else:
                self.cards.extendleft(cards)
        elif index != self_size:
            half_x, half_y = self.split(index)
            self.cards = list(half_x.cards) + list(cards) + list(half_y.cards)

    def is_sorted(self, ranks=None):
        """
        Checks whether the stack is sorted.

        :arg dict ranks:
            The rank dict to reference for checking. If ``None``, it will
            default to ``DEFAULT_RANKS``.

        :returns:
            Whether or not the cards are sorted.

        """
        ranks = ranks or self.ranks

        return tools.check_sorted(self, ranks)

    def open_cards(self, filename=None):
        """
        Open cards from a txt file.

        :arg str filename:
            The filename of the deck file to open. If no filename given,
            defaults to "cards-YYYYMMDD.txt", where "YYYYMMDD" is the year,
            month, and day. For example, "cards-20140711.txt".

        """
        self.cards = tools.open_cards(filename)

    def random_card(self, remove=False):
        """
        Returns a random card from the PinochleStack. If ``remove=True``, it will
        also remove the card from the deck.

        :arg bool remove:
            Whether or not to remove the card from the deck.

        :returns:
            A random Card object, from the PinochleStack.

        """
        return tools.random_card(self, remove)

    def reverse(self):
        """Reverse the order of the PinochleStack in place."""

        self.cards = self[::-1]

    def save_cards(self, filename=None):
        """
        Save the current stack contents, in plain text, to a txt file.

        :arg str filename:
            The filename to use for the file. If no filename given, defaults
            to "cards-YYYYMMDD.txt", where "YYYYMMDD" is the year, month, and
            day. For example, "cards-20140711.txt".

        """
        tools.save_cards(self, filename)

    def set_cards(self, cards):
        """
        Change the Deck's current contents to the given cards.

        :arg list cards:
            The Cards to assign to the stack.

        """
        self.cards = cards

    def shuffle(self, times=1):
        """
        Shuffles the PinochleStack.

        .. note::
            Shuffling large numbers of cards (100,000+) may take a while.

        :arg int times:
            The number of times to shuffle.

        """
        for _ in range(times):
            random.shuffle(self.cards)

    @property
    def size(self):
        """
        Counts the number of cards currently in the stack.

        :returns:
            The number of cards in the stack.

        """
        return len(self.cards)

    def sort(self, ranks=None):
        """
        Sorts the stack, either by poker ranks, or big two ranks.

        :arg dict ranks:
            The rank dict to reference for sorting. If ``None``, it will
            default to ``DEFAULT_RANKS``.

        :returns:
            The sorted cards.

        """
        ranks = ranks or self.ranks
        self.cards = tools.sort_cards(self.cards, ranks)

    def split(self, index=None):
        """
        Splits the PinochleStack, either in half, or at the given index, into two
        separate PinochleStacks.

        :arg int index:
            Optional. The index to split the PinochleStack at. Defaults to the middle
            of the ``PinochleStack``.

        :returns:
            The two parts of the PinochleStack, as separate PinochleStack instances.

        """
        self_size = self.size
        if self_size > 1:
            if not index:
                mid = self_size // 2
                return PinochleStack(cards=self[0:mid]), PinochleStack(
                    cards=self[mid::]
                )

            return PinochleStack(cards=self[0:index]), PinochleStack(
                cards=self[index::]
            )

        return PinochleStack(cards=self.cards), PinochleStack()


# ===============================================================================
# Helper Functions
# ===============================================================================


def convert_to_stack(deck):
    """
    Convert a ``PinochleDeck`` to a ``PinochleStack``.

    :arg Deck deck:
        The ``PinochleDeck`` to convert.

    :returns:
        A new ``PinochleStack`` instance, containing the cards from the given ``PinochleDeck``
        instance.

    """
    return PinochleStack(cards=list(deck.cards))
