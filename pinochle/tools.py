"""
Generic tools to work with a stack of Pinochle cards.
These tools are helpful when working with sequences of cards, some
of which are used by the classes in the PyDealer package, such as the functions
``build_cards``, ``sort_cards``, and ``check_term`` for example.
This module is mostly used by PinochleStack.

License: GPLv3
Derived from: https://github.com/Trebek/pydealer
Original author: Alex Crawford
Modernized and modified for Pinochle by Paul Kronenwetter
"""

# ===============================================================================
# PyDealer - Tools
# -------------------------------------------------------------------------------
# Version: 1.4.0
# Updated: 10-01-2015
# Author: Alex Crawford
# License: GPLv3
# ===============================================================================

"""
The tools module contains functions for working with sequences of cards, some
of which are used by the classes in the PyDealer package, such as the functions
``build_cards``, ``sort_cards``, and ``check_term`` for example.

"""


# ===============================================================================
# Imports
# ===============================================================================

import random
import time

from .const import DEFAULT_RANKS, SUITS, VALUES
from .card import PinochleCard


# ===============================================================================
# Utility Functions
# ===============================================================================


def build_cards(jokers=False, num_jokers=0):
    """
    Builds a list containing a full French deck of 52 PinochleCard instances. The
    cards are sorted according to ``DEFAULT_RANKS``.

    .. note:
        Adding jokers may break some functions & methods at the moment.

    :arg bool jokers:
        Whether or not to include jokers in the deck.
    :arg int num_jokers:
        The number of jokers to include.

    :returns:
        A list containing a full French deck of 52 PinochleCard instances.

    """
    new_deck = []

    if jokers:
        new_deck += [PinochleCard("Joker", None) for i in range(num_jokers)]

    new_deck += [PinochleCard(value, suit) for value in VALUES for suit in SUITS]

    return new_deck


def check_sorted(cards, ranks=None):
    """
    Checks whether the given cards are sorted by the given ranks.

    :arg cards:
        The cards to check. Can be a ``Stack``, ``Deck``, or ``list`` of
        ``PinochleCard`` isntances.
    :arg dict ranks:
        The ranks to check against. Default is DEFAULT_RANKS.

    :returns:
        ``True`` or ``False``.

    """
    ranks = ranks or DEFAULT_RANKS

    sorted_cards = sort_cards(cards, ranks)

    if cards == sorted_cards or cards[::-1] == sorted_cards:
        return True
    else:
        return False


def check_term(card, term):
    """
    Checks a given search term against a given card's full name, suit,
    value, and abbreviation.

    :arg PinochleCard card:
        The card to check.
    :arg str term:
        The search term to check for. Can be a card full name, suit,
        value, or abbreviation.

    :returns:
        ``True`` or ``False``.

    """
    check_list = [
        x.lower()
        for x in [
            card.name,
            card.suit,
            card.value,
            card.abbrev,
            card.suit[0],
            card.value[0],
        ]
    ]

    term = term.lower()

    for check in check_list:
        if check == term:
            return True

    return False


def compare_stacks(cards_x, cards_y, sorted=False):
    """
    Checks whether two given ``Stack``, ``Deck``, or ``list`` instances,
    contain the same cards (based on value & suit, not instance). Does not
    take into account the ordering.

    :arg cards_x:
        The first stack to check. Can be a ``Stack``, ``Deck``, or ``list``
        instance.
    :arg cards_y:
        The second stack to check. Can be a ``Stack``, ``Deck``, or ``list``
        instance.
    :arg bool sorted:
        Whether or not the cards are already sorted. If ``True``, then
        ``compare_stacks`` will skip the sorting process.

    :returns:
        ``True`` or ``False``.

    """
    if len(cards_x) == len(cards_y):
        if not sorted:
            cards_x = sort_cards(cards_x, DEFAULT_RANKS)
            cards_y = sort_cards(cards_y, DEFAULT_RANKS)
        for i, c in enumerate(cards_x):
            if c != cards_y[i]:
                return False
        return True
    else:
        return False


def find_card(cards, term, limit=0, sort=False, ranks=None):
    """
    Searches the given cards for cards with a value, suit, name, or
    abbreviation matching the given argument, ``term``.

    :arg cards:
        The cards to search. Can be a ``Stack``, ``Deck`` or ``list``.
    :arg str term:
        The search term. Can be a card full name, value, suit,
        or abbreviation.
    :arg int limit:
        The number of items to retrieve for each term.
    :arg bool sort:
        Whether or not to sort the results, by poker ranks.
    :arg dict ranks:
        The rank dict to reference for sorting. If ``None``, it will
        default to ``DEFAULT_RANKS``.

    :returns:
        A list of indexes for the cards matching the given terms,
        if found.

    """
    found_indexes = []
    count = 0

    if not limit:
        for i, card in enumerate(cards):
            if check_term(card, term):
                found_indexes.append(i)
    else:
        for i, card in enumerate(cards):
            if count < limit:
                if check_term(card, term):
                    found_indexes.append(i)
                    count += 1
            else:
                break

    if sort:
        found_indexes = sort_card_indexes(self, found_indexes, ranks)

    return found_indexes


def find_list(cards, terms, limit=0, sort=False, ranks=None):
    """
    Searches the given cards for cards with a value, suit, name, or
    abbreviation matching the given argument, ``terms``.

    :arg cards:
        The cards to search. Can be a ``Stack``, ``Deck`` or ``list``.
    :arg list terms:
        The search terms. Can be card full names, suits, values,
        or abbreviations.
    :arg int limit:
        The number of items to retrieve for each term. 0 == no limit.
    :arg bool sort:
        Whether or not to sort the results, by poker ranks.
    :arg dict ranks:
        The rank dict to reference for sorting. If ``None``, it will
        default to ``DEFAULT_RANKS``.

    :returns:
        A list of indexes for the cards matching the given terms,
        if found.

    """
    found_indexes = []
    count = 0

    if not limit:
        for term in terms:
            for i, card in enumerate(cards):
                if check_term(card, term) and i not in found_indexes:
                    found_indexes.append(i)
    else:
        for term in terms:
            for i, card in enumerate(cards):
                if count < limit:
                    if check_term(card, term) and i not in found_indexes:
                        found_indexes.append(i)
                        count += 1
                else:
                    break
            count = 0

    if sort:
        found_indexes = sort_card_indexes(cards, found_indexes, ranks)

    return found_indexes


def get_card(cards, term, limit=0, sort=False, ranks=None):
    """
    Get the specified card from the stack.

    :arg cards:
        The cards to get from. Can be a ``Stack``, ``Deck`` or ``list``.
    :arg str term:
        The card's full name, value, suit, abbreviation, or stack index.
    :arg int limit:
        The number of items to retrieve for each term.
    :arg bool sort:
        Whether or not to sort the results, by poker ranks.
    :arg dict ranks:
        If ``sort=True``, the rank dict to refer to for sorting.

    :returns:
        A copy of the given cards, with the found cards removed, and a list
        of the specified cards, if found.

    """
    got_cards = []

    try:
        indexes = find_card(cards, term, limit=limit)
        got_cards = [cards[i] for i in indexes]
        cards = [v for i, v in enumerate(cards) if i not in indexes]
    except:
        got_cards = [cards[term]]
        cards = [v for i, v in enumerate(cards) if i is not term]

    if sort:
        got_cards = sort_cards(got_cards)

    return cards, got_cards


def get_list(cards, terms, limit=0, sort=False, ranks=None):
    """
    Get the specified cards from the stack.

    :arg cards:
        The cards to get from. Can be a ``Stack``, ``Deck`` or ``list``.
    :arg list terms:
        A list of card's full names, values, suits, abbreviations, or stack
        indexes.
    :arg int limit:
        The number of items to retrieve for each term.
    :arg bool sort:
        Whether or not to sort the results, by poker ranks.
    :arg dict ranks:
        If ``sort=True``, the rank dict to refer to for sorting.

    :returns:
        A list of the specified cards, if found.

    """
    got_cards = []

    try:
        indexes = find_list(cards, terms, limit=limit)
        got_cards = [cards[i] for i in indexes if cards[i] not in got_cards]
        cards = [v for i, v in enumerate(cards) if i not in indexes]
    except:
        indexes = []
        for item in terms:
            try:
                card = cards[item]
                if card not in got_cards:
                    got_cards.append(card)
                    indexes.append(item)
            except:
                indexes += find_card(cards, item, limit=limit)
                got_cards += [cards[i] for i in indexes if cards[i] not in got_cards]
        cards = [v for i, v in enumerate(cards) if i not in indexes]

    if sort:
        got_cards = sort_cards(got_cards, ranks)

    return cards, got_cards


def open_cards(filename=None):
    """
    Open cards from a txt file.

    :arg str filename:
        The filename of the deck file to open. If no filename given,
        defaults to "cards-YYYYMMDD.txt", where "YYYYMMDD" is the year, month,
        and day. For example, "cards-20140711.txt".

    :returns:
        The opened cards, as a list.

    """
    filename = filename or "cards-%s.txt" % (time.strftime("%Y%m%d"))

    with open(filename, "r") as deck_file:
        card_data = [line.rstrip("\n") for line in deck_file.readlines()]

    cards = [None] * len(card_data)

    for i, card in enumerate(card_data):
        card = card.split()
        cards[i] = PinochleCard(card[0], card[1])

    return cards


def random_card(cards, remove=False):
    """
    Returns a random card from the Stack. If ``remove=True``, it will
    also remove the card from the deck.

    :arg bool remove:
        Whether or not to remove the card from the deck.

    :returns:
        A random PinochleCard object, from the Stack.

    """
    if not remove:
        return random.choice(cards)
    else:
        i = random.randrange(len(cards))
        card = cards[i]
        del cards[i]
        return card


def save_cards(cards, filename=None):
    """
    Save the given cards, in plain text, to a txt file.

    :arg cards:
        The cards to save. Can be a ``Stack``, ``Deck``, or ``list``.
    :arg str filename:
        The filename to use for the cards file. If no filename given,
        defaults to "cards-YYYYMMDD.txt", where "YYYYMMDD" is the year, month,
        and day. For example, "cards-20140711.txt".

    """
    filename = filename or "cards-%s.txt" % (time.strftime("%Y%m%d"))

    with open(filename, "w") as deck_file:
        card_reprs = ["%s %s\n" % (card.value, card.suit) for card in cards]
        card_reprs[-1] = card_reprs[-1].rstrip("\n")
        for card in card_reprs:
            deck_file.write(card)


def sort_card_indexes(cards, indexes, ranks=None):
    """
    Sorts the given Deck indexes by the given ranks. Must also supply the
    ``Stack``, ``Deck``, or ``list`` that the indexes are from.

    :arg cards:
        The cards the indexes are from. Can be a ``Stack``, ``Deck``, or
        ``list``
    :arg list indexes:
        The indexes to sort.
    :arg dict ranks:
        The rank dict to reference for sorting. If ``None``, it will
        default to ``DEFAULT_RANKS``.

    :returns:
        The sorted indexes.

    """
    ranks = ranks or DEFAULT_RANKS

    if ranks.get("suits"):
        indexes = sorted(
            indexes,
            key=lambda x: ranks["suits"][cards[x].suit] if cards[x].suit != None else 0,
        )
    if ranks.get("values"):
        indexes = sorted(indexes, key=lambda x: ranks["values"][cards[x].value])

    return indexes


def sort_cards(cards, ranks=None):
    """
    Sorts a given list of cards, either by poker ranks, or big two ranks.

    :arg cards:
        The cards to sort.
    :arg dict ranks:
        The rank dict to reference for sorting. If ``None``, it will
        default to ``DEFAULT_RANKS``.

    :returns:
        The sorted cards.

    """
    ranks = ranks or DEFAULT_RANKS

    if ranks.get("suits"):
        cards = sorted(
            cards, key=lambda x: ranks["suits"][x.suit] if x.suit != None else 0
        )
    if ranks.get("values"):
        cards = sorted(cards, key=lambda x: ranks["values"][x.value])

    return cards
