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

from pinochle import const, pinochle_card, pinochle_deck, pinochle_stack, pinochle_tools

# ===============================================================================
# TestTools Class
# ===============================================================================


class TestTools(unittest.TestCase):
    def setUp(self):
        """"""
        self.ace_spades = pinochle_card.PinochleCard("Ace", "Spades")
        self.nine_diamonds = pinochle_card.PinochleCard("9", "Diamonds")
        self.queen_hearts = pinochle_card.PinochleCard("Queen", "Hearts")
        self.king_clubs = pinochle_card.PinochleCard("King", "Clubs")
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
        self.deck = pinochle_deck.PinochleDeck(build=True)
        self.stack = pinochle_stack.PinochleStack(cards=self.cards)
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
        cards = pinochle_tools.build_cards()

        self.assertEqual(list(self.deck.cards), cards)

    def test_check_sorted(self):
        """"""
        result = pinochle_tools.check_sorted(self.deck, ranks=const.PINOCHLE_RANKS)

        self.assertEqual(result, True)

    def test_check_term(self):
        """"""
        result = pinochle_tools.check_term(self.deck[0], "9 of Diamonds")

        self.assertEqual(result, True)

    def test_compare_stacks(self):
        """"""
        other_deck = pinochle_deck.PinochleDeck(build=True)

        result = pinochle_tools.compare_stacks(self.deck, other_deck)

        self.assertEqual(result, True)

    def test_find_card_abbrev(self):
        """"""
        found = pinochle_tools.find_card(self.deck, "AS")
        i = found[0]

        self.assertEqual(len(found), 1)
        self.assertEqual(self.deck[i].name, "Ace of Spades")

    def test_find_card_full(self):
        """"""
        found = pinochle_tools.find_card(self.deck, "Ace of Spades")
        i = found[0]

        self.assertEqual(len(found), 1)
        self.assertEqual(self.deck[i].name, "Ace of Spades")

    def test_find_card_partial_value(self):
        """"""
        found = pinochle_tools.find_card(self.deck, "Ace")

        self.assertEqual(len(found), 4)
        for i in found:
            self.assertEqual(self.deck[i].value, "Ace")

    def test_find_card_partial_suit(self):
        """"""
        found = pinochle_tools.find_card(self.deck, "Spades")

        self.assertEqual(len(found), 6)
        for i in found:
            self.assertEqual(self.deck[i].suit, "Spades")

    def test_find_card_limit(self):
        """"""
        found = pinochle_tools.find_card(self.deck, "Spades", limit=1)

        self.assertEqual(len(found), 1)

    def test_find_list_full(self):
        """"""
        full_list = [
            "Ace of Spades",
            "9 of Diamonds",
            "Queen of Hearts",
            "King of Clubs",
        ]

        found = pinochle_tools.find_list(self.stack, full_list)

        self.find_list_helper(self.stack, found)

    def test_find_list_abbrev(self):
        """"""
        abbrev_list = ["AS", "9D", "QH", "KC"]

        found = pinochle_tools.find_list(self.stack, abbrev_list)

        self.find_list_helper(self.stack, found)

    def test_find_list_partial_value(self):
        """"""
        partial_list = ["Ace", "9", "Queen", "King"]

        found = pinochle_tools.find_list(self.stack, partial_list)

        self.find_list_helper(self.stack, found)

    def test_find_list_partial_suit(self):
        """"""
        partial_list = ["Spades", "Diamonds", "Hearts", "Clubs"]

        found = pinochle_tools.find_list(self.stack, partial_list)

        self.find_list_helper(self.stack, found)

    def test_find_list_mixed(self):
        """"""
        mixed_list = ["AS", "9 of Diamonds", "Hearts", "K"]

        found = pinochle_tools.find_list(self.stack, mixed_list)

        self.find_list_helper(self.stack, found)

    def test_find_list_limit(self):
        """"""
        found = pinochle_tools.find_list(self.stack, ["Spades"], limit=1)

        self.assertEqual(len(found), 1)

    def test_get_card_abbrev(self):
        """"""
        left, got_cards = pinochle_tools.get_card(self.deck, "AS")
        card = got_cards[0]

        self.assertEqual(len(got_cards), 1)
        self.assertEqual(len(left), 23)
        self.assertEqual(card.name, "Ace of Spades")

    def test_get_card_full(self):
        """"""
        left, got_cards = pinochle_tools.get_card(self.deck, "Ace of Spades")
        card = got_cards[0]

        self.assertEqual(len(got_cards), 1)
        self.assertEqual(len(left), 23)
        self.assertEqual(card.name, "Ace of Spades")

    def test_get_card_partial_value(self):
        """"""
        left, got_cards = pinochle_tools.get_card(self.deck, "Ace")

        self.assertEqual(len(got_cards), 4)
        self.assertEqual(len(left), 20)
        for card in got_cards:
            self.assertEqual(card.value, "Ace")

    def test_get_card_partial_suit(self):
        """"""
        left, got_cards = pinochle_tools.get_card(self.deck, "Spades")

        self.assertEqual(len(got_cards), 6)
        self.assertEqual(len(left), 18)
        for card in got_cards:
            self.assertEqual(card.suit, "Spades")

    def test_get_card_limit(self):
        """"""
        left, got_cards = pinochle_tools.get_card(self.deck, "Spades", limit=1)

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

        left, got_cards = pinochle_tools.get_list(self.stack, full_list)

        self.get_list_helper(left, got_cards)

    def test_get_list_abbrev(self):
        """"""
        abbrev_list = ["AS", "9D", "QH", "KC"]

        left, got_cards = pinochle_tools.get_list(self.stack, abbrev_list)

        self.get_list_helper(left, got_cards)

    def test_get_list_partial_value(self):
        """"""
        partial_list = ["Ace", "9", "Queen", "King"]

        left, got_cards = pinochle_tools.get_list(self.stack, partial_list)

        self.get_list_helper(left, got_cards)

    def test_get_list_partial_suit(self):
        """"""
        partial_list = ["Spades", "Diamonds", "Hearts", "Clubs"]

        left, got_cards = pinochle_tools.get_list(self.stack, partial_list)

        self.get_list_helper(left, got_cards)

    def test_get_list_mixed(self):
        """"""
        mixed_list = ["AS", "9 of Diamonds", "Hearts", "King"]

        left, got_cards = pinochle_tools.get_list(self.stack, mixed_list)

        self.get_list_helper(left, got_cards)

    def test_get_list_limit(self):
        """"""
        left, got_cards = pinochle_tools.get_list(self.stack, ["Spades"], limit=1)

        self.assertEqual(len(got_cards), 1)


# if __name__ == '__main__':
#     unittest.main()
