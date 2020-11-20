# ===============================================================================
# Card Data
# ===============================================================================

SUITS = ["Diamonds", "Clubs", "Hearts", "Spades"]
VALUES = ["9", "10", "Jack", "Queen", "King", "Ace"]

# ===============================================================================
# Card Rank Dicts
# ===============================================================================
PINOCHLE_RANKS = {
    "suits": {"Spades": 4, "Hearts": 3, "Clubs": 2, "Diamonds": 1},
    "values": {
        "Ace": 6,
        "10": 5,
        "King": 4,
        "Queen": 3,
        "Jack": 2,
        "9": 1,
    },
}

DEFAULT_RANKS = PINOCHLE_RANKS

# ===============================================================================
# Misc.
# ===============================================================================

# Stack/Deck ends.
TOP = "top"
BOTTOM = "bottom"
