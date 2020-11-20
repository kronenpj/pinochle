import pydealer

from . import const, pinochle_deck
from .log_decorator import log_decorator


# Broken here too # @log_decorator
def create_deck():
    built_deck = pinochle_deck.PinochleDeck()
    # Add a second set of cards.
    built_deck.build()

    built_deck.shuffle()
    return built_deck


# Broken here too # @log_decorator
def deal_hands(players=4, deck=None, kitty_cards=0):
    if deck is None:
        deck = create_deck()

    # Create empty hands
    hand = list()
    for index in range(0, players):
        hand.append(pinochle_deck.PinochleDeck())
        hand[index].empty()
    kitty = pinochle_deck.PinochleDeck()
    kitty.empty()

    # If the number of players isn't evenly divisible into the size of the
    # deck, force a number of kitty cards, if none are requested.
    if kitty_cards == 0:
        remainder = deck.size % players
        if remainder != 0:
            kitty_cards = remainder

    # Pull out random cards for the kitty, if requested
    if kitty_cards > 0:
        kitty += deck.deal(kitty_cards)
        deck.shuffle()

    # Deal remaining cards equally to each player, one at a time and
    while deck.size > 0:
        for index in range(0, players):
            hand[index] += deck.deal()

    return hand, kitty


@log_decorator
def build_cards(jokers=False, num_jokers=0):
    """
    Builds a list containing a single (half) pinochle deck of 24 Card instances. The
    cards are sorted according to ``DEFAULT_RANKS``.

    .. note:
        Adding jokers may break some functions & methods at the moment.

    :arg bool jokers:
        Whether or not to include jokers in the deck. - Ignored - Pinochle decks do not
        use Jokers.
    :arg int num_jokers:
        The number of jokers to include. - Ignored - Pinochle decks do not use Jokers.

    :returns:
        A list containing a single (half) pinochle deck of 24 Card instances.

    """
    new_deck = []

    new_deck += [
        pydealer.Card(value, suit) for value in const.VALUES for suit in const.SUITS
    ]

    return new_deck


@log_decorator
def sort_cards(cards, ranks=None):
    """
    Sorts a given list of cards, either by poker ranks, or big two ranks.

    :arg cards:
        The cards to sort.
    :arg dict ranks:
        The rank dict to reference for sorting. If ``None``, it will
        default to ``PINOCHLE_RANKS``.

    :returns:
        The sorted cards.

    """
    ranks = ranks or const.PINOCHLE_RANKS

    if ranks.get("suits"):
        cards = sorted(
            cards,
            key=lambda x: (ranks["suits"][x.suit], -ranks["values"][x.value])
            if x.suit != None
            else 0,
        )

    return cards
