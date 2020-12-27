"""
This test exercises the ``PinochleCard`` class with tests specific to Pinochle
values such as 10 > King.

License: GPLv3
Derived from: https://github.com/Trebek/pydealer
Original author: Alex Crawford
Modernized and modified for Pinochle by Paul Kronenwetter
"""

# ===============================================================================
# Imports
# ===============================================================================

import unittest

from pinochle.cards import card


# ===============================================================================
# TestPinochleCard Class
# ===============================================================================


class TestPinochleCard(unittest.TestCase):
    def setUp(self):
        """"""
        self.ace_spades = card.PinochleCard("Ace", "Spades")
        self.ten_spades = card.PinochleCard("10", "Spades")
        self.king_spades = card.PinochleCard("King", "Spades")
        self.queen_spades = card.PinochleCard("Queen", "Spades")
        self.jack_spades = card.PinochleCard("Jack", "Spades")
        self.nine_spades = card.PinochleCard("9", "Spades")
        self.ace_hearts = card.PinochleCard("Ace", "Hearts")
        self.ace_clubs = card.PinochleCard("Ace", "Clubs")
        self.ace_diamonds = card.PinochleCard("Ace", "Diamonds")

    def test_face_value_ranking(self):
        """"""
        self.assertTrue(self.ace_spades.gt(self.ten_spades))
        self.assertTrue(self.ten_spades.gt(self.king_spades))
        self.assertTrue(self.king_spades.gt(self.queen_spades))
        self.assertTrue(self.queen_spades.gt(self.jack_spades))
        self.assertTrue(self.jack_spades.gt(self.nine_spades))

    def test_suit_ranking(self):
        """
        There's no reason this should be this way. However, it's handy for
        sorting.
        """
        self.assertTrue(self.ace_spades.gt(self.ace_hearts))
        self.assertTrue(self.ace_spades.gt(self.ace_diamonds))
        self.assertTrue(self.ace_spades.gt(self.ace_clubs))
        self.assertFalse(self.ace_hearts.gt(self.ace_spades))
        self.assertFalse(self.ace_diamonds.gt(self.ace_spades))
        self.assertFalse(self.ace_clubs.gt(self.ace_spades))
