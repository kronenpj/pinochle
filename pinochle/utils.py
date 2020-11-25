"""
Utilities to work with a deck of Pinochle cards.

License: GPLv3
Inspired by: https://github.com/Trebek/pydealer
Modernized and modified for Pinochle by Paul Kronenwetter
"""

import copy
from typing import List

from game.hand import Hand
from game.player import Player
from pinochle import const, score_meld, score_tricks
from pinochle.card import PinochleCard
from pinochle.deck import PinochleDeck
from pinochle.exceptions import InvalidDeckError, InvalidSuitError
from pinochle.log_decorator import log_decorator


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
def deal_hands(deck=None, players=4, kitty_cards=0):
    if deck is None:
        deck = populate_deck()

    # Create empty hands
    hand = [None] * players
    for index in range(0, players):
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

    # Pull out random cards for the kitty, if requested
    if kitty_cards > 0:
        kitty += deck.deal(kitty_cards)
        deck.shuffle()

    # Deal remaining cards equally to each player, one at a time and
    while deck.size > 0:
        for index in range(0, players):
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
            key=lambda x: (-ranks["suits"][x.suit], -ranks["values"][x.value])
            if x.suit is not None
            else 0,
        )

    return cards


@log_decorator
def set_trump(trump="", hand=PinochleDeck()) -> PinochleDeck:
    """
    Set trump for the supplied hand and return a new deck instance.

    :param trump: String containing suit to be made trump, defaults to ""
    :type trump: str, optional
    :param hand: Deck of cards to process, defaults to PinochleDeck()
    :type hand: PinochleDeck, optional
    :raises InvalidSuitError: [description]
    :raises InvalidDeckError: [description]
    :return: PinochleDeck instance with the suit weight adjusted.
    :rtype: PinochleDeck
    """
    if trump not in const.SUITS:
        raise InvalidSuitError("%s is not a valid suit." % str(trump))
    if not isinstance(hand, PinochleDeck):
        raise InvalidDeckError(
            "Supplied deck (hand) is not an instance of PinochleDeck."
        )

    newhand = copy.deepcopy(hand)
    newhand.ranks["suits"][trump] = const.TRUMP_VALUE
    # print(newhand.ranks)

    return newhand


@log_decorator
def deck_list_summary(
    hands: List[PinochleDeck], players: int, kitty: PinochleDeck = None
) -> str:
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
    if len(kitty):
        output += "\nKitty:\n"
        output += str(kitty)
        output += "\n"

    return output


@log_decorator
def hand_summary(hand: Hand) -> str:
    output = ""

    player_list: List[Player] = []
    for team_index in range(len(hand.teams)):
        for player_index in range(len(hand.teams[team_index].players)):
            output += " Player %1d (Team %1d)%9s" % (player_index, team_index, "")
            player_list.append(hand.teams[team_index].players[player_index])
    output += "\n"
    for line in range(player_list[0].hand.size):
        for player_index in range(len(player_list)):
            output += "%25s" % player_list[player_index].hand.cards[line]
        output += "\n"
    output += "-" * (25 * len(player_list))
    return output


@log_decorator
def hand_summary_score(hand: Hand) -> str:
    player_list: List[Player] = []
    for team_index in range(len(hand.teams)):
        for player_index in range(len(hand.teams[team_index].players)):
            player_list.append(hand.teams[team_index].players[player_index])

    output = r"  9  P  M  J  Q  K  A  R|" * len(player_list)
    output += "\n"
    for player_index in range(len(player_list)):
        output += " %2d " % score_meld._nines(player_list[player_index].hand)
        output += "%2d " % score_meld._pinochle(player_list[player_index].hand)
        output += "%2d " % score_meld._marriages(player_list[player_index].hand)
        output += "%2d " % score_meld._jacks(player_list[player_index].hand)
        output += "%2d " % score_meld._queens(player_list[player_index].hand)
        output += "%2d " % score_meld._kings(player_list[player_index].hand)
        output += "%2d " % score_meld._aces(player_list[player_index].hand)
        output += r"%2d|" % score_meld._run(player_list[player_index].hand)
    output += "\n"
    output += "Meld  "
    for player_index in range(len(player_list)):
        output += "%12d%12s" % (score_meld.score(player_list[player_index].hand), "")
    output += "\n"
    output += "Trick "
    for player_index in range(len(player_list)):
        output += "%12d%12s" % (score_tricks.score(player_list[player_index].hand), "")

    return output
