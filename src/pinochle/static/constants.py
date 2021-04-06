"""
Module to provide constants.
"""

CARD_URL = "/static/playingcards.svg"

# Intrinsic dimensions of the cards in the deck.
card_width = 170  # pylint: disable=invalid-name
card_height = 245  # pylint: disable=invalid-name

#                0      1        2           3        4       5
GAME_MODES = ["game", "bid", "bidfinal", "reveal", "meld", "trick"]

# These are a lot less dynamic than I thought they'd be.
DECK_CONFIG = {
    "player": {
        1: {"flippable": False, "movable": False, "show_face": True},  # Bid
        2: {"flippable": False, "movable": False, "show_face": True},  # Bidfinal
        3: {"flippable": False, "movable": False, "show_face": True},  # Reveal
        4: {"flippable": False, "movable": True, "show_face": True},  # Meld
        5: {"flippable": False, "movable": True, "show_face": True},  # Trick
    },
    "kitty": {
        1: {"flippable": False, "movable": False, "show_face": False},  # Bid (Kitty)
        2: {"flippable": False, "movable": False, "show_face": False},  # Bidfinal (Kitty)
        3: {"flippable": False, "movable": False, "show_face": False},  # Reveal (Kitty)
        4: {"flippable": False, "movable": False, "show_face": True},  # Meld (Meld)
        5: {"flippable": False, "movable": False, "show_face": True},  # Trick (Discard)
    },
    "meld": {
        1: {"flippable": False, "movable": False, "show_face": False},  # Bid (Kitty)
        2: {"flippable": False, "movable": False, "show_face": False},  # Bidfinal (Kitty)
        3: {"flippable": False, "movable": False, "show_face": False},  # Reveal (Kitty)
        4: {"flippable": False, "movable": False, "show_face": True},  # Meld (Meld)
        5: {"flippable": False, "movable": False, "show_face": True},  # Trick (Discard)
    },
    "trick": {
        1: {"flippable": False, "movable": False, "show_face": False},  # Bid (Kitty)
        2: {"flippable": False, "movable": False, "show_face": False},  # Bidfinal (Kitty)
        3: {"flippable": False, "movable": False, "show_face": False},  # Reveal (Kitty)
        4: {"flippable": False, "movable": False, "show_face": True},  # Meld (Meld)
        5: {"flippable": False, "movable": False, "show_face": True},  # Trick (Discard)
    },
}
