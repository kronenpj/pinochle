from browser import window, document, html, svg
import brySVG.dragcanvas as SVG

CARD_URL = "/static/playingcards.svg"
CARDS = [
    # "n_10",
    # "n_1",
    # "n_2",
    # "n_3",
    # "n_4",
    # "n_5",
    # "n_6",
    # "n_7",
    # "n_8",
    # "n_9",
    # "ace",
    # "king",
    # "queen",
    # "jack",
    # "base",
    # "club",
    # "diamond",
    # "heart",
    # "spade",
    # "jack_1",
    # "jack_3",
    # "jack_2",
    # "jack_4",
    # "queen_4",
    # "queen_2",
    # "queen_3",
    # "queen_1",
    # "king_3",
    # "king_1",
    # "king_4",
    # "king_2",
    # "joker",
    # "laurel",
    # "twist",
    # "club_ace",
    # "club_2",
    # "club_3",
    # "club_4",
    # "club_5",
    # "club_6",
    # "club_7",
    # "club_8",
    # "club_9",
    # "club_10",
    "club_jack",
    # "club_queen",
    # "club_king",
    # "diamond_ace",
    # "diamond_2",
    # "diamond_3",
    # "diamond_4",
    # "diamond_5",
    # "diamond_6",
    # "diamond_7",
    # "diamond_8",
    # "diamond_9",
    # "diamond_10",
    # "diamond_jack",
    "diamond_queen",
    # "diamond_king",
    # "heart_ace",
    # "heart_2",
    # "heart_3",
    # "heart_4",
    # "heart_5",
    # "heart_6",
    # "heart_7",
    # "heart_8",
    # "heart_9",
    # "heart_10",
    # "heart_jack",
    # "heart_queen",
    "heart_king",
    "spade_ace",
    # "spade_2",
    # "spade_3",
    # "spade_4",
    # "spade_5",
    # "spade_6",
    # "spade_7",
    # "spade_8",
    # "spade_9",
    # "spade_10",
    # "spade_jack",
    # "spade_queen",
    # "spade_king",
    # "joker_black",
    # "joker_text",
    # "joker_full",
    # "joker_red",
    # "back",
    # "back_c1",
    # "back_c2",
    # "back_c3",
    # "back_c4",
    # "back_c5",
    # "g_lace",
    # "alternate-back",
    # "card-base",
    # "suit-club",
    # "suit-spade",
    # "suit-heart",
    # "suit-diamond",
]


def calculate_dimensions():
    global table_width, table_height
    # Gather information about the display environment
    table_width = document["canvas"].clientWidth
    table_height = document["canvas"].clientHeight


# Create the base SVG object for the card table.
canvas = SVG.CanvasObject("95vw", "95vh", "green", objid="canvas")

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

# Locate the card table in the HTML document.
CardTable = document["card_table"]

# Attach the card graphics file
document["card_definitions"] <= SVG.Definitions(filename=CARD_URL)

# Create the base SVG object for the card table.
CardTable <= canvas
canvas.setDimensions()
calculate_dimensions()

# Fan out the cards.
for card in CARDS:
    piece = SVG.UseObject(href=f"#{card}")
    canvas.addObject(piece)
    canvas.translateObject(piece, (xpos, ypos))
    xpos += xincr
    if xpos > table_width - card_width:
        xpos = 0
        ypos += yincr

canvas.fitContents()
canvas.mouseMode = SVG.MouseMode.DRAG
