from sys import stdout

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
        movable=True,
    ):
        # Set the initial face to be shown.
        if href is None:
            href = "#back"
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
        if flippable:
            self.bind("click", self.flip_card)
        if movable:
            # FIXME: Registering mouseup causes touch to require double-taps again.
            # self.bind("mouseup", self.handler)
            # FIXME: Registering touchend doesn't do anything.
            # self.bind("touchend", self.handler)
            pass

        self.handler()

    def handler(self, event=None):
        # print("In PlayingCard.handler()")
        obj = self
        new_y = table_height

        # print(f"{obj.attrs['y']}, {obj.style['transform']}")
        # Moving a card within a card_height of the top "throws" that card.
        if (
            event is not None
            and obj.id.startswith("hand")  # Can only throw cards from the player's hand
            and obj.show_face  # Only throw cards that are face-up
            and obj.style["transform"] != ""  # Empty when not moving
        ):
            # The object already has the correct 'Y' value from the move.
            if "touch" in event.type:
                new_y = float(obj.attrs["y"])
                print(f"Touch event: {obj.id=} {new_y=}")

            # Cope with the fact that the original Y coordinate is given rather than the
            # new one. And that the style element is a string...
            if "mouse" in event.type:
                # TODO: See if there's a better way to do this.
                transform = obj.style["transform"]
                starting_point = transform.find("translate(")
                if starting_point >= 0:
                    y_coord = transform.find("px,", starting_point) + 4
                    y_coord_end = transform.find("px", y_coord)
                    y_move = transform[y_coord:y_coord_end]
                    new_y = float(obj.attrs["y"]) + float(y_move)
                print(f"Mouse event: {obj.id=} {new_y=}")

            # Determine whether the card is now in a position to be considered thrown.
            if new_y < card_height:
                print(f"Throwing {obj.id=} ({obj.face_value=})")
                players_hand.remove(obj.face_value)
                discard_deck.insert(0, obj.face_value)
                discard_deck.remove("card-base")
                # TODO: Call game API to notify server what card was thrown by which
                # player.
                update_display()

        # Display the correct card face.
        if obj.show_face:
            obj.attrs["href"] = f"#{obj.face_value}"
            obj.style["fill"] = ""
        else:
            obj.attrs["href"] = "#back"
            obj.style["fill"] = "crimson"  # darkblue also looks "right"
        # print("Leaving PlayingCard.handler()")

    def flip_card(self, event=None):
        # print("In PlayingCard.flip_card()")
        if self.flippable:
            self.show_face = not self.show_face
            self.handler(event)


def place_cards(deck, target_canvas, location="top", deck_type="hand"):
    """
    Place the supplied deck / list of cards on the display.

    :param deck: card names in the format that svg-cards.svg wants.
    :type deck: list
    :param location: String of "top", "bottom" or anything else, defaults to "top", instructing where to place the cards vertically.
    :type location: str, optional
    :param deck_type: The type of (sub)-deck this is.
    :type deck_type: str, optional # TODO: Should probably be enum
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
        if deck_type == "hand":
            piece = PlayingCard(
                face_value=card_value,
                objid=f"{deck_type}{counter}",
                origin=(xpos, ypos),
            )
            target_canvas.addObject(piece)
        elif deck_type == "kitty":
            piece = PlayingCard(
                face_value=card_value,
                objid=f"{deck_type}{counter}",
                origin=(xpos, ypos),
                show_face=False,
                flippable=True,
                movable=False,
            )
            target_canvas.addObject(piece, fixed=True)
        elif deck_type == "discard":
            piece = PlayingCard(
                face_value=card_value,
                objid=f"{deck_type}{counter}",
                origin=(xpos, ypos),
                show_face=True,
                movable=False,
            )
            target_canvas.addObject(piece, fixed=True)
        else:
            # Throw exception of some species here.
            pass

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


def update_display():
    calculate_dimensions()
    canvas.deleteAll()

    # Last-drawn are on top (z-index wise)
    # place_cards(deck, temp_group, location="middle", deck_type="discard")
    # place_cards(discard_deck, canvas, location="top", deck_type="discard")
    place_cards(kitty_deck, canvas, location="top", deck_type="kitty")
    place_cards(players_hand, canvas, location="bottom", deck_type="hand")

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

# TODO: Call game API to retrieve list of cards for player's hand and other sub-decks.
# Quickie deck generation while I'm building the real API
deck = list()
for decks in range(0, 2):  # Double deck
    for card in ["ace", "10", "king", "queen", "jack", "9"]:
        for suit in ["heart", "diamond", "spade", "club"]:
            deck.append(f"{suit}_{card}")

# Collect cards into discard, kitty and player's hand
discard_deck = ["card-base", "card-base", "card-base", "card-base"]
kitty_deck = sorted(sample(deck, k=4))
for choice in kitty_deck:
    deck.remove(choice)
players_hand = sorted(sample(deck, k=13))
for choice in players_hand:
    deck.remove(choice)


update_display()

canvas.setDimensions()
canvas.fitContents()
canvas.mouseMode = SVG.MouseMode.DRAG
