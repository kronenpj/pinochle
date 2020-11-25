"""
Tests for the application module.
"""
from unittest import TestCase

import pytest
from pinochle import card, deck, utils
from pinochle.exceptions import InvalidDeckError, InvalidSuitError


class TestUtils(TestCase):
    def test_populate_deck_util(self):
        """
        Simple test to make sure the generated deck is the right size, contains
        the appropriate collection and quantities of cards.
        """
        test_deck = utils.populate_deck()
        assert test_deck.size == 48
        assert test_deck.find_list(["2", "3", "4", "5", "6", "7", "8"]) == []
        for card in ["Ace", "10", "King", "Queen", "Jack", "9"]:
            self.assertEqual(
                len(test_deck.find(card)), 8, f"Incorrect number of {card} cards."
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
            test_deck = utils.populate_deck()
            hands, kitty = utils.deal_hands(
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
        test_deck = utils.populate_deck()
        hands, kitty = utils.deal_hands(
            deck=test_deck, players=players, kitty_cards=kitty_cards
        )
        assert len(hands) == players
        assert len(kitty) == 3

    def test_hand_uneven_players(self):
        """
        Tests a invalid combinations of pinochle players and kitty sizes.
        """
        players = 5
        kitty_cards = 1

        test_deck = utils.populate_deck()
        with pytest.raises(AssertionError):
            __, __ = utils.deal_hands(
                deck=test_deck, players=players, kitty_cards=kitty_cards
            )

    def test_uninitialized_deck(self):
        """
        Tests the default combination of pinochle players and kitty sizes.
        """
        hands, kitty = utils.deal_hands()
        assert len(hands) == 4
        assert len(kitty) == 0

    def test_trump_suit_exception(self):
        """
        Tests that an exception is raised as appropriate.
        """
        temp_deck = deck.PinochleDeck(build=True)
        with pytest.raises(InvalidSuitError):
            utils.set_trump(trump="NotASuit", hand=temp_deck)

    def test_trump_deck_exception(self):
        """
        Tests that an exception is raised as appropriate.
        """
        with pytest.raises(InvalidDeckError):
            utils.set_trump(trump="Spades", hand=5)
