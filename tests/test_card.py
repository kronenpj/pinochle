"""
This test exercises the ``PinochleCard`` class.

License: GPLv3
Derived from: https://github.com/Trebek/pydealer
Original author: Alex Crawford
Modernized and modified for Pinochle by Paul Kronenwetter
"""

# ===============================================================================
# card - Tests - PinochleCard
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

from pinochle import card


# ===============================================================================
# TestCard Class
# ===============================================================================


class TestCard(unittest.TestCase):
    def setUp(self):
        """"""
        self.test_card = card.PinochleCard("Ace", "Spades")

    def test_card_abbrev(self):
        """"""
        abbrev = card.card_abbrev("Ace", "Spades")

        self.assertEqual(abbrev, "AS")

    def test_card_name(self):
        """"""
        name = card.card_name("Ace", "Spades")

        self.assertEqual(name, "Ace of Spades")

    def test_value(self):
        """"""
        self.assertEqual(self.test_card.value, "Ace")

    def test_suit(self):
        """"""
        self.assertEqual(self.test_card.suit, "Spades")

    def test_abbrev(self):
        """"""
        self.assertEqual(self.test_card.abbrev, "AS")

    def test_name(self):
        """"""
        self.assertEqual(self.test_card.name, "Ace of Spades")

    def test_eq(self):
        """"""
        ace_spades = card.PinochleCard("Ace", "Spades")

        self.assertEqual(self.test_card, ace_spades)

    def test_eq_func(self):
        """"""
        ace_spades = card.PinochleCard("Ace", "Spades")

        result = self.test_card.eq(ace_spades)

        self.assertTrue(result)

    def test_ge(self):
        """"""
        ace_spades = card.PinochleCard("Ace", "Spades")
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        self.assertGreaterEqual(self.test_card, ace_spades)
        self.assertGreaterEqual(self.test_card, nine_diamonds)

    def test_ge_func(self):
        """"""
        ace_spades = card.PinochleCard("Ace", "Spades")
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        result_x = self.test_card.ge(ace_spades)
        result_y = self.test_card.ge(nine_diamonds)

        self.assertTrue(result_x)
        self.assertTrue(result_y)

    def test_gt(self):
        """"""
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        self.assertGreater(self.test_card, nine_diamonds)

    def test_gt_func(self):
        """"""
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        result = self.test_card.gt(nine_diamonds)

        self.assertTrue(result)

    def test_le(self):
        """"""
        ace_spades = card.PinochleCard("Ace", "Spades")
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        self.assertLessEqual(self.test_card, ace_spades)
        self.assertLessEqual(nine_diamonds, ace_spades)

    def test_le_func(self):
        """"""
        ace_spades = card.PinochleCard("Ace", "Spades")
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        result_x = self.test_card.le(ace_spades)
        result_y = self.test_card.le(nine_diamonds)

        self.assertTrue(result_x)
        self.assertFalse(result_y)

    def test_lt(self):
        """"""
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        self.assertLess(nine_diamonds, self.test_card)

    def test_lt_func(self):
        """"""
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        result = self.test_card.lt(nine_diamonds)

        self.assertFalse(result)

    def test_ne(self):
        """"""
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        self.assertNotEqual(self.test_card, nine_diamonds)

    def test_ne_func(self):
        """"""
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        result = self.test_card.ne(nine_diamonds)

        self.assertTrue(result)
