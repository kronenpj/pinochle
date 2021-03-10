from sys import stderr

from browser import document
import brySVG.polygoncanvas as SVG

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

# Calculate relative increments for the card table.
xincr = int(table_width / 13)
yincr = int(card_height / 4)

# Where to start the first card on the table.
(xpos, ypos) = (0, 0)

# Fan out the cards.
for card in ["ace", "10", "king", "queen", "jack", "9"]:
    for suit in ["heart", "diamond", "spade", "club"]:
        for decks in range(0, 2):  # Double decks
            piece = SVG.UseObject(href="/static/svg-cards.svg#" + f"{suit}_{card}")
            canvas.addObject(piece)
            canvas.translateObject(piece, (xpos, ypos))
            xpos += xincr
        if xpos > table_width - card_width:
            xpos = 0
            ypos += yincr
