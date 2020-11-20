from collections import deque

from pydealer import Deck, Stack

from . import const, custom_log, pinochle_utils
from .log_decorator import log_decorator


class PinochleDeck(Deck):
    @log_decorator
    def __init__(self, **kwargs):
        """
        PinochleDeck constructor method.

        """
        self._cards = deque(kwargs.get("cards", []))

        self.jokers = kwargs.get("jokers", False)  # pragma: no mutate
        self.num_jokers = kwargs.get("num_jokers", 0)  # pragma: no mutate
        self.rebuild = kwargs.get("rebuild", False)
        self.re_shuffle = kwargs.get("re_shuffle", False)
        self.ranks = kwargs.get("ranks", const.PINOCHLE_RANKS)
        self.decks_used = 0

        if kwargs.get("build", True):
            self.build()

    @log_decorator
    def __add__(self, other):
        """
        Allows you to add (merge) decks together, with the ``+`` operand.

        :arg other:
            The other Deck to add to the Deck. Can be a ``Stack`` or ``Deck``
            instance.

        :returns:
            A new PinochleDeck instance, with the combined cards.

        """
        try:
            new_deck = PinochleDeck(
                cards=(list(self.cards) + list(other.cards)), build=False
            )
        except:
            new_deck = PinochleDeck(cards=list(self.cards) + other, build=False)

        return new_deck

    @log_decorator
    def __repr__(self):
        """
        Returns a string representation of the ``PinochleDeck`` instance.

        :returns:
            A string representation of the PinochleDeck instance.

        """
        return "PinochleDeck(cards=%r)" % (self.cards)

    @log_decorator
    def build(self, jokers=False, num_jokers=0):
        """
        Builds a standard pinochle card deck of Card instances.

        :arg bool jokers:
            Whether or not to include jokers in the deck. - Ignored - Pinochle decks do
            not use Jokers.
        :arg int num_jokers:
            The number of jokers to include. - Ignored - Pinochle decks do not use
            Jokers.

        """
        self.decks_used += 1

        self.cards += pinochle_utils.build_cards(False, 0)

    @log_decorator
    def sort(self, ranks=None):
        """
        Sorts the stack, either by poker ranks, or big two ranks.

        :arg dict ranks:
            The rank dict to reference for sorting. If ``None``, it will
            default to ``PINOCHLE_RANKS``.

        :returns:
            The sorted cards.

        """
        ranks = ranks or self.ranks
        self.cards = pinochle_utils.sort_cards(self.cards, ranks)

    @log_decorator
    def deal(
        self, num=1, rebuild=False, shuffle=False, end=const.TOP
    ):  # pragma: no cover
        """
        Returns a list of cards, which are removed from the deck.

        :arg int num:
            The number of cards to deal.
        :arg bool rebuild:
            Whether or not to rebuild the deck when cards run out.
        :arg bool shuffle:
            Whether or not to shuffle on rebuild.
        :arg str end:
            The end of the ``Stack`` to add the cards to. Can be ``TOP`` ("top")
            or ``BOTTOM`` ("bottom").

        :returns:
            A given number of cards from the deck.

        """
        _num = num

        rebuild = rebuild or self.rebuild
        re_shuffle = shuffle or self.re_shuffle

        self_size = self.size

        if rebuild or num <= self_size:
            dealt_cards = [None] * num
        elif num > self_size:
            dealt_cards = [None] * self_size

        while num > 0:
            ends = {const.TOP: self.cards.pop, const.BOTTOM: self.cards.popleft}
            n = _num - num
            try:
                card = ends[end]()
                dealt_cards[n] = card
                num -= 1
            except:
                if self.size == 0:
                    if rebuild:
                        self.build()
                        if re_shuffle:
                            self.shuffle()
                    else:
                        break

        return Stack(cards=dealt_cards)
