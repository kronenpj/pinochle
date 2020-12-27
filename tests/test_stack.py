"""
This test exercises the ``PinochleStack`` class.

License: GPLv3
Derived from: https://github.com/Trebek/pydealer
Original author: Alex Crawford
Modernized and modified for Pinochle by Paul Kronenwetter
"""

# ===============================================================================
# stack - Tests - Stack
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

from pinochle.log_decorator import log_decorator
from pinochle.cards import card, stack, tools
from pinochle.cards.const import BOTTOM

# ===============================================================================
# TestStack Class
# ===============================================================================


class TestStack(unittest.TestCase):
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
        self.stack = stack.PinochleStack()
        self.full_stack = stack.PinochleStack(cards=tools.build_cards())
        self.small_stack = stack.PinochleStack(cards=self.cards)

    def find_list_helper(self, stack, found):
        """"""
        self.assertEqual(len(found), 4)

        for i, name in enumerate(self.names):
            self.assertEqual(stack[found[i]].name, name)

    def get_list_helper(self, found):
        """"""
        self.assertEqual(len(found), 4)

        for i, name in enumerate(self.names):
            self.assertEqual(found[i].name, name)

    def test_add_top(self):
        """"""
        self.stack.add(self.nine_diamonds)
        self.assertIs(self.stack[-1], self.nine_diamonds)

    def test_add_bottom(self):
        """"""
        self.stack.add(self.ace_spades, BOTTOM)
        self.assertIs(self.stack[0], self.ace_spades)

    def test_add_plus_eq(self):
        """"""
        self.stack += [self.ace_spades]
        self.assertIs(self.stack[-1], self.ace_spades)

    def test_contains(self):
        """"""
        self.stack.add(self.ace_spades)
        result = self.ace_spades in self.stack
        self.assertTrue(result)

    def test_deal_single(self):
        """"""
        cards = self.full_stack.deal()

        self.assertEqual(len(cards), 1)
        self.assertIsInstance(cards[0], card.PinochleCard)

    def test_deal_multiple(self):
        """"""
        cards = self.full_stack.deal(7)

        self.assertEqual(len(cards), 7)
        self.assertIsInstance(cards[0], card.PinochleCard)

    def test_del_item(self):
        """"""
        test_card = self.full_stack[0]
        del self.full_stack[0]
        result = test_card in self.full_stack

        self.assertFalse(result)

    def test_empty(self):
        """"""
        # This wouldn't be needed if hammett executed the setup routine.
        self.full_stack = stack.PinochleStack(cards=tools.build_cards())

        cards = self.full_stack.empty(return_cards=True)

        self.assertEqual(len(cards), 24)
        self.assertEqual(len(self.full_stack), 0)

    def test_eq(self):
        """"""
        # This wouldn't be needed if hammett executed the setup routine.
        self.full_stack = stack.PinochleStack(cards=tools.build_cards())

        other_stack = stack.PinochleStack(cards=tools.build_cards())

        result = self.full_stack == other_stack

        self.assertTrue(result)

    def test_find_abbrev(self):
        """"""
        found = self.full_stack.find("AS")
        i = found[0]

        self.assertEqual(len(found), 1)
        self.assertEqual(self.full_stack[i].name, "Ace of Spades")

    def test_find_full(self):
        """"""
        found = self.full_stack.find("Ace of Spades")
        i = found[0]

        self.assertEqual(len(found), 1)
        self.assertEqual(self.full_stack[i].name, "Ace of Spades")

    def test_find_partial_value(self):
        """"""
        found = self.full_stack.find("Ace")

        self.assertEqual(len(found), 4)
        for i in found:
            self.assertEqual(self.full_stack[i].value, "Ace")

    def test_find_partial_suit(self):
        """"""
        found = self.full_stack.find("Spades")

        self.assertEqual(len(found), 6)
        for i in found:
            self.assertEqual(self.full_stack[i].suit, "Spades")

    def test_find_limit(self):
        """"""
        found = self.full_stack.find("Spades", limit=1)

        self.assertEqual(len(found), 1)

    def test_find_list_full(self):
        """"""
        full_list = [
            "Ace of Spades",
            "9 of Diamonds",
            "Queen of Hearts",
            "King of Clubs",
        ]

        found = self.small_stack.find_list(full_list)

        self.find_list_helper(self.small_stack, found)

    def test_find_list_abbrev(self):
        """"""
        abbrev_list = ["AS", "9D", "QH", "KC"]

        found = self.small_stack.find_list(abbrev_list)

        self.find_list_helper(self.small_stack, found)

    def test_find_list_partial_value(self):
        """"""
        partial_list = ["Ace", "9", "Queen", "King"]

        found = self.small_stack.find_list(partial_list)

        self.find_list_helper(self.small_stack, found)

    def test_find_list_partial_suit(self):
        """"""
        partial_list = ["Spades", "Diamonds", "Hearts", "Clubs"]

        found = self.small_stack.find_list(partial_list)

        self.find_list_helper(self.small_stack, found)

    def test_find_list_mixed(self):
        """"""
        mixed_list = ["AS", "9 of Diamonds", "Hearts", "King"]

        found = self.small_stack.find_list(mixed_list)

        self.find_list_helper(self.small_stack, found)

    def test_find_list_limit(self):
        """"""
        found = self.full_stack.find_list(["Spades"], limit=1)

        self.assertEqual(len(found), 1)

    def test_get_abbrev(self):
        """"""
        found = self.full_stack.get("AS")
        test_card = found[0]

        self.assertEqual(len(found), 1)
        self.assertEqual(test_card.name, "Ace of Spades")

    def test_get_full(self):
        """"""
        # This wouldn't be needed if hammett executed the setup routine.
        self.full_stack = stack.PinochleStack(cards=tools.build_cards())

        found = self.full_stack.get("Ace of Spades")
        test_card = found[0]

        self.assertEqual(len(found), 1)
        self.assertEqual(test_card.name, "Ace of Spades")

    def test_get_partial_value(self):
        """"""
        # This wouldn't be needed if hammett executed the setup routine.
        self.full_stack = stack.PinochleStack(cards=tools.build_cards())

        found = self.full_stack.get("Ace")

        self.assertEqual(len(found), 4)
        for test_card in found:
            self.assertEqual(test_card.value, "Ace")

    def test_get_partial_suit(self):
        """"""
        # This wouldn't be needed if hammett executed the setup routine.
        self.full_stack = stack.PinochleStack(cards=tools.build_cards())

        found = self.full_stack.get("Spades")

        self.assertEqual(len(found), 6)
        for test_card in found:
            self.assertEqual(test_card.suit, "Spades")

    def test_get_limit(self):
        """"""
        found = self.full_stack.get("Spades", limit=1)

        self.assertEqual(len(found), 1)

    def test_get_list_full(self):
        """"""
        full_list = [
            "Ace of Spades",
            "9 of Diamonds",
            "Queen of Hearts",
            "King of Clubs",
        ]

        # This wouldn't be needed if hammett executed the setup routine.
        self.small_stack = stack.PinochleStack(cards=self.cards)

        found = self.small_stack.get_list(full_list)

        self.get_list_helper(found)

    def test_get_list_abbrev(self):
        """"""
        abbrev_list = ["AS", "9D", "QH", "KC"]

        found = self.small_stack.get_list(abbrev_list)

        self.get_list_helper(found)

    def test_get_list_partial_value(self):
        """"""
        # This wouldn't be needed if hammett executed the setup routine.
        self.small_stack = stack.PinochleStack(cards=self.cards)

        partial_list = ["Ace", "9", "Queen", "King"]

        found = self.small_stack.get_list(partial_list)

        self.get_list_helper(found)

    def test_get_list_partial_suit(self):
        """"""
        # This wouldn't be needed if hammett executed the setup routine.
        self.small_stack = stack.PinochleStack(cards=self.cards)

        partial_list = ["Spades", "Diamonds", "Hearts", "Clubs"]

        found = self.small_stack.get_list(partial_list)

        self.get_list_helper(found)

    def test_get_list_mixed(self):
        """"""
        # This wouldn't be needed if hammett executed the setup routine.
        self.small_stack = stack.PinochleStack(cards=self.cards)

        mixed_list = ["AS", "9 of Diamonds", "Hearts", "King"]

        found = self.small_stack.get_list(mixed_list)

        self.get_list_helper(found)

    def test_get_list_limit(self):
        """"""
        found = self.full_stack.get_list(["Spades"], limit=1)

        self.assertEqual(len(found), 1)

    def test_getitem(self):
        """"""
        test_card = self.full_stack[0]

        self.assertIsInstance(test_card, card.PinochleCard)

        test_card = self.full_stack[-1]

        self.assertIsInstance(test_card, card.PinochleCard)

    def test_insert(self):
        """"""
        self.full_stack.insert(self.ace_spades, 1)

        self.assertIs(self.full_stack[1], self.ace_spades)

    def test_insert_list(self):
        """"""
        self.full_stack.insert_list(self.cards, 1)

        stack_slice = self.full_stack[1:5]

        self.assertEqual(stack_slice, self.cards)

    def test_iter(self):
        """"""
        for test_card in self.full_stack:
            self.assertIsInstance(test_card, card.PinochleCard)

    def test_len(self):
        """"""
        # This wouldn't be needed if hammett executed the setup routine.
        self.full_stack = stack.PinochleStack(cards=tools.build_cards())

        result = len(self.full_stack)

        self.assertIs(result, 24)

    def test_ne(self):
        """"""
        result = self.full_stack != self.stack

        self.assertTrue(result)

    def test_open_cards(self):
        """"""
        indices = [0, 1, 2, 3]
        self.stack.open_cards("tests/cards.txt")

        self.find_list_helper(self.stack, indices)

    def test_random_card(self):
        """"""
        test_card = self.full_stack.random_card()

        self.assertIsInstance(test_card, card.PinochleCard)

    def test_repr(self):
        """"""
        # This wouldn't be needed if hammett executed the setup routine.
        self.stack = stack.PinochleStack()

        result = repr(self.stack)

        self.assertEqual(result, "PinochleStack(cards=deque([]))")

    def test_reverse(self):
        """"""
        cards_reversed_x = list(self.small_stack.cards)[::-1]

        self.small_stack.reverse()
        cards_reversed_y = list(self.small_stack.cards)

        self.assertEqual(cards_reversed_x, cards_reversed_y)

    def test_save_cards(self):
        """"""
        # This wouldn't be needed if hammett executed the setup routine.
        self.small_stack = stack.PinochleStack(cards=self.cards)

        names = ["Ace Spades\n", "9 Diamonds\n", "Queen Hearts\n", "King Clubs"]

        self.small_stack.save_cards("tests/cards-save.txt")

        with open("tests/cards-save.txt", "r") as cards_save:
            lines = cards_save.readlines()
            for i, name in enumerate(names):
                self.assertEqual(lines[i], name)

    def test_set_cards(self):
        """"""
        self.stack.set_cards(self.cards)

        self.assertEqual(list(self.stack.cards), self.cards)

    def test_setitem(self):
        """"""
        self.full_stack[0] = self.ace_spades

        self.assertIs(self.full_stack[0], self.ace_spades)

    def test_shuffle(self):
        """"""
        cards_before = list(self.full_stack.cards)
        self.full_stack.shuffle()
        cards_after = list(self.full_stack.cards)

        self.assertNotEqual(cards_before, cards_after)

    def test_size(self):
        """"""
        self.assertEqual(self.full_stack.size, 24)

    def test_sort(self):
        """"""
        ordered = [
            self.nine_diamonds,
            self.queen_hearts,
            self.king_clubs,
            self.ace_spades,
        ]

        self.small_stack.sort()

        self.assertEqual(list(self.small_stack.cards), ordered)

    def test_split(self):
        """"""
        split1, split2 = self.small_stack.split()

        self.assertEqual(list(split1.cards), self.small_stack[0:2])
        self.assertEqual(list(split2.cards), self.small_stack[2::])

    def test_str(self):
        """"""
        # This wouldn't be needed if hammett executed the setup routine.
        self.full_stack = stack.PinochleStack(cards=tools.build_cards())

        result = str(self.full_stack[0])

        self.assertEqual(result, "9 of Diamonds")
