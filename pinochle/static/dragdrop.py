from sys import stderr

from browser import document, html
import brySVG.polygoncanvas as SVG
from random import sample

# Locate the card table in the HTML document.
SVGRoot = document["card_table"]

# Create the base SVG object for the card table.
canvas = SVG.CanvasObject("95vw", "95vh", "green", objid="canvas")
SVGRoot <= canvas
canvas.mouseMode = SVG.MouseMode.DRAG

# Intrinsic dimensions of the cards in the deck.
card_width = 170
card_height = 245

# Gather information about the display environment
table_width = document["card_table"].clientWidth
table_height = document["card_table"].clientHeight

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

# Fan out the cards.
# Where to start the first card on the player's hand.
(xpos, ypos) = (table_width / 2, table_height - (card_height / 2))
xincr = int(table_width / (len(deck) + 3))
for choice in deck:
    piece = SVG.UseObject(href="/static/svg-cards.svg#" + f"{choice}")
    canvas.addObject(piece)
    # Scale down by 0.5 since we're just looking at the rest of the deck.
    document[piece["id"]].style["transform"] += " scale(0.5)"

    canvas.translateObject(piece, (xpos, ypos))

    xpos += xincr
    if xpos > table_width * 2 - xincr:
        xpos = table_width / 2
        ypos += yincr

# Fan out the discard cards.
# Where to start the first card on the discard pile.
(xpos, ypos) = (table_width / 2 - card_width * 2, 0)
xincr = int(table_width / len(discard_deck))
for choice in discard_deck:
    piece = SVG.UseObject(href="/static/svg-cards.svg#" + f"{choice}")
    canvas.addObject(piece)
    canvas.translateObject(piece, (xpos, ypos))
    xpos += card_width
    if xpos > table_width - card_width:
        xpos = table_width / 2
        ypos += yincr

# Fan out the player's hand.
# Where to start the first card on the player's hand.
(xpos, ypos) = (0, table_height - card_height)
xincr = int(table_width / (len(players_hand) + 1))
for choice in players_hand:
    piece = SVG.UseObject(href="/static/svg-cards.svg#" + f"{choice}")
    canvas.addObject(piece)
    canvas.translateObject(piece, (xpos, ypos))
    xpos += xincr
    if xpos > table_width - card_width:
        xpos = 0
        ypos += yincr
