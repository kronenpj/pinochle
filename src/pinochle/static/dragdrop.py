from browser import window, document, html, svg
import brySVG.dragcanvas as SVG
from brySVG.dragcanvas import UseObject
from random import sample
import copy

# Define constants
DEBUG = 0
CARD_URL = "/static/playingcards.svg"
GAME_MODES = ["bid", "reveal", "meld", "trick"]
PLAYER_DECK_CONFIG = {
    0: {"flippable": False, "movable": False},
    1: {"flippable": False, "movable": False},
    2: {"flippable": False, "movable": True},
    3: {"flippable": False, "movable": True},
}
OTHER_DECK_CONFIG = {  # Doubles as the mode for the meld pile used in the "bid" mode.
    # Also doubles as the mode for the discard pile used in the "trick" mode.
    0: {"flippable": False, "movable": False, "show_face": False},  # Bid (Kitty)
    1: {"flippable": True, "movable": False, "show_face": False},  # Reveal (Kitty)
    2: {"flippable": False, "movable": False, "show_face": True},  # Meld (Meld)
    3: {"flippable": False, "movable": False, "show_face": True},  # Trick (Discard)
}
# TODO: Retrieve current game state from API
GAME_MODE = 0

# API "Constants"
GAME_ID = ""
TEAM_ID = ""
PLAYER_ID = ""
PLAYERS = 4
PLAYER_NAME = ["" for _ in range(PLAYERS)]

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
        self.bind("click", self.card_click_handler)
        if movable:
            self.bind("mouseup", self.move_handler)
            self.bind("touchend", self.move_handler)
            # self.bind("click", self.move_handler)
            pass
        self.face_update_dom()

    def face_update_dom(self):
        if DEBUG:
            print("Entering PlayingCard.face_update_dom()")

        # Display the correct card face.
        if self.show_face:
            self.attrs["href"] = f"#{self.face_value}"
            self.style["fill"] = ""
        else:
            self.attrs["href"] = "#back"
            self.style["fill"] = "crimson"  # darkblue also looks "right"

    def move_handler(self, event=None):
        if DEBUG:
            print(
                f"PlayingCard.move_handler: {self.attrs['y']}, {self.style['transform']}"
            )

        # Moving a card within a card_height of the top "throws" that card.
        if (
            event
            and self.id.startswith(
                "player"
            )  # Can only throw cards from the player's hand
            and self.show_face  # Only throw cards that are face-up
            and self.style["transform"] != ""  # Empty when not moving
        ):
            self.play_handler(event)

    def play_handler(self, event=None):
        """
        Handler for when a card is "played." This can mean one of two things.
        1. The card is chosen as meld either by moving or clicking on the card.
        2. The card is 'thrown' during trick play.

        :param event: [description], defaults to None
        :type event: [type], optional
        """
        obj = self
        new_y = table_height

        # The object already has the correct 'Y' value from the move.
        if "touch" in event.type or "click" in event.type:
            new_y = float(obj.attrs["y"])
            if DEBUG > 1:
                print(f"PlayingCard.play_handler: Touch event: {obj.id=} {new_y=}")

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
            if DEBUG > 1:
                print(f"PlayingCard.play_handler: Mouse event: {obj.id=} {new_y=}")

        # Determine whether the card is now in a position to be considered thrown.
        if new_y < card_height or "click" in event.type:
            if DEBUG > 1:
                print(
                    f"PlayingCard.play_handler: Throwing {obj.id=} ({obj.face_value=}) {obj.canvas}"
                )
            parent_canvas = obj.canvas
            card_tag = GAME_MODES[GAME_MODE]

            # Protect the player's deck during meld process.
            # Create a reference to the appropriate deck by mode.
            receiving_deck = []
            # This "should never be called" during GAME_MODEs 0 or 1.
            add_only = False
            if GAME_MODE == 2:  # Meld
                if True or "player" in obj.id:
                    sending_deck = players_meld_deck  # Deep copy
                    receiving_deck = meld_deck  # Reference
                else:
                    add_only = True
                    card_tag = "player"
                    sending_deck = meld_deck  # Reference
                    receiving_deck = players_meld_deck  # Deep copy
            if GAME_MODE == 3:  # Trick
                sending_deck = players_hand  # Reference
                receiving_deck = discard_deck  # Reference

            # TODO: Finish implementation option for player to move card from meld deck back into their hand. The list manipulation should be ok, but the DOM is missing a card in the player's deck for the code below to work as written.

            # Decide which card in receiving_deck to replace - identify the index of the
            # first remaining instance of 'card-base'
            if add_only and "card-base" not in receiving_deck:
                receiving_deck.append("card-base")
            placement = receiving_deck.index("card-base")
            if DEBUG > 1:
                print(f"PlayingCard.play_handler: Locating {card_tag}{placement}")
                id_list = [objid for (objid, _) in parent_canvas.objectDict.items()]

                print(
                    f"PlayingCard.play_handler: {parent_canvas.attrs['mode']}: {id_list}"
                )
            # Locate the ID of the target card in the DOM.
            # Tried:
            #    discard_object = parent_canvas.getElementById(f"{card_tag}{placement}")
            #       only returns the DOM object.
            #    discard_object = parent_canvas[f"{card_tag}{placement}"]
            #       wrong access method
            discard_object = [
                x
                for (objid, x) in parent_canvas.objectDict.items()
                if f"{card_tag}{placement}" in objid
            ][0]

            # Delete the original card's transparent hit target from the UI.
            parent_canvas.deleteObject(obj.hitTarget)
            # Delete the original card from the UI.
            parent_canvas.deleteObject(obj)
            # Remove the original card from the player's hand and put it in the
            # discard deck.
            sending_deck.remove(obj.face_value)
            receiving_deck[placement] = obj.face_value
            # Replace the discard face with that of the original, moved card.
            discard_object.face_value = obj.face_value
            discard_object.href.baseVal = obj.href.baseVal

            # TODO: Remove this when taking meld back is implemented above.
            discard_object.movable = False
            discard_object.unbind("click")
            # TODO: Remove this when taking meld back is implemented above.

            # TODO: Call game API to notify server what card was added to meld or
            # thrown and by which player.
            obj.face_update_dom()
            update_display()

    def card_click_handler(self, event=None):
        """
        Click handler for the playing card. The action depends on the game mode.
        Since the only time this is done is during the meld process, also call the API to
        notify it that a kitty card has been flipped over and which card that is.

        :param event: [description], defaults to None
        :type event: [type], optional
        """
        if DEBUG:
            print("Entering PlayingCard.card_click_handler()")
        if event and "click" in event.type:
            if GAME_MODE == 1 and self.flippable:
                self.show_face = not self.show_face
                self.flippable = False
                # TODO: Call game API to notify the other players this particular card was
                # flipped over and add it to the player's hand.
                players_hand.append(self.face_value)
                players_meld_deck.append(self.face_value)
                self.face_update_dom()
            if GAME_MODE == 2:
                self.play_handler(event)


def populate_canvas(deck, target_canvas, deck_type="player"):
    """
    Populate given canvas with the deck of cards but without specific placement.

    :param deck: card names in the format that svg-cards.svg wants.
    :type deck: list
    :param target_canvas: [description]
    :type target_canvas: [type]
    """
    if DEBUG:
        print(
            "Entering populate_canvas(deck={},target_canvas={},deck_type={}).".format(
                deck, target_canvas, deck_type
            )
        )

    # DOM ID Counters
    counter = 0

    # TODO: Need a "bury" display for bid winner.
    for card_value in deck:
        flippable = None
        movable = True
        show_face = True
        if "player" in deck_type:
            flippable = PLAYER_DECK_CONFIG[GAME_MODE]["flippable"]
            movable = PLAYER_DECK_CONFIG[GAME_MODE]["movable"]
        elif "kitty" in deck_type or "meld" in deck_type or "trick" in deck_type:
            show_face = OTHER_DECK_CONFIG[GAME_MODE]["show_face"]
            flippable = OTHER_DECK_CONFIG[GAME_MODE]["flippable"]
            movable = OTHER_DECK_CONFIG[GAME_MODE]["movable"]
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


def place_cards(deck, target_canvas, location="top", deck_type="player"):
    """
    Place the supplied deck / list of cards in the correct position on the display.

    :param deck: card names in the format that svg-cards.svg wants.
    :type deck: list
    :param location: String of "top", "bottom" or anything else for middle, defaults to
    "top", instructing routine where to place the cards vertically.
    :type location: str, optional
    :param deck_type: The type of (sub)-deck this is.
    :type deck_type: str, optional # TODO: Should probably be enum-like
    """
    if DEBUG:
        print("Entering place_cards(deck={}, deck_type={}).".format(deck, deck_type))

    # Calculate relative vertical overlap for cards, if needed.
    yincr = int(card_height / 4)

    # Where to vertically place first card on the table
    if location.lower() == "top":
        start_y = 0
    elif location.lower() == "bottom":
        # Place cards one card height above the bottom, plus a bit.
        start_y = table_height - card_height - 2
        # Keep the decks relatively close together.
        if start_y > card_height * 3:
            start_y = card_height * 3 + card_height / 20
    else:
        # Place cards in the middle.
        start_y = table_height / 2 - card_height / 2
        # Keep the decks relatively close together.
        if start_y > card_height * 2:
            start_y = card_height * 2

    # Calculate how far to move each card horizontally then based on that,
    # calculate the starting horizontal position.
    xincr = int(table_width / (len(deck) + 0.5))  # Spacing to cover entire width
    start_x = 0
    if DEBUG > 1 and len(deck) == 4:
        print(f"place_cards: Calculated: {xincr=}, {start_x=}")
    if xincr > card_width:
        xincr = int(card_width)
        # Start deck/2 cards from table's midpoint horizontally
        start_x = int(table_width / 2 - xincr * (float(len(deck))) / 2)
        if DEBUG > 1 and len(deck) == 4:
            print(f"place_cards: Reset to card_width: {xincr=}, {start_x=}")
    if xincr < int(
        card_width / 20
    ):  # Make sure at least the value of the card is visible.
        xincr = int(card_width / 20)

    # Set the initial position
    xpos = start_x
    ypos = start_y
    if DEBUG > 1:
        print(f"place_cards: Start position: ({xpos}, {ypos})")

    # Iterate over canvas's child nodes and move any node
    # where deck_type matches the node's id
    for node in [
        x for (objid, x) in target_canvas.objectDict.items() if deck_type in objid
    ]:
        if DEBUG > 1:
            print(f"place_cards: Processing node {node.id}. ({xpos=}, {ypos=})")

        (x, y) = node.origin
        if DEBUG > 1 and (xpos - x) != 0 and (ypos - y) != 0:
            print(
                f"place_cards: Moving {node.id} from ({x}, {y}) by ({xpos-x}px, {ypos-y}px) to ({xpos}, {ypos})"
            )
        target_canvas.translateObject(node, (xpos - x, ypos - y))

        # Each time through the loop, move the next card's starting position.
        xpos += xincr
        if xpos > table_width - xincr:
            if DEBUG > 1:
                print(
                    f"place_cards: Exceeded x.max, resetting position. ({xpos=}, {table_width=}, {xincr=}"
                )
            xpos = xincr
            ypos += yincr


def calculate_dimensions():
    global table_width, table_height
    # Gather information about the display environment
    table_width = document["canvas"].clientWidth
    table_height = document["canvas"].clientHeight


def update_display(event=None):
    if DEBUG:
        print("Entering update_display. (mode={})".format(GAME_MODES[GAME_MODE]))
    calculate_dimensions()
    # Place the desired decks on the display.
    if not canvas.objectDict:
        if GAME_MODE == 0:  # Bid
            # Use empty deck to prevent peeking at the kitty.
            populate_canvas(discard_deck, canvas, "kitty")
            populate_canvas(players_hand, canvas, "player")
        if GAME_MODE == 1:  # Reveal
            populate_canvas(kitty_deck, canvas, "kitty")
            populate_canvas(players_hand, canvas, "player")
        if GAME_MODE == 2:  # Meld
            populate_canvas(meld_deck, canvas, GAME_MODES[GAME_MODE])
            populate_canvas(players_meld_deck, canvas, "player")
        if GAME_MODE == 3:  # Trick
            populate_canvas(discard_deck, canvas, GAME_MODES[GAME_MODE])
            populate_canvas(players_hand, canvas, "player")

    # Last-drawn are on top (z-index wise)
    if GAME_MODE == 0 or GAME_MODE == 1:  # Bid & Reveal
        place_cards(discard_deck, canvas, location="top", deck_type="kitty")
        place_cards(players_hand, canvas, location="bottom", deck_type="player")
        # TODO: Retrieve events from API to show kitty cards when they are flipped over.
    if GAME_MODE == 2:  # Meld
        # TODO: Expand display to show all four players.
        # TODO: Retrieve events from API to show other player's meld.
        place_cards(meld_deck, canvas, location="top", deck_type=GAME_MODES[GAME_MODE])
        place_cards(players_meld_deck, canvas, location="bottom", deck_type="player")
    if GAME_MODE == 3:  # Trick
        # TODO: Retrieve/send events from API to show cards as they are played.
        place_cards(
            discard_deck, canvas, location="top", deck_type=GAME_MODES[GAME_MODE]
        )
        place_cards(players_hand, canvas, location="bottom", deck_type="player")


def clear_display(event=None):
    if DEBUG:
        print("Entering clear_display (mode={})".format(GAME_MODES[GAME_MODE]))
    global canvas
    try:
        document.getElementById("canvas").remove()
    except AttributeError:
        pass
    if DEBUG > 1:
        print("Destroying canvas with mode: {}".format(canvas.attrs["mode"]))
    canvas.deleteAll()

    # Create the base SVG object for the card table.
    canvas = SVG.CanvasObject("95vw", "95vh", None, objid="canvas")
    canvas.attrs["mode"] = GAME_MODES[GAME_MODE]

    # Attach the new canvas to the card_table div of the document.
    CardTable <= canvas
    canvas.setDimensions()
    update_display()

    # Update buttons
    canvas.addObject(button_clear)
    canvas.addObject(button_refresh)
    canvas.addObject(button_advance_mode)

    canvas.fitContents()
    canvas.mouseMode = SVG.MouseMode.DRAG


def advance_mode(event=None):
    global GAME_MODE
    if DEBUG:
        print(
            "Entering advance_mode (mode={}->{})".format(
                GAME_MODES[GAME_MODE], GAME_MODES[(GAME_MODE + 1) % len(GAME_MODES)]
            )
        )
    # TODO: Retrieve the kitty when transitioning from "bid" to "reveal" modes.
    GAME_MODE = (GAME_MODE + 1) % len(GAME_MODES)
    button_advance_mode.label.textContent = GAME_MODES[GAME_MODE]
    clear_display()


# Make the update_display function easily available to scripts.
window.update_display = update_display
window.clear_display = clear_display
window.advance_mode = advance_mode

# Locate the card table in the HTML document.
CardTable = document["card_table"]

# Attach the card graphics file
document["card_definitions"] <= SVG.Definitions(filename=CARD_URL)

# Create the base SVG object for the card table.
canvas = SVG.CanvasObject("95vw", "95vh", None, objid="canvas")
canvas.attrs["mode"] = "initial"

# TODO: Call game API to retrieve game_id, team_id, player_id, player names, etc...
# TODO: Call game API to retrieve list of cards for player's hand and other sub-decks.
# TODO: Add buttons & display to facilitate bidding. Tie into API.

# Quickie deck generation while I'm building the real API
pinochle_deck = list()
for decks in range(0, 2):  # Double deck
    for card in ["ace", "10", "king", "queen", "jack", "9"]:
        for suit in ["heart", "diamond", "spade", "club"]:
            pinochle_deck.append(f"{suit}_{card}")

# Collect cards into discard, kitty and player's hand
discard_deck = ["card-base" for _ in range(PLAYERS)]
kitty_deck = sorted(
    sample(pinochle_deck, k=4)
)  # 'k' will vary depending on the number of players. 4 for four players, 3 or 6 for three players. 0 will also need to be a valid option.
for choice in kitty_deck:
    pinochle_deck.remove(choice)
HAND_SIZE = int(len(pinochle_deck) / PLAYERS)
meld_deck = ["card-base" for _ in range(HAND_SIZE)]
players_hand = sorted(sample(pinochle_deck, k=HAND_SIZE))
for choice in players_hand:
    pinochle_deck.remove(choice)
# Protect the player's deck during meld process.
players_meld_deck = copy.deepcopy(players_hand)  # Deep copy

# Button to call update_display on demand
button_refresh = SVG.Button(
    position=(-70, 0),
    size=(70, 35),
    text="Refresh",
    onclick=update_display,
    fontsize=18,
    objid="button_refresh",
)

# Button to call clear_display on demand
button_clear = SVG.Button(
    position=(-70, 40),
    size=(70, 35),
    text="Clear",
    onclick=clear_display,
    fontsize=18,
    objid="button_clear",
)

# Button to call clear_display on demand
button_advance_mode = SVG.Button(
    position=(-70, -40),
    size=(70, 35),
    text=GAME_MODES[GAME_MODE],
    onclick=advance_mode,
    fontsize=18,
    objid="button_advance_mode",
)

document.getElementById("please_wait").remove()
clear_display()
