# Import PyDealer
import pydealer


def create_deck():
    deck1 = pydealer.Deck()
    # Add a second set of cards.
    deck1.build()

    # Create a list of indices where the unused card faces
    # are captured.
    items = list()
    for face in [x for x in range(2, 9)]:
        items += deck1.find(f"{face}")

    # Trim the deck down to the cards used in pinochle by
    # copying card by card and excluding the above list.
    deck2 = pydealer.Deck()
    deck2.empty()
    for card in range(0, deck1.size):
        if card not in items:
            deck2.add(deck1.cards[card])

    deck2.shuffle()
    return deck2


def deal_hands(players=4, deck=None, kitty_cards=4):
    if deck is None:
        deck = create_deck()

    # Create empty hands
    hand = list()
    for index in range(0, players):
        hand.append(pydealer.Deck())
        hand[index].empty()
    kitty = pydealer.Deck()
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


def temp():
    players = 4
    kitty_cards = 4
    mydeck = create_deck()

    hands, kitty = deal_hands(deck=mydeck, players=players, kitty_cards=kitty_cards)

    if kitty.size > 0:
        print(f"Kitty ({kitty.size}):")
        print(kitty)
    for index in range(0, players):
        print(f"\nHand {index} ({hands[index].size}):")
        print(hands[index])
    for index in range(0, players - 1):
        assert hands[index].size == hands[index + 1].size


if __name__ == "__main__":  # pragma: no mutate
    # execute only if run as a script
    temp()
