from sys import stdout

from browser import window, document, html, svg
import brySVG.dragcanvas as SVG
from brySVG.dragcanvas import UseObject
from random import sample

CARD_URL = "/static/playingcards.svg"

# Define constants
table_width = 0
table_height = 0

# Intrinsic dimensions of the cards in the deck.
card_width = 170
card_height = 245


class PlayingCard(UseObject):
    def __init__(
        self,
        href=None,
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
            objid=objid,
        )
        self.flippable = flippable
        if flippable:
            self.bind("click", self.flip_card)
        if movable:
            self.bind("mouseup", self.handler)
            self.bind("touchend", self.handler)
            # self.bind("click", self.handler)
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
            if "touch" in event.type or "click" in event.type:
                new_y = float(obj.attrs["y"])
                # print(f"Touch event: {obj.id=} {new_y=}")

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
                # print(f"Mouse event: {obj.id=} {new_y=}")

            # Determine whether the card is now in a position to be considered thrown.
            if new_y < card_height:
                # print(f"Throwing {obj.id=} ({obj.face_value=})")
                parent_canvas = obj.parentElement

                # Decide which card in discard_deck to replace - identify the index of the
                # first remaining instance of 'card-base'
                placement = discard_deck.index("card-base")
                # This doesn't work...
                # discard_object = parent_canvas[f"discard{placement}"]
                discard_object = [
                    x for x in parent_canvas.childNodes if f"discard{placement}" in x.id
                ][0]

                # Delete the original card.
                parent_canvas.deleteObject(obj)
                # Remove the original card from the player's hand and put it in the
                # discard deck.
                players_hand.remove(obj.face_value)
                discard_deck[placement] = obj.face_value
                # Replace the discard face with that of the original, moved card.
                discard_object.face_value = obj.face_value
                discard_object.movable = False
                # Promote the discard_object to be the selected object.
                obj = discard_object
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
            self.handler()


def populate_canvas(deck, target_canvas, deck_type="hand"):
    """
    Populate given canvas with the deck of cards but without specific placement.

    :param deck: card names in the format that svg-cards.svg wants.
    :type deck: list
    :param target_canvas: [description]
    :type target_canvas: [type]
    """

    # DOM ID Counters
    counter = 0

    for card_value in deck:
        flippable = None
        movable = True
        show_face = True
        if deck_type == "hand":
            pass  # Defaults work for this type.
        elif deck_type == "kitty":
            show_face = False
            flippable = True
            movable = False
        elif deck_type == "discard":
            movable = False
        else:
            # Throw exception of some species here.
            pass
        # Add the card to the canvas.
        piece = PlayingCard(
            face_value=card_value,
            objid=f"{deck_type}{counter}",
            show_face=show_face,
            flippable=flippable,
            movable=movable,
        )
        target_canvas.addObject(piece, fixed=not movable)

        counter += 1


def place_cards(deck, target_canvas, location="top", deck_type="hand"):
    """
    Place the supplied deck / list of cards in the correct position on the display.

    :param deck: card names in the format that svg-cards.svg wants.
    :type deck: list
    :param location: String of "top", "bottom" or anything else for middle, defaults to
    "top", instructing routine where to place the cards vertically.
    :type location: str, optional
    :param deck_type: The type of (sub)-deck this is.
    :type deck_type: str, optional # TODO: Should probably be enum
    """
    print("In place_cards.")

    # Calculate relative vertical overlap for cards, if needed.
    yincr = int(card_height / 4)

    # Where to vertically place first card on the table
    if location.lower() == "top":
        start_y = 0
    elif location.lower() == "bottom":
        # Place cards one card height above the bottom, plus a bit.
        start_y = table_height - card_height - 2
    else:
        # Place cards in the middle.
        start_y = table_height / 2 - card_height / 2

    # Calculate how far to move each card horizontally then based on that,
    # calculate the starting horizontal position.
    xincr = int(table_width / (len(deck) + 0.5))  # Spacing to cover entire width
    start_x = 0
    if len(deck) == 4:
        print(f"Calculated: {xincr=}, {start_x=}")
    if xincr > card_width:
        xincr = int(card_width)
        # Start deck/2 cards from table's midpoint horizontally
        start_x = int(table_width / 2 - xincr * (float(len(deck))) / 2)
        if len(deck) == 4:
            print(f"Reset to card_width: {xincr=}, {start_x=}")

    # Set the initial position
    xpos = start_x
    ypos = start_y
    # print(f"Start position: ({xpos}, {ypos})")

    # Iterate over canvas's child nodes and move any node
    # where deck_type matches the node's id
    for node in [x for x in target_canvas.childNodes if deck_type in x.id]:
        # print(f"Processing node {node.id}. ({xpos=}, {ypos=})")

        x = float(node.attrs["x"])
        y = float(node.attrs["y"])
        # if (xpos - x) != 0 and (ypos - y) != 0:
        #     print(f"Moving {node.id} from ({x}, {y}) by ({xpos-x}px, {ypos-y}px) to ({xpos}, {ypos})")
        target_canvas.translateObject(node, (xpos - x, ypos - y))

        # Each time through the loop, move the next card's starting position.
        xpos += xincr
        if xpos > table_width - xincr:
            # print(f"Exceeded x.max, resetting position. ({xpos=}, {table_width=}, {xincr=}")
            xpos = xincr
            ypos += yincr


def calculate_dimensions():
    global table_width, table_height
    # Gather information about the display environment
    table_width = document["canvas"].clientWidth
    table_height = document["canvas"].clientHeight


def update_display(event=None):
    calculate_dimensions()
    # Place the desired decks on the display.
    if canvas.firstChild is None:
        populate_canvas(discard_deck, canvas, "discard")
        # populate_canvas(kitty_deck, canvas, "kitty")
        # populate_canvas(pinochle_deck, canvas, "discard")
        populate_canvas(players_hand, canvas, "hand")

    # Last-drawn are on top (z-index wise)
    place_cards(discard_deck, canvas, location="top", deck_type="discard")
    # place_cards(kitty_deck, canvas, location="top", deck_type="kitty")
    # place_cards(pinochle_deck, canvas, location="middle", deck_type="discard")
    place_cards(players_hand, canvas, location="bottom", deck_type="hand")


# Make the update_display function easily available to scripts.
window.update_display = update_display

# Locate the card table in the HTML document.
CardTable = document["card_table"]

# Create the base SVG object for the card table.
canvas = SVG.CanvasObject("95vw", "95vh", None, objid="canvas")

# Attach the card SVG and the new canvas to the card_table div of the document.
CardTable <= SVG.Definitions(filename=CARD_URL)
CardTable <= canvas
canvas.setDimensions()

# TODO: Create groups to put cards in so that the screen can be cleared without event
# callbacks being lost (I hope).

# TODO: Call game API to retrieve list of cards for player's hand and other sub-decks.

# TODO: Be sure not to read the kitty until after the bid is won so that the player's
# can't cheat easily.

# Quickie deck generation while I'm building the real API
pinochle_deck = list()
for decks in range(0, 2):  # Double deck
    for card in ["ace", "10", "king", "queen", "jack", "9"]:
        for suit in ["heart", "diamond", "spade", "club"]:
            pinochle_deck.append(f"{suit}_{card}")

# Collect cards into discard, kitty and player's hand
discard_deck = ["card-base" for iter in range(4)]
kitty_deck = sorted(sample(pinochle_deck, k=4))
for choice in kitty_deck:
    pinochle_deck.remove(choice)
players_hand = sorted(sample(pinochle_deck, k=13))
for choice in players_hand:
    pinochle_deck.remove(choice)

# Attach the card graphics file
document["card_definitions"] <= SVG.Definitions(filename=CARD_URL)

document['please_wait'].text=""
update_display()

canvas.fitContents()
canvas.mouseMode = SVG.MouseMode.DRAG
