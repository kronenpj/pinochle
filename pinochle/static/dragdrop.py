from sys import stderr

from browser import document, html
import brySVG.polygoncanvas as SVG
from random import sample

# Locate the card table in the HTML document.
SVGRoot = document["card_table"]
CARD_URL = "/static/svg-cards.svg#"

# Create the base SVG object for the card table.
canvas = SVG.CanvasObject("95vw", "95vh", None, objid="canvas")
SVGRoot <= canvas
canvas.mouseMode = SVG.MouseMode.DRAG

# Intrinsic dimensions of the cards in the deck.
card_width = 170
card_height = 245

# Gather information about the display environment
table_width = document["canvas"].clientWidth
table_height = document["canvas"].clientHeight

# Calculate relative vertical overlap for cards, if needed.
yincr = int(card_height / 4)

deck = list()
for decks in range(0, 2):  # Double deck
    for card in ["ace", "10", "king", "queen", "jack", "9"]:
        for suit in ["heart", "diamond", "spade", "club"]:
            deck.append(f"{suit}_{card}")

# Collect cards into discard and player's hand
discard_deck = sample(deck, k=4).sort()
for choice in discard_deck:
    deck.remove(choice)
players_hand = sample(deck, k=13).sort()
for choice in players_hand:
    deck.remove(choice)


def place_cards(deck, location="top", kitty=False):
    """
    Place the supplied deck / list of cards on the display. This will need to be 
    refactored somewhat if a gradual kitty reveal is desired.

    :param deck: card names in the format that svg-cards.svg wants.
    :type deck: list
    :param location: String of "top", "bottom" or anything else, defaults to "top", instructing where to place the cards vertically.
    :type location: str, optional
    :param kitty: Whether or not to draw backs (True) or faces (False), defaults to False
    :type kitty: bool, optional
    """

    # Where to vertically place first card on the table
    if location.lower() == "top":
        start_y = 0
    elif location.lower() == "bottom":
        # Place cards one card height above the bottom, plus a bit.
        start_y = table_height - card_height - 2
    else:
        # Place cards in the middle.
        start_y = table_height / 2 - card_height / 2

    # Calculate how far to move each card horizontally and based on that calculate the
    # starting horizontal position.
    xincr = int(table_width / (len(deck) + 0.5))
    if xincr > card_width:
        xincr = card_width
        start_x = int(table_width / 2 - xincr * (len(deck) + 0.0) / 2)
    else:
        start_x = 0
    (xpos, ypos) = (start_x, start_y)

    for card_value in deck:
        if kitty:
            piece = SVG.UseObject(href=CARD_URL + "back")
            piece.style["fill"] = "crimson"  # darkblue also looks "right"
        else:
            piece = SVG.UseObject(href=CARD_URL + f"{card_value}")
        canvas.addObject(piece)
        canvas.translateObject(piece, (xpos, ypos))
        xpos += xincr
        if xpos > table_width - xincr:
            xpos = 0
            ypos += yincr

# Last-drawn are on top (z-index wise)
place_cards(deck, "blah")
place_cards(discard_deck, kitty=True)
place_cards(players_hand, "bottom")
