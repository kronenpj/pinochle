"""
Tests for the application module.
"""
from unittest import TestCase

from pinochle import card, const, deck, score_tricks, utils


class test_trick_score(TestCase):
    def test_1(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("9", "Spades")]
        temp_deck += [card.PinochleCard("10", "Hearts")]
        temp_deck += [card.PinochleCard("King", "Hearts")]
        temp_deck += [card.PinochleCard("King", "Diamonds")]
        temp_deck += [card.PinochleCard("9", "Spades")]
        temp_deck += [card.PinochleCard("Jack", "Clubs")]

        assert score_tricks.score(temp_deck) == 3

    def test_2(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("Jack", "Spades")]
        temp_deck += [card.PinochleCard("10", "Hearts")]
        temp_deck += [card.PinochleCard("King", "Hearts")]
        temp_deck += [card.PinochleCard("Queen", "Hearts")]
        temp_deck += [card.PinochleCard("10", "Spades")]
        temp_deck += [card.PinochleCard("Queen", "Clubs")]

        assert score_tricks.score(temp_deck) == 3

    def test_3(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("Jack", "Spades")]
        temp_deck += [card.PinochleCard("Jack", "Hearts")]
        temp_deck += [card.PinochleCard("King", "Hearts")]
        temp_deck += [card.PinochleCard("10", "Hearts")]
        temp_deck += [card.PinochleCard("Jack", "Diamonds")]
        temp_deck += [card.PinochleCard("Jack", "Clubs")]

        assert score_tricks.score(temp_deck) == 2

    def test_4(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("Queen", "Spades")]
        temp_deck += [card.PinochleCard("Jack", "Hearts")]
        temp_deck += [card.PinochleCard("Queen", "Hearts")]
        temp_deck += [card.PinochleCard("10", "Hearts")]
        temp_deck += [card.PinochleCard("Queen", "Diamonds")]
        temp_deck += [card.PinochleCard("Queen", "Clubs")]

        assert score_tricks.score(temp_deck) == 1

    def test_5(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("King", "Spades")]
        temp_deck += [card.PinochleCard("King", "Hearts")]
        temp_deck += [card.PinochleCard("King", "Hearts")]
        temp_deck += [card.PinochleCard("10", "Hearts")]
        temp_deck += [card.PinochleCard("King", "Diamonds")]
        temp_deck += [card.PinochleCard("King", "Clubs")]

        assert score_tricks.score(temp_deck) == 6

    def test_6(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("Ace", "Spades")]
        temp_deck += [card.PinochleCard("Jack", "Hearts")]
        temp_deck += [card.PinochleCard("Queen", "Hearts")]
        temp_deck += [card.PinochleCard("Ace", "Hearts")]
        temp_deck += [card.PinochleCard("Ace", "Diamonds")]
        temp_deck += [card.PinochleCard("Ace", "Clubs")]

        assert score_tricks.score(temp_deck) == 4

    def test_7(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("Ace", "Spades")]
        temp_deck += [card.PinochleCard("Jack", "Diamonds")]
        temp_deck += [card.PinochleCard("Queen", "Spades")]
        temp_deck += [card.PinochleCard("Ace", "Hearts")]
        temp_deck += [card.PinochleCard("Ace", "Diamonds")]
        temp_deck += [card.PinochleCard("Ace", "Clubs")]

        assert score_tricks.score(temp_deck) == 4

    def test_8(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("Ace", "Hearts")]
        temp_deck += [card.PinochleCard("Jack", "Hearts")]
        temp_deck += [card.PinochleCard("Queen", "Hearts")]
        temp_deck += [card.PinochleCard("10", "Hearts")]
        temp_deck += [card.PinochleCard("King", "Hearts")]
        temp_deck += [card.PinochleCard("10", "Clubs")]

        assert score_tricks.score(temp_deck) == 4

    def test_score_deck(self):
        """"""
        temp_deck = deck.PinochleDeck(build=True)

        assert score_tricks.score(temp_deck) == 12
