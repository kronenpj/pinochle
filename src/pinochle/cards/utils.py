"""
Utilities to work with a deck of Pinochle cards.

License: GPLv3
Inspired by: https://github.com/Trebek/pydealer
Modernized and modified for Pinochle by Paul Kronenwetter
"""

from copy import deepcopy
from typing import List

from .. import score_meld, score_tricks
from ..exceptions import InvalidDeckError, InvalidSuitError
from ..log_decorator import log_decorator
from ..models.hand import Hand
from ..models.player import Player
from . import const
from .card import PinochleCard
from .deck import PinochleDeck


@log_decorator
def populate_deck():
    new_deck = PinochleDeck()
    # Add a deck of cards.
    new_deck.build()
    # Add a second set of cards.
    new_deck.build()

    new_deck.shuffle()
    return new_deck


@log_decorator
def deal_hands(
    deck: PinochleDeck = None, players=4, kitty_cards=0
) -> (List[PinochleDeck], PinochleDeck):
    if deck is None:
        deck = populate_deck()

    # Create empty hands
    hand = [None] * players
    for index in range(players):
        hand[index] = PinochleDeck(
            gameid=deck.gameid,
            rebuild=deck.rebuild,
            re_shuffle=deck.re_shuffle,
            ranks=deck.ranks,
            decks_used=deck.decks_used,
            build=False,
        )
    kitty = PinochleDeck(
        gameid=deck.gameid,
        rebuild=deck.rebuild,
        re_shuffle=deck.re_shuffle,
        ranks=deck.ranks,
        decks_used=deck.decks_used,
        build=False,
    )

    # If the number of players isn't evenly divisible into the size of the
    # deck, force a number of kitty cards, if none are requested.
    if kitty_cards == 0:
        remainder = deck.size % players
        if remainder != 0:
            kitty_cards = remainder

    # Make sure everyone will receive the same number of cards.
    assert (deck.size - kitty_cards) % players == 0

    # Pull out random cards for the kitty, if requested
    if kitty_cards > 0:
        kitty += deck.deal(kitty_cards)
        deck.shuffle()

    # Deal remaining cards equally to each player, one at a time
    while deck.size > 0:
        for index in range(players):
            hand[index] += deck.deal()

    # Make sure everyone has the same size hand
    for index in range(0, players - 1):
        assert hand[index].size == hand[index + 1].size

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
        PinochleCard(value, suit) for value in const.VALUES for suit in const.SUITS
    ]

    return new_deck


@log_decorator
def sort_cards(cards, ranks=None):  # pragma: no cover
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
            key=lambda x: (-ranks["suits"][x.suit], -ranks["values"][x.value])
            if x.suit is not None
            else 0,
        )

    return cards


@log_decorator
def set_trump(trump="", f_deck=PinochleDeck()) -> PinochleDeck:
    """
    Set trump for the supplied hand and return a new deck instance.

    :param trump: String containing suit to be made trump, defaults to ""
    :type trump: str, optional
    :param f_deck: Deck of cards to process, defaults to PinochleDeck()
    :type f_deck: PinochleDeck, optional
    :raises InvalidSuitError: [description]
    :raises InvalidDeckError: [description]
    :return: PinochleDeck instance with the suit weight adjusted.
    :rtype: PinochleDeck
    """
    if trump not in const.SUITS:
        raise InvalidSuitError("%s is not a valid suit." % str(trump))
    if not isinstance(f_deck, PinochleDeck):
        raise InvalidDeckError(
            "Supplied deck (hand) is not an instance of PinochleDeck."
        )

    newhand = deepcopy(f_deck)
    newhand.ranks["suits"][trump] = const.TRUMP_VALUE
    # print(newhand.ranks)

    return newhand


@log_decorator
def deck_list_summary(
    hands: List[PinochleDeck], players: int, kitty: PinochleDeck = None
) -> str:  # pragma: no cover
    output = ""

    for index in range(players):
        output += " Player %1d%17s" % (index, "")
    output += "\n"
    for line in range(hands[0].size):
        for index in range(players):
            output += "%25s" % hands[index].cards[line]
        output += "\n"
    output += "-" * (25 * players) + "\n"
    output += r"  9  P  M  J  Q  K  A  R|" * players
    output += "\n"
    for index in range(players):
        output += " %2d " % score_meld._nines(hands[index])
        output += "%2d " % score_meld._pinochle(hands[index])
        output += "%2d " % score_meld._marriages(hands[index])
        output += "%2d " % score_meld._jacks(hands[index])
        output += "%2d " % score_meld._queens(hands[index])
        output += "%2d " % score_meld._kings(hands[index])
        output += "%2d " % score_meld._aces(hands[index])
        output += r"%2d|" % score_meld._run(hands[index])
    output += "\n"
    output += "Meld  "
    for index in range(players):
        output += "%12d%12s" % (score_meld.score(hands[index]), "")
    output += "\n"
    output += "Trick "
    for index in range(players):
        output += "%12d%12s" % (score_tricks.score(hands[index]), "")
    output += "\n"
    if len(kitty) > 0:
        output += "\nKitty:\n"
        output += str(kitty)
        output += "\n"

    return output


@log_decorator
def hand_summary(hand: Hand) -> str:  # pragma: no cover
    output = ""

    player_list: List[Player] = []
    for __, e_team in enumerate(hand.teams):
        for __, e_player in enumerate(e_team.players):
            output += " %8s (%6s)%9s" % (e_player.name, e_team.name, "",)
            player_list.append(e_player)
    output += "\n"
    for line in range(player_list[0].hand.size):
        for __, e_player in enumerate(player_list):
            output += "%25s" % e_player.hand.cards[line]
        output += "\n"
    output += "-" * (25 * len(player_list))
    return output


@log_decorator
def hand_summary_score(hand: Hand) -> str:  # pragma: no cover
    player_list: List[Player] = []
    for __, e_team in enumerate(hand.teams):
        for __, e_player in enumerate(e_team.players):
            player_list.append(e_player)

    output = r"  9  P  M  J  Q  K  A  R|" * len(player_list)
    output += "\n"
    for __, e_player in enumerate(player_list):
        output += " %2d " % score_meld._nines(e_player.hand)
        output += "%2d " % score_meld._pinochle(e_player.hand)
        output += "%2d " % score_meld._marriages(e_player.hand)
        output += "%2d " % score_meld._jacks(e_player.hand)
        output += "%2d " % score_meld._queens(e_player.hand)
        output += "%2d " % score_meld._kings(e_player.hand)
        output += "%2d " % score_meld._aces(e_player.hand)
        output += r"%2d|" % score_meld._run(e_player.hand)
    output += "\n"
    output += "Meld  "
    for __, e_player in enumerate(player_list):
        output += "%12d%12s" % (score_meld.score(e_player.hand), "")
    output += "\n"
    output += "Trick "
    for __, e_player in enumerate(player_list):
        output += "%12d%12s" % (score_tricks.score(e_player.hand), "")

    return output


@log_decorator
def convert_to_svg_names(deck: PinochleDeck) -> List[str]:
    return_list = []
    for p_card in deck:
        (value, suit) = str(p_card).split(" of ")
        suit = suit.lower()[:-1]  # Trim the trailing 's'
        value = value.lower()
        return_list.append(f"{suit}_{value}")

    return return_list


@log_decorator
def convert_to_svg_name(card: PinochleCard) -> str:
    (value, suit) = str(card).split(" of ")
    suit = suit.lower()[:-1]  # Trim the trailing 's'
    value = value.lower()
    return f"{suit}_{value}"


@log_decorator
def convert_from_svg_names(deck: list) -> PinochleDeck:
    return_deck = PinochleDeck()
    for p_card in deck:
        (suit, value) = p_card.split("_")
        suit.capitalize()
        suit += "s"  # Re-add the trailing s
        value.capitalize()
        temp_card = PinochleCard(value=value, suit=suit)
        return_deck.add(temp_card)

    return return_deck
