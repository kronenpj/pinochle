"""
Tests for the application module.
"""
from unittest import TestCase

from pinochle import pinochle_utils
from pinochle.pinochle_deck import PinochleDeck


class test_deck(TestCase):
    def test_pinochle_deck(self):
        """
        Simple test to make sure the generated deck is the right size, contains
        the appropriate collection and quantities of cards.
        """
        test_deck = pinochle_utils.create_deck()
        assert test_deck.size == 48
        assert test_deck.find_list(["2", "3", "4", "5", "6", "7", "8"]) == []
        for card in ["Ace", "10", "King", "Queen", "Jack", "9"]:
            self.assertEqual(
                len(test_deck.find(card)), 8, f"Incorrect number of {card}"
            )

    def test_hand_sizes_dealt(self):
        """
        Tests various combinations of pinochle players and kitty sizes.
        """
        cases = [
            {"p": 2, "k": 0, "s": 24},  # 48 cards for 2 players = 24 cards each
            {"p": 3, "k": 0, "s": 16},  # 48 / 3 = 16 cards each
            {"p": 3, "k": 3, "s": 15},  # 48 / 3 = 15 cards each + 3
            {"p": 4, "k": 0, "s": 12},  # 48 / 4 = 12 cards each
            {"p": 4, "k": 4, "s": 11},  # 48 / 4 = 11 cards each + 4
            {"p": 5, "k": 3, "s": 9},  # 48 / 5 = 9 cards each + 3
        ]
        for case in cases:
            players = case["p"]
            kitty_cards = case["k"]
            test_deck = pinochle_utils.create_deck()
            hands, kitty = pinochle_utils.deal_hands(
                deck=test_deck, players=players, kitty_cards=kitty_cards
            )
            self.assertEqual(len(hands), players, msg="Wrong number of players")
            self.assertEqual(
                len(kitty), kitty_cards, msg="Wrong number of cards in the kitty"
            )
            for hand in hands:
                self.assertEqual(
                    hand.size, case["s"], msg="Player's hand size incorrect"
                )

    def test_hand_forced_kitty(self):
        """
        Tests a specific combination of pinochle players and kitty sizes.
        """
        players = 5
        kitty_cards = 0
        test_deck = pinochle_utils.create_deck()
        hands, kitty = pinochle_utils.deal_hands(
            deck=test_deck, players=players, kitty_cards=kitty_cards
        )
        assert len(hands) == players
        assert len(kitty) == 3

    def test_uninitialized_deck(self):
        """
        Tests sorting a full deck.
        """
        hands, kitty = pinochle_utils.deal_hands()
        assert len(hands) == 4
        assert len(kitty) == 0

    def test_deck_sort(self):
        """
        Tests a specific combination of pinochle players and kitty sizes.
        """
        deck = PinochleDeck()
        deck.empty()
        deck = deck + pinochle_utils.sort_cards(pinochle_utils.create_deck())
        while deck.size > 0:
            one = deck.deal(1)
            two = deck.deal(1)
            self.assertEqual(one, two)

    def test_verify(self):
        """
        Tests a specific combination of pinochle players and kitty sizes.
        """
        hands, kitty = pinochle_utils.deal_hands()
        assert len(hands) == 4
        assert len(kitty) == 0
