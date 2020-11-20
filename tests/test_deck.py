"""
Tests for the application module.
"""
from unittest import TestCase

from pinochle import utils
from pinochle.deck import PinochleDeck


class test_deck(TestCase):
    def setUp(self):
        """"""
        self.deck = PinochleDeck(build=True)
        self.empty_deck = PinochleDeck(build=False)
        # pass

    def test_add(self):
        """"""
        self.empty_deck = self.empty_deck + self.deck

        self.assertEqual(self.empty_deck, self.deck)

    def test_build(self):
        """"""
        self.empty_deck.build()

        self.assertEqual(len(self.empty_deck.cards), 24)

    def test_deal(self):
        """"""
        card_names = [
            "Ace of Spades",
            "Ace of Hearts",
            "Ace of Clubs",
            "Ace of Diamonds",
        ]

        dealt_cards = self.deck.deal(4)

        for i, name in enumerate(card_names):
            self.assertEqual(dealt_cards[i].name, name)

    def test_deal_rebuild(self):
        """"""
        self.deck.rebuild = True

        dealt_cards = self.deck.deal(25)

        self.assertEqual(self.deck.size, 23)

    def test_repr(self):
        """"""
        result = repr(self.empty_deck)

        self.assertEqual(result, "PinochleDeck(cards=deque([]))")

    def test_deck(self):
        """
        Simple test to make sure the generated deck is the right size, contains
        the appropriate collection and quantities of cards. This is a half-pinochle
        deck. For a full deck, use populate_deck from utils.
        """
        assert self.deck.size == 24
        assert self.deck.find_list(["2", "3", "4", "5", "6", "7", "8"]) == []
        for card in ["Ace", "10", "King", "Queen", "Jack", "9"]:
            self.assertEqual(
                len(self.deck.find(card)), 4, f"Incorrect number of {card} cards."
            )

    def test_deck_sort(self):
        """
        Tests sorting a full deck.
        """
        deck = PinochleDeck(build=False)
        self.empty_deck += utils.sort_cards(utils.populate_deck())
        while deck.size > 0:
            one, two = deck.deal(2)
            self.assertEqual(one, two)

    def test_verify(self):
        """
        Tests a specific combination of pinochle players and kitty sizes.
        """
        hands, kitty = utils.deal_hands()
        assert len(hands) == 4
        assert len(kitty) == 0
