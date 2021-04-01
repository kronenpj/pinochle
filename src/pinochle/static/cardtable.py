"""
In-browser script to handle the card-table user interface.
"""
import copy
import json
import logging

import brySVG.dragcanvas as SVG  # pylint: disable=import-error
from browser import ajax, document, window
from brySVG.dragcanvas import TextObject, UseObject  # pylint: disable=import-error

from constants import CARD_URL, GAME_MODES, OTHER_DECK_CONFIG, PLAYER_DECK_CONFIG

# TODO: Retrieve current game state from API
GAME_MODE = 0

# Programmatically create a pre-sorted deck to compare to when sorting decks of cards.
# Importing a statically-defined list from constants doesn't work for some reason.
# "9", "jack", "queen", "king", "10", "ace"
# "ace", "10", "king", "queen", "jack", "9"
DECK_SORTED = []
for _suit in ["spade", "diamond", "club", "heart"]:
    for _card in ["ace", "10", "king", "queen", "jack", "9"]:
        DECK_SORTED.append(f"{_suit}_{_card}")

mylog = logging.getLogger("cardtable")
# mylog.setLevel(logging.CRITICAL)  # No output
mylog.setLevel(logging.ERROR)  # Function entry/exit
# mylog.setLevel(logging.WARNING)  # Everything

# API "Constants"
AJAX_URL_ENCODING = "application/x-www-form-urlencoded"
GAME_ID = ""
KITTY_SIZE = 0
PLAYER_ID = ""
PLAYERS = 4
ROUND_ID = ""
TEAM_ID = ""

# Various state globals
game_dict = {}
kitty_deck = []
player_dict = {}
players_hand = []
players_meld_deck = []
team_dict = {}
team_list = []

# Track whether this user is the round's bid winner.
round_bid_winner = False  # pylint: disable=invalid-name

table_width = 0  # pylint: disable=invalid-name
table_height = 0  # pylint: disable=invalid-name
button_advance_mode = None  # pylint: disable=invalid-name

# Intrinsic dimensions of the cards in the deck.
card_width = 170  # pylint: disable=invalid-name
card_height = 245  # pylint: disable=invalid-name


class PlayingCard(UseObject):
    """
    PlayingCard class to hold additional attributes than available from UseObject,
    specific to the Pinochle game.

    :param UseObject: brySVG.UseObject class
    :type UseObject: brySVG.UseObject
    """

    def __init__(
        self,
        href=None,
        objid=None,
        face_value="back",
        show_face=True,
        flippable=False,
        movable=True,
    ):
        # Set the initial face to be shown.
        if href is None:
            href = "#back"
        self.face_value = face_value
        self.show_face = show_face
        UseObject.__init__(
            self, href=href, objid=objid,
        )
        self.flippable = flippable
        self.bind("click", self.card_click_handler)
        if movable:
            self.bind("mouseup", self.move_handler)
            self.bind("touchend", self.move_handler)
            # self.bind("click", self.move_handler)
        self.face_update_dom()

    def face_update_dom(self):
        """
        Function to update the document object model for the PlayingCard object,
        depending on the state of show_face.
        """
        mylog.error("Entering PlayingCard.face_update_dom()")

        # Display the correct card face.
        if self.show_face:
            self.attrs["href"] = f"#{self.face_value}"
            self.style["fill"] = ""
        else:
            self.attrs["href"] = "#back"
            self.style["fill"] = "crimson"  # darkblue also looks "right"

    def move_handler(self, event=None):
        """
        Inspect the object's attributes and determine whether additional action needs to
        be taken during a move action.

        :param event: The event object passed in during callback, defaults to None
        :type event: Event(?), optional
        """
        mylog.error(
            "PlayingCard.move_handler: %s, %s",
            self.attrs["y"],
            self.style["transform"],
        )

        # Moving a card within a card_height of the top "throws" that card.
        if (
            event
            and self.id.startswith("player")  # Only play cards from player's hand
            and self.show_face  # Only throw cards that are face-up
            and self.style["transform"] != ""  # Empty when not moving
        ):
            self.play_handler(event)

    def play_handler(self, event=None):
        """
        Handler for when a card is "played." This can mean one of two things.
        1. The card is chosen as meld either by moving or clicking on the card.
        2. The card is 'thrown' during trick play.

        :param event: The event object passed in during callback, defaults to None
        :type event: Event(?), optional
        """
        new_y = table_height

        # The object already has the correct 'Y' value from the move.
        if "touch" in event.type or "click" in event.type:
            new_y = float(self.attrs["y"])
            mylog.warning(
                "PlayingCard.play_handler: Touch event: id=%s new_y=%f", self.id, new_y,
            )

        # Cope with the fact that the original Y coordinate is given rather than the
        # new one. And that the style element is a string...
        if "mouse" in event.type:
            # TODO: See if there's a better way to do this.
            transform = self.style["transform"]
            starting_point = transform.find("translate(")
            if starting_point >= 0:
                y_coord = transform.find("px,", starting_point) + 4
                y_coord_end = transform.find("px", y_coord)
                y_move = transform[y_coord:y_coord_end]
                new_y = float(self.attrs["y"]) + float(y_move)
            mylog.warning(
                "PlayingCard.play_handler: Mouse event: id=%s new_y=%f", self.id, new_y,
            )

        # Determine whether the card is now in a position to be considered thrown.
        if new_y >= card_height and "click" not in event.type:
            # New Y is greater than one card_height from the top.
            return  # Not thrown.

        mylog.warning(
            "PlayingCard.play_handler: Throwing id=%s (face_value=%s) canvas=%s",
            self.id,
            self.face_value,
            self.canvas,
        )
        parent_canvas = self.canvas
        card_tag = GAME_MODES[GAME_MODE]

        # Protect the player's deck during meld process.
        # Create a reference to the appropriate deck by mode.
        receiving_deck = []
        # This "should never be called" during GAME_MODEs 0 or 1.
        add_only = False
        if GAME_MODES[GAME_MODE] in ["meld"]:  # Meld
            if True or "player" in self.id:
                sending_deck = players_meld_deck  # Deep copy
                receiving_deck = meld_deck  # Reference
            else:
                add_only = True
                card_tag = "player"
                sending_deck = meld_deck  # Reference
                receiving_deck = players_meld_deck  # Deep copy
        elif GAME_MODES[GAME_MODE] in ["trick"]:  # Trick
            sending_deck = players_hand  # Reference
            receiving_deck = discard_deck  # Reference

        # TODO: Finish implementation option for player to move card from meld deck back into their hand. The list manipulation should be ok, but the DOM is missing a card in the player's deck for the code below to work as written.

        # Decide which card in receiving_deck to replace - identify the index of the
        # first remaining instance of 'card-base'
        if add_only and "card-base" not in receiving_deck:
            receiving_deck.append("card-base")
        placement = receiving_deck.index("card-base")
        mylog.warning(
            "PlayingCard.play_handler: Locating %s%s\nPlayingCard.play_handler: %s: %s",
            card_tag,
            placement,
            parent_canvas.attrs["mode"],
            [objid for (objid, _) in parent_canvas.objectDict.items()],
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
        parent_canvas.deleteObject(self.hitTarget)
        # Delete the original card from the UI.
        parent_canvas.deleteObject(self)
        # Remove the original card from the player's hand and put it in the
        # discard deck.
        sending_deck.remove(self.face_value)
        receiving_deck[placement] = self.face_value
        # Replace the discard face with that of the original, moved card.
        discard_object.face_value = self.face_value
        discard_object.href.baseVal = self.href.baseVal

        # TODO: Remove this when taking meld back is implemented above.
        discard_object.movable = False
        discard_object.unbind("click")
        # TODO: Remove this when taking meld back is implemented above.

        # TODO: Call game API to notify server what card was added to meld or
        # thrown and by which player.
        self.face_update_dom()
        update_display()

    def card_click_handler(self, event=None):
        """
        Click handler for the playing card. The action depends on the game mode.
        Since the only time this is done is during the meld process, also call the API to
        notify it that a kitty card has been flipped over and which card that is.

        :param event: The event object passed in during callback, defaults to None
        :type event: Event(?), optional
        """
        global players_hand, players_meld_deck  # pylint: disable=global-statement, invalid-name
        mylog.error("Entering PlayingCard.card_click_handler()")
        if event and "click" in event.type:
            if GAME_MODES[GAME_MODE] in ["reveal"] and self.flippable:
                mylog.warning(
                    "PlayingCard.card_click_handler: flippable=%r", self.flippable
                )
                self.show_face = not self.show_face
                self.flippable = False
                # TODO: Call API to notify the other players this particular card was
                # flipped over and add it to the player's hand.
                players_hand.append(self.face_value)
                players_meld_deck.append(self.face_value)
                self.face_update_dom()
            if GAME_MODES[GAME_MODE] in ["meld"]:
                self.play_handler(event)


def on_complete_games(req):
    """
    Callback for AJAX request for the list of games.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_games.")

    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global game list.
    game_dict.clear()
    for item in temp:
        mylog.warning("on_complete_games: item=%s", item)
        game_dict[item["game_id"]] = item
        # game_list.append(item["game_id"])

    display_game_options()


def on_complete_rounds(req):
    """
    Callback for AJAX request for the list of rounds.

    :param req: Request object from callback.
    :type req: [type]
    """
    global ROUND_ID, team_list  # pylint: disable=global-statement, invalid-name
    team_list.clear()
    mylog.error("In on_complete_rounds.")

    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the round ID.
    ROUND_ID = temp["round_id"]
    mylog.warning("on_complete_rounds: round_id=%s", ROUND_ID)

    display_game_options()


def on_complete_teams(req):
    """
    Callback for AJAX request for the information on the teams associated with the round.

    :param req: Request object from callback.
    :type req: [type]
    """
    global team_list  # pylint: disable=global-statement, invalid-name
    mylog.error("In on_complete_teams.")

    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global list of teams for this round.
    team_list.clear()
    team_list = temp["team_ids"]
    mylog.warning("on_complete_teams: team_list=%r", team_list)

    # Clear the team dict here because of the multiple callbacks.
    team_dict.clear()
    for item in team_list:
        get(f"/team/{item}", on_complete_team_names)


def on_complete_team_names(req):
    """
    Callback for AJAX request for team information.

    :param req: Request object from callback.
    :type req: [type]
    """
    global team_dict  # pylint: disable=global-statement, invalid-name
    mylog.error("In on_complete_team_names.")

    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global dict of team names for this round.
    mylog.warning(
        "on_complete_team_names: Setting team_dict[%s]=%r", temp["team_id"], temp
    )
    team_dict[temp["team_id"]] = temp
    mylog.warning("on_complete_team_names: team_dict=%s", team_dict)

    # Only call API once per team, per player.
    for item in team_dict[temp["team_id"]]["player_ids"]:
        mylog.warning("on_complete_team_names: calling get/player/%s", item)
        get(f"/player/{item}", on_complete_players)


def on_complete_players(req):
    """
    Callback for AJAX request for player information.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_players.")

    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global dict of players for reference later.
    player_dict[temp["player_id"]] = temp
    mylog.warning("In on_complete_players: player_dict=%s", player_dict)
    display_game_options()


def on_complete_set_gamecookie(req):
    """
    Callback for AJAX request for setcookie information.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_set_gamecookie.")

    if req.status in [200, 0]:
        get("/getcookie/game_id", on_complete_getcookie)


def on_complete_set_playercookie(req):
    """
    Callback for AJAX request for setcookie information.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_set_playercookie.")

    if req.status in [200, 0]:
        get("/getcookie/player_id", on_complete_getcookie)


def on_complete_getcookie(req):
    """
    Callback for AJAX request for setcookie information.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_getcookie.")
    global GAME_ID, PLAYER_ID, KITTY_SIZE, TEAM_ID, kitty_deck  # pylint: disable=global-statement, invalid-name

    if req.status != 200:
        return
    if req.text is None or req.text == "":
        mylog.warning("on_complete_getcookie: cookie response is None.")
        return
    mylog.warning("on_complete_getcookie: req.text=%s", req.text)
    response_data = json.loads(req.text)

    # Set the global deck of cards for the player's hand.
    mylog.warning("on_complete_getcookie: response_data=%s", response_data)
    if "game_id" in response_data["kind"]:
        GAME_ID = response_data["ident"]
        mylog.warning(
            "on_complete_getcookie: Setting GAME_ID=%s", response_data["ident"]
        )
        try:
            KITTY_SIZE = game_dict[GAME_ID]["kitty_size"]
            mylog.warning("on_complete_getcookie: KITTY_SIZE=%s", KITTY_SIZE)
            if KITTY_SIZE > 0:
                kitty_deck = ["card-base" for _ in range(KITTY_SIZE)]
        except KeyError:
            pass
        clear_display()
    elif "player_id" in response_data["kind"]:
        PLAYER_ID = response_data["ident"]
        mylog.warning(
            "on_complete_getcookie: Setting PLAYER_ID=%s", response_data["ident"]
        )
        get(f"/player/{PLAYER_ID}/hand", on_complete_player_cards)

        # Set the TEAM_ID variable based on the player id chosen.
        for _temp in team_dict:
            mylog.warning("Key: %s Value: %r", _temp, team_dict[_temp]["player_ids"])
            if PLAYER_ID in team_dict[_temp]["player_ids"]:
                TEAM_ID = team_dict[_temp]["team_id"]
    display_game_options()


def on_complete_kitty(req):
    """
    Callback for AJAX request for the round's kitty cards, if any.

    :param req: Request object from callback.
    :type req: [type]
    """
    global kitty_deck  # pylint: disable=global-statement, invalid-name
    mylog.error("In on_complete_kitty.")

    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global deck of cards for the kitty.
    kitty_deck.clear()
    kitty_deck = temp["cards"]
    mylog.warning("on_complete_kitty: kitty_deck=%s", kitty_deck)
    if len(kitty_deck) == 0:
        advance_mode()
        advance_mode()


def on_complete_player_cards(req):
    """
    Callback for AJAX request for the player's cards.

    :param req: Request object from callback.
    :type req: [type]
    """
    global players_hand, players_meld_deck  # pylint: disable=global-statement, invalid-name
    mylog.error("In on_complete_player_cards.")

    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global deck of cards for the player's hand.
    players_hand.clear()
    players_meld_deck.clear()
    players_hand = [x["card"] for x in temp]
    mylog.warning("on_complete_player_cards: players_hand=%s", players_hand)
    players_meld_deck = copy.deepcopy(players_hand)  # Deep copy

    update_display()


def on_complete_get_meld_score(req):
    """
    Callback for AJAX request for the player's meld.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_get_meld_score.")

    temp = on_complete_common(req)
    if temp is None:
        return

    mylog.warning("on_complete_get_meld_score: score: %s", temp)


def on_complete_common(req):
    """
    Common function for AJAX callbacks.

    :param req: Request object from callback.
    :type req: [type]
    :return: Object returned in the request as decoded by JSON.
    :rtype: [type]
    """
    mylog.error("In on_complete_common.")
    if req.status in [200, 0]:
        return json.loads(req.text)

        mylog.warning("on_complete_common: req=%s", req)


def get(url: str, callback=None):
    """
    Wrapper for the AJAX GET call.

    :param url: The part of the URL that is being requested.
    :type url: str
    :param callback: Function to be called when the AJAX request is complete.
    :type callback: function, optional
    """
    req = ajax.ajax()  # pylint: disable=no-value-for-parameter
    if callback is not None:
        req.bind("complete", callback)
    mylog.warning("Calling GET /api%s", url)
    req.open("GET", "/api" + url, True)
    req.set_header("content-type", "application/x-www-form-urlencoded")
    req.send()


def put(data: dict, url: str, callback=None):
    """
    Wrapper for the AJAX PUT call.

    :param data: The data to be submitted.
    :param data: dict
    :param url: The part of the URL that is being requested.
    :type url: str
    :param callback: Function to be called when the AJAX request is complete.
    :type callback: function, optional
    """
    req = ajax.ajax()  # pylint: disable=no-value-for-parameter
    if callback is not None:
        req.bind("complete", callback)
    mylog.warning("Calling PUT /api%s with data: %r", url, data)
    req.open("PUT", url, True)
    req.set_header("content-type", AJAX_URL_ENCODING)
    # req.send({"a": a, "b":b})
    req.send(data)


def post(data: dict, url: str, callback=None):
    """
    Wrapper for the AJAX POST call.

    :param data: The data to be submitted.
    :param data: Any
    :param url: The part of the URL that is being requested.
    :type url: str
    :param callback: Function to be called when the AJAX request is complete.
    :type callback: function, optional
    """
    req = ajax.ajax()  # pylint: disable=no-value-for-parameter
    if callback is not None:
        req.bind("complete", callback)
    mylog.warning("Calling POST /api%s with data: %r", url, data)
    req.open("POST", url, True)
    req.set_header("content-type", AJAX_URL_ENCODING)
    req.send(data)


def delete(url: str, callback=None):
    """
    Wrapper for the AJAX Data call.

    :param url: The part of the URL that is being requested.
    :type url: str
    :param callback: Function to be called when the AJAX request is complete.
    :type callback: function, optional
    """
    req = ajax.ajax()  # pylint: disable=no-value-for-parameter
    if callback is not None:
        req.bind("complete", callback)
    # pass the arguments in the query string
    req.open("DELETE", url)
    req.set_header("content-type", AJAX_URL_ENCODING)
    req.send()


def populate_canvas(deck, target_canvas, deck_type="player"):
    """
    Populate given canvas with the deck of cards but without specific placement.

    :param deck: card names in the format that svg-cards.svg wants.
    :type deck: list
    :param target_canvas: [description]
    :type target_canvas: [type]
    """
    mylog.error(
        "Entering populate_canvas(deck=%s target_canvas=%s deck_type=%s).",
        deck,
        target_canvas,
        deck_type,
    )

    # DOM ID Counters
    counter = 0

    # TODO: Need a "bury" display for bid winner.
    for card_value in deck:
        flippable = False
        movable = True
        show_face = True
        if "player" in deck_type:
            flippable = PLAYER_DECK_CONFIG[GAME_MODE]["flippable"]
            movable = PLAYER_DECK_CONFIG[GAME_MODE]["movable"]
        elif "kitty" in deck_type:
            show_face = OTHER_DECK_CONFIG[GAME_MODE]["show_face"]
            flippable = round_bid_winner
            movable = OTHER_DECK_CONFIG[GAME_MODE]["movable"]
        elif "meld" in deck_type or "trick" in deck_type:
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
        if False and "trick" in deck_type:
            # TODO: This needs to start with the player who won the bid or the last trick.
            mylog.warning("%s %s", counter, player_dict[PLAYER_ID]["name"])
            text = TextObject(
                f"{player_dict[PLAYER_ID]['name']}",
                fontsize=24,
                objid=f"t_{deck_type}{counter}",
            )
            target_canvas.addObject(text, fixed=True)
        counter += 1


def calculate_y(location: str) -> (float, float):
    """
    Calculate how far to move each card vertically then based on that,
    calculate the starting vertical position.

    :param location: Text description of the location of the cards being
                    placed: top, bottom, or something else for middle.
    :type location: str
    :return: A tuple containing the Y-starting position and Y-increment.
    :rtype: tuple(float, float)
    """
    # Calculate relative vertical overlap for cards, if needed.
    yincr = int(card_height / 4)

    # Where to vertically place first card on the table
    if location.lower() == "top":
        start_y = 0
    elif location.lower() == "bottom":
        # Place cards one card height above the bottom, plus "a bit."
        start_y = table_height - card_height * 1.25
        # Keep the decks relatively close together.
        if start_y > card_height * 2.5:
            start_y = card_height * 2.5 + card_height / 20
    else:
        # Place cards in the middle.
        start_y = table_height / 2 - card_height / 2
        start_y = min(start_y, card_height * 2)
    return start_y, yincr


def calculate_x(deck: list) -> (float, float):
    """
    Calculate how far to move each card horizontally then based on that,
    calculate the starting horizontal position.

    :param deck: card names in the format that svg-cards.svg wants.
    :type deck: list
    :return: A tuple containing the Y-starting position and Y-increment.
    :rtype: tuple(float, float)
    """
    xincr = int(table_width / (len(deck) + 0.5))  # Spacing to cover entire width
    start_x = 0
    mylog.warning("place_cards: Calculated: xincr=%f, start_x=%f", xincr, start_x)
    if xincr > card_width:
        xincr = int(card_width)
        # Start deck/2 cards from table's midpoint horizontally
        start_x = int(table_width / 2 - xincr * (float(len(deck))) / 2)
        mylog.warning(
            "place_cards: Reset to card_width: xincr=%f, start_x=%f", xincr, start_x
        )
    if xincr < int(
        card_width / 20
    ):  # Make sure at least the value of the card is visible.
        xincr = int(card_width / 20)

    return start_x, xincr


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
    mylog.error("Entering place_cards(deck=%s, deck_type=%s).", deck, deck_type)

    # Determine the starting point and step size for the location and deck being placed.
    start_y, yincr = calculate_y(location=location)
    start_x, xincr = calculate_x(deck)

    # Set the initial position
    xpos = start_x
    ypos = start_y
    mylog.warning("place_cards: Start position: (%f, %f)", xpos, ypos)

    # Iterate over canvas's child nodes and move any node
    # where deck_type matches the node's id
    for node in [
        x for (objid, x) in target_canvas.objectDict.items() if deck_type in objid
    ]:
        if not isinstance(node, UseObject):
            continue

        mylog.warning(
            "place_cards: Processing node %s. (xpos=%f, ypos=%f)", node.id, xpos, ypos
        )

        # Move the node into the new position.
        # NOTE: setPosition takes a tuple, so the double parenthesis are necessary.
        node.setPosition((xpos, ypos))

        # Each time through the loop, move the next card's starting position.
        xpos += xincr
        if xpos > table_width - xincr:
            mylog.warning("place_cards: Exceeded x.max, resetting position. ")
            mylog.warning(
                "    (xpos=%f, table_width=%f, xincr=%f", xpos, table_width, xincr,
            )
            xpos = xincr
            ypos += yincr


def calculate_dimensions():
    """
    Run setDimensions and set global variables on demand.
    """
    global table_width, table_height  # pylint: disable=global-statement, invalid-name
    # Gather information about the display environment
    (table_width, table_height) = canvas.setDimensions()


def create_game_select_buttons(xpos, ypos) -> bool:
    mylog.warning("create_game_select_buttons: game_dict=%s", game_dict)
        if game_dict == {}:
            no_game_button = SVG.Button(
                position=(xpos, ypos),
                size=(450, 35),
                text="No games found, create one and press here.",
                onclick=lambda x: get("/game", on_complete_games),
                fontsize=18,
                objid="nogame",
            )
            canvas.attach(no_game_button)
            added_button = True
        else:
            canvas.deleteAll()
        for item in game_dict:
        mylog.warning("create_game_select_buttons: game_dict item: item=%s", item)
            game_button = SVG.Button(
                position=(xpos, ypos),
                size=(450, 35),
                text=f"Game: {game_dict[item]['timestamp'].replace('T',' ')}",
                onclick=choose_game,
                fontsize=18,
                objid=item,
            )
            canvas.attach(game_button)
            added_button = True
            ypos += 40
    return added_button


def create_player_select_buttons(xpos, ypos) -> bool:
        for item in player_dict:
            mylog.warning("player_dict[item]=%s", player_dict[item])
        player_button = SVG.Button(
                position=(xpos, ypos),
                size=(450, 35),
                text=f"Player: {player_dict[item]['name']}",
                onclick=choose_player,
                fontsize=18,
                objid=player_dict[item]["player_id"],
            )
        mylog.warning("create_player_select_buttons: player_dict item: item=%s", item)
        canvas.attach(player_button)
            ypos += 40
            added_button = True
    return added_button


def display_game_options():
    """
    Conditional ladder for early game data selection. This needs to be done better and
    have new game/team/player capability.
    """
    added_button = False
    xpos = 10
    ypos = 0
    # Grab the game_id, team_ids, and players. Display and allow player to choose.
    if GAME_ID == "":
        added_button = create_game_select_buttons(xpos, ypos)
    elif ROUND_ID == "":
        # Open the websocket if needed.
        if WEBSOCKET is None:
            ws_open()

        get(f"/game/{GAME_ID}/round", on_complete_rounds)
    elif team_list == []:
        get(f"/round/{ROUND_ID}/teams", on_complete_teams)
    elif PLAYER_ID == "":
        added_button = create_player_select_buttons(xpos, ypos)
    else:
        # Display the player's name in the UI
        if player_dict != {} and PLAYER_ID in player_dict:
            mylog.warning("Players: %r", player_dict)

            document.getElementById("player_name").clear()
            document.getElementById("player_name").attach(
                html.BIG(player_dict[PLAYER_ID]["name"].capitalize())
            )
            # TODO: Do something more useful like a line of names with color change when
            # the player's client registers.
            document.getElementById("player_name").attach(html.BR())
            document.getElementById("player_name").attach(
                html.SMALL(
                    ", ".join(
                        y["name"].capitalize()
                        for y in [player_dict[x] for x in player_dict if x != PLAYER_ID]
                    )
                )
            )
        # Send the registration message.
        send_registration()

        if GAME_MODE == 0:
            mylog.warning("KITTY_SIZE=%d", KITTY_SIZE)
            advance_mode()

    try:
        if added_button:
            canvas.fitContents()
    except AttributeError:
        pass


def update_display(event=None):  # pylint: disable=unused-argument
    """
    Populate and place cards based on the game's current mode. This needs a little more
    work to support more aspects of the game.

    :param event: The event object passed in during callback, defaults to None
    :type event: [type], optional
    """
    global GAME_MODE  # pylint: disable=global-statement
    mode = GAME_MODES[GAME_MODE]
    mylog.error("Entering update_display. (mode=%s)", mode)
    calculate_dimensions()

    # Place the desired decks on the display.
    if not canvas.objectDict:
        if mode in ["game"] and GAME_ID == "":  # Choose game, player
            display_game_options()
        if mode in ["bid", "bidfinal"]:  # Bid
            # Use empty deck to prevent peeking at the kitty.
            populate_canvas(kitty_deck, canvas, "kitty")
            populate_canvas(players_hand, canvas, "player")
        if mode in ["bidfinal"]:  # Bid submitted
            # The kitty doesn't need to remain 'secret' now that the bidding is done.
            get(f"/round/{ROUND_ID}/kitty", on_complete_kitty)
        elif mode in ["reveal"]:  # Reveal
            # Ask the server for the cards in the kitty.
            populate_canvas(kitty_deck, canvas, "kitty")
            populate_canvas(players_hand, canvas, "player")
        elif mode in ["meld"]:  # Meld
            # TODO: IF bid winner, need way to select trump & communicate with other players - BEFORE they have the chance to choose / submit their meld.
            # TODO: Add a score meld button to submit temporary deck and retrieve and display a numerical score, taking into account trump.
            populate_canvas(meld_deck, canvas, GAME_MODES[GAME_MODE])
            populate_canvas(players_meld_deck, canvas, "player")
        elif mode in ["trick"]:  # Trick
            populate_canvas(discard_deck, canvas, GAME_MODES[GAME_MODE])
            populate_canvas(players_hand, canvas, "player")

    # Last-drawn are on top (z-index wise)
    # TODO: Add buttons/input for this player's meld.
    # TODO: Figure out how to convey the bidding process across the players.
    # TODO: Retrieve events from API to show kitty cards when they are flipped over.
    if mode in ["bid", "bidfinal", "reveal"]:  # Bid & Reveal
        place_cards(kitty_deck, canvas, location="top", deck_type="kitty")
        place_cards(players_hand, canvas, location="bottom", deck_type="player")
    elif mode in ["meld"]:  # Meld
        # TODO: Expand display to show all four players.
        # TODO: Retrieve events from API to show other player's meld.
        place_cards(meld_deck, canvas, location="top", deck_type=mode)
        place_cards(players_meld_deck, canvas, location="bottom", deck_type="player")
    elif mode in ["trick"]:  # Trick
        # TODO: Retrieve/send events from API to show cards as they are played.
        place_cards(discard_deck, canvas, location="top", deck_type=mode)
        place_cards(players_hand, canvas, location="bottom", deck_type="player")

    # try:
    #     canvas.fitContents()
    # except AttributeError:
    #     pass
    canvas.mouseMode = SVG.MouseMode.DRAG


def clear_display(event=None):  # pylint: disable=unused-argument
    """
    Clear the display by removing everything from the canvas object, the canvas object
    itself, then re-adding everything back. It also works for the initial creation and
    addition of the canvas to the overall DOM.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    global button_advance_mode, canvas  # pylint: disable=global-statement, invalid-name
    mode = GAME_MODES[GAME_MODE]
    mylog.error("Entering clear_display (mode=%s)", mode)
    try:
        document.getElementById("canvas").remove()
    except AttributeError:
        pass
    mylog.warning("Destroying canvas with mode: %s", canvas.attrs["mode"])
    canvas.deleteAll()

    # Create the base SVG object for the card table.
    canvas = SVG.CanvasObject("95vw", "90vh", None, objid="canvas")
    canvas.attrs["mode"] = mode

    # Attach the new canvas to the card_table div of the document.
    CardTable <= canvas  # pylint: disable=pointless-statement
    calculate_dimensions()
    update_display()

    # Update buttons
    if GAME_MODE > 0:  # Only display buttons when there are cards.
        half_table = table_width / 2 - 35

        # Button to call advance_mode on demand
        button_advance_mode = SVG.Button(
            position=(half_table - 80 * 3, -40),
            size=(70, 35),
            text=GAME_MODES[GAME_MODE].capitalize(),
            onclick=advance_mode,
            fontsize=18,
            objid="button_advance_mode",
        )

        # Button to call update_display on demand
        button_refresh = SVG.Button(
            position=(half_table - 80 * 2, -40),
            size=(70, 35),
            text="Refresh",
            onclick=update_display,
            fontsize=18,
            objid="button_refresh",
        )

        # Button to call clear_display on demand
        button_clear = SVG.Button(
            position=(half_table - 80 * 1, -40),
            size=(70, 35),
            text="Clear",
            onclick=clear_display,
            fontsize=18,
            objid="button_clear",
        )

        # Button to call submit_meld on demand
        button_send_meld = SVG.Button(
            position=(half_table, -40),
            size=(70, 35),
            text="Send\nMeld",
            onclick=send_meld,
            fontsize=16,
            objid="button_send_meld",
        )

        # Button to call clear_game on demand
        button_clear_game = SVG.Button(
            position=(half_table + 80 * 1, -40),
            size=(70, 35),
            text="Clear\nGame",
            onclick=clear_game,
            fontsize=16,
            objid="button_clear_game",
        )

        # Button to call clear_player on demand
        button_clear_player = SVG.Button(
            position=(half_table + 80 * 2, -40),
            size=(70, 35),
            text="Clear\nPlayer",
            onclick=clear_player,
            fontsize=16,
            objid="button_clear_player",
        )

        # Button to call window reload on demand
        button_reload_page = SVG.Button(
            position=(half_table + 80 * 3, -40),
            size=(70, 35),
            text="Reload",
            onclick=window.location.reload,
            fontsize=16,
            objid="button_reload_page",
        )

        start_y, yincr = calculate_y(location="bottom")
        # Button to call sort_player_cards on demand
        button_sort_player = SVG.Button(
            position=(half_table, start_y - yincr * 0.75),
            size=(70, 35),
            text="Sort",
            onclick=sort_player_cards,
            fontsize=18,
            objid="button_sort_player",
        )

        canvas.addObject(button_sort_player)

        for item in [
            button_clear,
            button_refresh,
            button_advance_mode,
            button_clear_game,
            button_clear_player,
            button_reload_page,
        ]:
            canvas.addObject(item)

        # canvas.translateObject(button_clear, (half_table - 80 * 1, -40))
        # canvas.translateObject(button_refresh, (half_table - 80 * 2, -40))
        # canvas.translateObject(button_advance_mode, (half_table - 80 * 3, -40))
        # canvas.translateObject(button_clear_game, (half_table + 80 * 1, -40))
        # canvas.translateObject(button_clear_player, (half_table + 80 * 2, -40))
        # canvas.translateObject(button_reload_page, (half_table + 80 * 3, -40))
    if GAME_MODES[GAME_MODE] in ["meld"]:
        canvas.addObject(button_send_meld)
        # canvas.translateObject(button_send_meld, (table_width / 2 - 35, -40))

    try:
        canvas.fitContents()
    except AttributeError:
        pass
    canvas.mouseMode = SVG.MouseMode.DRAG


def advance_mode(event=None):  # pylint: disable=unused-argument
    """
    Routine to advance the game mode locally. This should be temporary as the game mode
    should be determined and maintained on the server. It can be called directly or via
    callback from an event.

    :param event: The event object passed in during callback, defaults to None
    :type event: [type], optional
    """
    global GAME_MODE  # pylint: disable=global-statement
    mylog.error(
        "Entering advance_mode (mode=%s->%s)",
        GAME_MODES[GAME_MODE],
        GAME_MODES[(GAME_MODE + 1) % len(GAME_MODES)],
    )
    GAME_MODE = (GAME_MODE + 1) % len(GAME_MODES)
    # Skip over 'choose game & player' mode when already playing a game.
    if GAME_MODE == 0:
        # TODO: Close out current round and...
        # TODO: Create new round & deal cards...
        GAME_MODE += 1
    button_advance_mode.label.textContent = GAME_MODES[GAME_MODE].capitalize()
    clear_display()


def sort_player_cards(event=None):  # pylint: disable=unused-argument
    """
    Sort the player's cards.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    players_hand.sort(
        key=lambda x: DECK_SORTED.index(x)  # pylint: disable=unnecessary-lambda
    )
    players_meld_deck.sort(
        key=lambda x: DECK_SORTED.index(x)  # pylint: disable=unnecessary-lambda
    )
    clear_display()


def send_meld(event=None):  # pylint: disable=unused-argument
    """
    Send the meld deck to the server.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    card_string = ",".join(x for x in meld_deck if x != "card-base")

    mylog.warning(
        "/round/%s/score_meld?player_id=%s&cards=%s", ROUND_ID, PLAYER_ID, card_string
    )

    get(
        f"/round/{ROUND_ID}/score_meld?player_id={PLAYER_ID}&cards={card_string}",
        on_complete_get_meld_score,
    )


def clear_game(event=None):  # pylint: disable=unused-argument
    """
    Request the game cookie be cleared.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    get("/setcookie/game_id/clear", on_complete_set_gamecookie)
    get("/setcookie/player_id/clear", on_complete_set_playercookie)


def clear_player(event=None):  # pylint: disable=unused-argument
    """
    Request the player cookie be cleared.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    get(f"/setcookie/player_id/clear", on_complete_set_playercookie)


def choose_game(event=None):
    """
    Callback for a button press of the choose game button.

    :param event: The event object passed in during callback, defaults to None
    :type event: [type], optional
    """
    try:
        game_to_be = event.currentTarget.id
        get(f"/setcookie/game_id/{game_to_be}", on_complete_set_gamecookie)
        mylog.warning("choose_game: GAME_ID will be %s", game_to_be)
    except AttributeError:
        return


def choose_player(event=None):
    """
    Callback for a button press of the choose player button.

    :param event: The event object passed in during callback, defaults to None
    :type event: [type], optional
    """
    try:
        player_to_be = event.currentTarget.id
        get(f"/setcookie/player_id/{player_to_be}", on_complete_set_playercookie)
        get(f"/player/{player_to_be}/hand", on_complete_player_cards)
        mylog.warning("choose_player: PLAYER_ID will be %s", player_to_be)
    except AttributeError:
        return


## END Function definitions.

# Make the update_display function easily available to scripts.
window.clear_display = clear_display

# Locate the card table in the HTML document.
CardTable = document["card_table"]

# Attach the card graphics file
document["card_definitions"].attach(SVG.Definitions(filename=CARD_URL))

# Create the base SVG object for the card table.
canvas = SVG.CanvasObject("95vw", "90vh", None, objid="canvas")
calculate_dimensions()
canvas.attrs["mode"] = "initial"

# See if some steps can be bypassed because we refreshed in the middle of the game.
get("/game", on_complete_games)
get("/getcookie/game_id", on_complete_getcookie)
get("/getcookie/player_id", on_complete_getcookie)

# TODO: Add buttons & display to facilitate bidding. Tie into API.

# Collect cards into discard, kitty and player's hand
discard_deck = ["card-base" for _ in range(PLAYERS)]

# TODO: Figure out how better to calculate HAND_SIZE.
HAND_SIZE = int(48 / PLAYERS)
meld_deck = ["card-base" for _ in range(HAND_SIZE)]

document.getElementById("please_wait").remove()
clear_display()
