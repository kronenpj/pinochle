from sys import stderr

from browser import window, document, html, svg
import brySVG.dragcanvas as SVG
from brySVG.dragcanvas import UseObject
from random import sample

CARD_URL = "/static/playingcards.svg"

# Intrinsic dimensions of the cards in the deck.
card_width = 170
card_height = 245

# Calculate relative vertical overlap for cards, if needed.
yincr = int(card_height / 4)


class PlayingCard(UseObject):
    def __init__(
        self,
        href=None,
        origin=(0, 0),
        angle=0,
        objid=None,
        face_value="back",
        show_face=True,
        flippable=None,
    ):
        # Set the initial face to be shown.
        if href is None:
            href = f"#{face_value}" if show_face else "#back"
        self.face_value = face_value
        self.show_face = show_face
        UseObject.__init__(
            self,
            href=href,
            origin=origin,
            angle=angle,
            objid=objid,
        )
        self.flippable = flippable
        self.bind("click", flip_card)  # This doesn't work right now.
        self.update()

    def update(self):
        super().update()

        # Moving a card within a card_height of the top "throws" that card.
        if (
            not self.id.startswith("kitty")  # Can't throw kitty cards
            and self.show_face  # Don't throw cards that are face-down
            and float(self.attrs["y"]) < card_height
        ):
            stderr.write(f"Throwing {self.id=} ({self.attrs['y']=})")

        # Indirectly handle flipping a card over.
        if self.show_face:
            self.attrs["href"] = f"#{self.face_value}"
            self.style["fill"] = ""
        else:
            self.attrs["href"] = "#back"
            self.style["fill"] = "crimson"  # darkblue also looks "right"

    def flip_card(self):
        if self.flippable:
            self.show_face = not self.show_face
            self.update()


def flip_card(event):
    """
    This is intended to be called when a click event is registered.

    :param event: [description]
    :type event: [type]
    """
    obj = document[event.target.id]
    if obj.flip_card is not None:
        obj.flip_card()


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

    # DOM ID Counters
    counter = 0

    for card_value in deck:
        if not kitty:
            piece = PlayingCard(
                face_value=card_value, objid=f"hand{counter}", origin=(xpos, ypos)
            )
        else:
            piece = PlayingCard(
                face_value=card_value,
                show_face=False,
                flippable=True,
                objid=f"kitty{counter}",
                origin=(xpos, ypos),
            )
        if not kitty:
            # This replaces the event handler.
            canvas.addObject(piece)
        else:
            # This retains the event handler defined above.
            canvas <= piece
            # Marks the card as immovable
            piece.attrs["fixed"] = True

        counter += 1
        xpos += xincr
        if xpos > table_width - xincr:
            xpos = 0
            ypos += yincr


def calculate_dimensions():
    global table_width, table_height
    # Gather information about the display environment
    table_width = document["canvas"].clientWidth
    table_height = document["canvas"].clientHeight


def clear_canvas():
    while canvas.firstChild:
        canvas.removeChild(canvas.firstChild)


def update_display():
    calculate_dimensions()
    clear_canvas()

    # Last-drawn are on top (z-index wise)
    # place_cards(deck, location="middle")
    place_cards(discard_deck, kitty=True)
    place_cards(players_hand, location="bottom")

    SVGRoot <= canvas


# Make the upadte_display function easily available to scripts.
window.update_display = update_display

# Locate the card table in the HTML document.
SVGRoot = document["card_table"]

table_width = 0
table_height = 0

# Create the base SVG object for the card table.
canvas = SVG.CanvasObject("95vw", "95vh", None, objid="canvas")
SVGRoot <= canvas
SVGRoot <= SVG.Definitions(filename=CARD_URL)


# Quickie deck generation while I'm building the real API
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


update_display()

canvas.setDimensions()
canvas.fitContents()
canvas.mouseMode = SVG.MouseMode.DRAG
