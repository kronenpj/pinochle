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
        self.reference_card = card.PinochleCard("Ace", "Spades")

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
        self.assertEqual(self.reference_card.value, "Ace")

    def test_suit(self):
        """"""
        self.assertEqual(self.reference_card.suit, "Spades")

    def test_abbrev(self):
        """"""
        self.assertEqual(self.reference_card.abbrev, "AS")

    def test_name(self):
        """"""
        self.assertEqual(self.reference_card.name, "Ace of Spades")

    def test_eq(self):
        """"""
        ace_spades = card.PinochleCard("Ace", "Spades")

        self.assertEqual(self.reference_card, ace_spades)

    def test_eq_func(self):
        """"""
        ace_spades = card.PinochleCard("Ace", "Spades")
        ten_hearts = card.PinochleCard("10", "Hearts")

        self.assertTrue(self.reference_card.eq(ace_spades))
        self.assertFalse(self.reference_card.eq(ten_hearts))

    def test_ge(self):
        """"""
        ace_spades = card.PinochleCard("Ace", "Spades")
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        self.assertGreaterEqual(self.reference_card, ace_spades)
        self.assertGreaterEqual(self.reference_card, nine_diamonds)
        self.assertGreaterEqual(ace_spades, nine_diamonds)

    def test_ge_func(self):
        """"""
        ace_spades = card.PinochleCard("Ace", "Spades")
        ace_clubs = card.PinochleCard("Ace", "Clubs")
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        self.assertFalse(self.reference_card.ge(5))
        self.assertTrue(self.reference_card.ge(ace_spades))
        self.assertTrue(self.reference_card.ge(ace_clubs))
        self.assertTrue(self.reference_card.ge(nine_diamonds))
        self.assertTrue(ace_clubs.ge(nine_diamonds))
        self.assertFalse(nine_diamonds.ge(ace_clubs))
        self.assertFalse(nine_diamonds.ge(self.reference_card))

    def test_gt(self):
        """"""
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        self.assertGreater(self.reference_card, nine_diamonds)

    def test_gt_func(self):
        """"""
        ace_spades = card.PinochleCard("Ace", "Spades")
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        self.assertTrue(self.reference_card.gt(nine_diamonds))
        self.assertFalse(self.reference_card.gt(ace_spades))
        self.assertFalse(nine_diamonds.gt(self.reference_card))

    def test_le(self):
        """"""
        ace_spades = card.PinochleCard("Ace", "Spades")
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        self.assertLessEqual(self.reference_card, ace_spades)
        self.assertLessEqual(nine_diamonds, ace_spades)

    def test_le_func(self):
        """"""
        ace_spades = card.PinochleCard("Ace", "Spades")
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        self.assertTrue(self.reference_card.le(ace_spades))
        self.assertFalse(self.reference_card.le(nine_diamonds))

    def test_lt(self):
        """"""
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        self.assertLess(nine_diamonds, self.reference_card)

    def test_lt_func(self):
        """"""
        ace_spades = card.PinochleCard("Ace", "Spades")
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        self.assertTrue(nine_diamonds.lt(self.reference_card))
        self.assertFalse(self.reference_card.lt(ace_spades))
        self.assertFalse(self.reference_card.lt(nine_diamonds))

    def test_ne(self):
        """"""
        nine_diamonds = card.PinochleCard("9", "Diamonds")
        ace_diamonds = card.PinochleCard("Ace", "Diamonds")
        ten_spades = card.PinochleCard("10", "Spades")

        self.assertNotEqual(self.reference_card, nine_diamonds)
        self.assertNotEqual(self.reference_card, ace_diamonds)
        self.assertNotEqual(self.reference_card, ten_spades)

    def test_ne_func(self):
        """"""
        nine_diamonds = card.PinochleCard("9", "Diamonds")

        self.assertTrue(self.reference_card.ne(nine_diamonds))
        self.assertFalse(nine_diamonds.ne(nine_diamonds))
