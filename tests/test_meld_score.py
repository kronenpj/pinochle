"""
Tests for the meld scoring module.

License: GPLv3
"""
import unittest

from pinochle import card, deck, score_meld, utils


class TestMeldScoring(unittest.TestCase):
    def test_no_trump(self):
        """"""
        temp_deck = deck.PinochleDeck(build=True)

        assert score_meld.score(temp_deck) == 0

    def test_nines(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("9", "Spades")]
        temp_deck += [card.PinochleCard("10", "Hearts")]
        temp_deck += [card.PinochleCard("King", "Hearts")]
        temp_deck += [card.PinochleCard("King", "Diamonds")]
        temp_deck += [card.PinochleCard("9", "Spades")]
        temp_deck += [card.PinochleCard("Jack", "Clubs")]

        assert score_meld._nines(utils.set_trump("Clubs", temp_deck)) == 0
        assert score_meld._nines(utils.set_trump("Diamonds", temp_deck)) == 0
        assert score_meld._nines(utils.set_trump("Hearts", temp_deck)) == 0
        assert score_meld._nines(utils.set_trump("Spades", temp_deck)) == 2

    def test_marriages(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("Jack", "Spades")]
        temp_deck += [card.PinochleCard("10", "Hearts")]
        temp_deck += [card.PinochleCard("King", "Hearts")]
        temp_deck += [card.PinochleCard("Queen", "Hearts")]
        temp_deck += [card.PinochleCard("10", "Spades")]
        temp_deck += [card.PinochleCard("Queen", "Clubs")]

        assert score_meld._marriages(utils.set_trump("Clubs", temp_deck)) == 2
        assert score_meld._marriages(utils.set_trump("Diamonds", temp_deck)) == 2
        assert score_meld._marriages(utils.set_trump("Hearts", temp_deck)) == 4
        assert score_meld._marriages(utils.set_trump("Spades", temp_deck)) == 2

    def test_jacks(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("Jack", "Spades")]
        temp_deck += [card.PinochleCard("Jack", "Hearts")]
        temp_deck += [card.PinochleCard("King", "Hearts")]
        temp_deck += [card.PinochleCard("10", "Hearts")]
        temp_deck += [card.PinochleCard("Jack", "Diamonds")]
        temp_deck += [card.PinochleCard("Jack", "Clubs")]

        assert score_meld._jacks(utils.set_trump("Clubs", temp_deck)) == 4
        assert score_meld._jacks(utils.set_trump("Diamonds", temp_deck)) == 4
        assert score_meld._jacks(utils.set_trump("Hearts", temp_deck)) == 4
        assert score_meld._jacks(utils.set_trump("Spades", temp_deck)) == 4

    def test_queens(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("Queen", "Spades")]
        temp_deck += [card.PinochleCard("Jack", "Hearts")]
        temp_deck += [card.PinochleCard("Queen", "Hearts")]
        temp_deck += [card.PinochleCard("10", "Hearts")]
        temp_deck += [card.PinochleCard("Queen", "Diamonds")]
        temp_deck += [card.PinochleCard("Queen", "Clubs")]

        assert score_meld._queens(utils.set_trump("Clubs", temp_deck)) == 6
        assert score_meld._queens(utils.set_trump("Diamonds", temp_deck)) == 6
        assert score_meld._queens(utils.set_trump("Hearts", temp_deck)) == 6
        assert score_meld._queens(utils.set_trump("Spades", temp_deck)) == 6

    def test_kings(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("King", "Spades")]
        temp_deck += [card.PinochleCard("King", "Hearts")]
        temp_deck += [card.PinochleCard("King", "Hearts")]
        temp_deck += [card.PinochleCard("10", "Hearts")]
        temp_deck += [card.PinochleCard("King", "Diamonds")]
        temp_deck += [card.PinochleCard("King", "Clubs")]

        assert score_meld._kings(utils.set_trump("Clubs", temp_deck)) == 8
        assert score_meld._kings(utils.set_trump("Diamonds", temp_deck)) == 8
        assert score_meld._kings(utils.set_trump("Hearts", temp_deck)) == 8
        assert score_meld._kings(utils.set_trump("Spades", temp_deck)) == 8

    def test_aces(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("Ace", "Spades")]
        temp_deck += [card.PinochleCard("Jack", "Hearts")]
        temp_deck += [card.PinochleCard("Queen", "Hearts")]
        temp_deck += [card.PinochleCard("Ace", "Hearts")]
        temp_deck += [card.PinochleCard("Ace", "Diamonds")]
        temp_deck += [card.PinochleCard("Ace", "Clubs")]

        assert score_meld._aces(utils.set_trump("Clubs", temp_deck)) == 10
        assert score_meld._aces(utils.set_trump("Diamonds", temp_deck)) == 10
        assert score_meld._aces(utils.set_trump("Hearts", temp_deck)) == 10
        assert score_meld._aces(utils.set_trump("Spades", temp_deck)) == 10

        temp_deck += temp_deck
        assert score_meld._aces(utils.set_trump("Clubs", temp_deck)) == 100
        assert score_meld._aces(utils.set_trump("Diamonds", temp_deck)) == 100
        assert score_meld._aces(utils.set_trump("Hearts", temp_deck)) == 100
        assert score_meld._aces(utils.set_trump("Spades", temp_deck)) == 100

    def test_pinochle(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("Ace", "Spades")]
        temp_deck += [card.PinochleCard("Jack", "Diamonds")]
        temp_deck += [card.PinochleCard("Queen", "Spades")]
        temp_deck += [card.PinochleCard("Ace", "Hearts")]
        temp_deck += [card.PinochleCard("Ace", "Diamonds")]
        temp_deck += [card.PinochleCard("Ace", "Clubs")]

        assert score_meld._pinochle(utils.set_trump("Clubs", temp_deck)) == 4
        assert score_meld._pinochle(utils.set_trump("Diamonds", temp_deck)) == 4
        assert score_meld._pinochle(utils.set_trump("Hearts", temp_deck)) == 4
        assert score_meld._pinochle(utils.set_trump("Spades", temp_deck)) == 4

        temp_deck += temp_deck
        assert score_meld._pinochle(utils.set_trump("Clubs", temp_deck)) == 35
        assert score_meld._pinochle(utils.set_trump("Diamonds", temp_deck)) == 35
        assert score_meld._pinochle(utils.set_trump("Hearts", temp_deck)) == 35
        assert score_meld._pinochle(utils.set_trump("Spades", temp_deck)) == 35

    def test_run(self):
        """"""
        temp_deck = deck.PinochleDeck(build=False)
        temp_deck += [card.PinochleCard("Ace",  "Hearts")]
        temp_deck += [card.PinochleCard("Jack", "Hearts")]
        temp_deck += [card.PinochleCard("Queen","Hearts")]
        temp_deck += [card.PinochleCard("10",  "Hearts")]
        temp_deck += [card.PinochleCard("King",  "Hearts")]
        temp_deck += [card.PinochleCard("10",  "Clubs")]

        assert score_meld._run(utils.set_trump("Clubs", temp_deck)) == 0
        assert score_meld._run(utils.set_trump("Diamonds", temp_deck)) == 0
        assert score_meld._run(utils.set_trump("Hearts", temp_deck)) == 11
        assert score_meld._run(utils.set_trump("Spades", temp_deck)) == 0

        assert score_meld.score(utils.set_trump("Clubs", temp_deck)) == 2
        assert score_meld.score(utils.set_trump("Diamonds", temp_deck)) == 2
        assert score_meld.score(utils.set_trump("Hearts", temp_deck)) == 15
        assert score_meld.score(utils.set_trump("Spades", temp_deck)) == 2


    def test_score_deck(self):
        """"""
        temp_deck = deck.PinochleDeck(build=True)

        assert score_meld._run(utils.set_trump("Clubs", temp_deck)) == 11
        assert score_meld._run(utils.set_trump("Diamonds", temp_deck)) == 11
        assert score_meld._run(utils.set_trump("Hearts", temp_deck)) == 11
        assert score_meld._run(utils.set_trump("Spades", temp_deck)) == 11

        assert score_meld.score(utils.set_trump("Clubs", temp_deck)) == 54
        assert score_meld.score(utils.set_trump("Diamonds", temp_deck)) == 54
        assert score_meld.score(utils.set_trump("Hearts", temp_deck)) == 54
        assert score_meld.score(utils.set_trump("Spades", temp_deck)) == 54
