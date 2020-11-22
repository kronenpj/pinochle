"""
This test exercises the ``Pinochle Tools`` module.

License: GPLv3
Derived from: https://github.com/Trebek/pydealer
Original author: Alex Crawford
Modernized and modified for Pinochle by Paul Kronenwetter
"""

# ===============================================================================
# PyDealer - Tests - Tools
# -------------------------------------------------------------------------------
# Version: 1.4.0
# Updated: 10-01-2015
# Author: Alex Crawford
# License: GPLv3
# ===============================================================================

# ===============================================================================
# Imports
# ===============================================================================

import unittest

from pinochle import const, card, deck, stack, tools

# ===============================================================================
# TestTools Class
# ===============================================================================


class TestTools(unittest.TestCase):
    def setUp(self):
        """"""
        self.ace_spades = card.PinochleCard("Ace", "Spades")
        self.nine_diamonds = card.PinochleCard("9", "Diamonds")
        self.queen_hearts = card.PinochleCard("Queen", "Hearts")
        self.king_clubs = card.PinochleCard("King", "Clubs")
        self.cards = [
            self.ace_spades,
            self.nine_diamonds,
            self.queen_hearts,
            self.king_clubs,
        ]
        self.names = [
            "Ace of Spades",
            "9 of Diamonds",
            "Queen of Hearts",
            "King of Clubs",
        ]
        self.deck = deck.PinochleDeck(build=True)
        self.stack = stack.PinochleStack(cards=self.cards)
        # pass

    def find_list_helper(self, stack, got_cards):
        """"""
        self.assertEqual(len(got_cards), 4)

        for i, name in enumerate(self.names):
            self.assertEqual(stack[got_cards[i]].name, name)

    def get_list_helper(self, left, got_cards):
        """"""
        self.assertEqual(len(got_cards), 4)
        self.assertEqual(len(left), 0)

        for i, name in enumerate(self.names):
            self.assertEqual(got_cards[i].name, name)

    def test_build_cards(self):
        """"""
        cards = tools.build_cards()

        self.assertEqual(list(self.deck.cards), cards)

    def test_check_sorted(self):
        """"""
        result = tools.check_sorted(self.deck, ranks=const.PINOCHLE_RANKS)

        self.assertEqual(result, True)

    def test_check_term(self):
        """"""
        result = tools.check_term(self.deck[0], "9 of Diamonds")

        self.assertEqual(result, True)

    def test_compare_stacks(self):
        """"""
        other_deck = deck.PinochleDeck(build=True)

        result = tools.compare_stacks(self.deck, other_deck)

        self.assertEqual(result, True)

    def test_find_card_abbrev(self):
        """"""
        found = tools.find_card(self.deck, "AS")
        i = found[0]

        self.assertEqual(len(found), 1)
        self.assertEqual(self.deck[i].name, "Ace of Spades")

    def test_find_card_full(self):
        """"""
        found = tools.find_card(self.deck, "Ace of Spades")
        i = found[0]

        self.assertEqual(len(found), 1)
        self.assertEqual(self.deck[i].name, "Ace of Spades")

    def test_find_card_partial_value(self):
        """"""
        found = tools.find_card(self.deck, "Ace")

        self.assertEqual(len(found), 4)
        for i in found:
            self.assertEqual(self.deck[i].value, "Ace")

    def test_find_card_partial_suit(self):
        """"""
        found = tools.find_card(self.deck, "Spades")

        self.assertEqual(len(found), 6)
        for i in found:
            self.assertEqual(self.deck[i].suit, "Spades")

    def test_find_card_limit(self):
        """"""
        found = tools.find_card(self.deck, "Spades", limit=1)

        self.assertEqual(len(found), 1)

    def test_find_list_full(self):
        """"""
        full_list = [
            "Ace of Spades",
            "9 of Diamonds",
            "Queen of Hearts",
            "King of Clubs",
        ]

        found = tools.find_list(self.stack, full_list)

        self.find_list_helper(self.stack, found)

    def test_find_list_abbrev(self):
        """"""
        abbrev_list = ["AS", "9D", "QH", "KC"]

        found = tools.find_list(self.stack, abbrev_list)

        self.find_list_helper(self.stack, found)

    def test_find_list_partial_value(self):
        """"""
        partial_list = ["Ace", "9", "Queen", "King"]

        found = tools.find_list(self.stack, partial_list)

        self.find_list_helper(self.stack, found)

    def test_find_list_partial_suit(self):
        """"""
        partial_list = ["Spades", "Diamonds", "Hearts", "Clubs"]

        found = tools.find_list(self.stack, partial_list)

        self.find_list_helper(self.stack, found)

    def test_find_list_mixed(self):
        """"""
        mixed_list = ["AS", "9 of Diamonds", "Hearts", "K"]

        found = tools.find_list(self.stack, mixed_list)

        self.find_list_helper(self.stack, found)

    def test_find_list_limit(self):
        """"""
        found = tools.find_list(self.stack, ["Spades"], limit=1)

        self.assertEqual(len(found), 1)

    def test_get_card_abbrev(self):
        """"""
        left, got_cards = tools.get_card(self.deck, "AS")
        test_card = got_cards[0]

        self.assertEqual(len(got_cards), 1)
        self.assertEqual(len(left), 23)
        self.assertEqual(test_card.name, "Ace of Spades")

    def test_get_card_full(self):
        """"""
        left, got_cards = tools.get_card(self.deck, "Ace of Spades")
        test_card = got_cards[0]

        self.assertEqual(len(got_cards), 1)
        self.assertEqual(len(left), 23)
        self.assertEqual(test_card.name, "Ace of Spades")

    def test_get_card_partial_value(self):
        """"""
        left, got_cards = tools.get_card(self.deck, "Ace")

        self.assertEqual(len(got_cards), 4)
        self.assertEqual(len(left), 20)
        for test_card in got_cards:
            self.assertEqual(test_card.value, "Ace")

    def test_get_card_partial_suit(self):
        """"""
        left, got_cards = tools.get_card(self.deck, "Spades")

        self.assertEqual(len(got_cards), 6)
        self.assertEqual(len(left), 18)
        for test_card in got_cards:
            self.assertEqual(test_card.suit, "Spades")

    def test_get_card_limit(self):
        """"""
        left, got_cards = tools.get_card(self.deck, "Spades", limit=1)

        self.assertEqual(len(got_cards), 1)
        self.assertEqual(len(left), 23)

    def test_get_list_full(self):
        """"""
        full_list = [
            "Ace of Spades",
            "9 of Diamonds",
            "Queen of Hearts",
            "King of Clubs",
        ]

        left, got_cards = tools.get_list(self.stack, full_list)

        self.get_list_helper(left, got_cards)

    def test_get_list_abbrev(self):
        """"""
        abbrev_list = ["AS", "9D", "QH", "KC"]

        left, got_cards = tools.get_list(self.stack, abbrev_list)

        self.get_list_helper(left, got_cards)

    def test_get_list_partial_value(self):
        """"""
        partial_list = ["Ace", "9", "Queen", "King"]

        left, got_cards = tools.get_list(self.stack, partial_list)

        self.get_list_helper(left, got_cards)

    def test_get_list_partial_suit(self):
        """"""
        partial_list = ["Spades", "Diamonds", "Hearts", "Clubs"]

        left, got_cards = tools.get_list(self.stack, partial_list)

        self.get_list_helper(left, got_cards)

    def test_get_list_mixed(self):
        """"""
        mixed_list = ["AS", "9 of Diamonds", "Hearts", "King"]

        left, got_cards = tools.get_list(self.stack, mixed_list)

        self.get_list_helper(left, got_cards)

    def test_get_list_limit(self):
        """"""
        left, got_cards = tools.get_list(self.stack, ["Spades"], limit=1)

        self.assertEqual(len(got_cards), 1)
