"""
In-browser script to handle the card-table user interface.
"""
import copy
import json
import logging

import brySVG.dragcanvas as SVG  # pylint: disable=import-error
from browser import ajax, document, window
from brySVG.dragcanvas import TextObject, UseObject  # pylint: disable=import-error

from constants import (
    CARD_URL,
    GAME_MODES,
    OTHER_DECK_CONFIG,
    PLAYER_DECK_CONFIG,
)

# TODO: Kitty cards in 'reveal' mode need to be non-flippable for all but the bid winner.
# TODO: Retrieve current game state from API
# TODO: Set a cookie for the game & player so that the game mode can be skipped
#       once chosen by the user.
GAME_MODE = 0

# Programmatically create a pre-sorted deck to compare to when sorting decks of cards.
# Importing a statically-defined constant from constants doesn't work for some reason.
DECK_SORTED = []
for _suit in ["spade", "diamond", "club", "heart"]:
    for _card in ["9", "jack", "queen", "king", "10", "ace"]:
        DECK_SORTED.append(f"{_suit}_{_card}")

mylog = logging.getLogger("cardtable")
mylog.setLevel(logging.WARNING)

# API "Constants"
GAME_ID = ""
KITTY_SIZE = 0
PLAYER_ID = ""
PLAYERS = 4
ROUND_ID = ""
TEAM_ID = ""

game_dict = {}
kitty_deck = []
player_dict = {}
players_hand = []
players_meld_deck = []
team_dict = {}
team_list = []

table_width = 0  # pylint: disable=invalid-name
table_height = 0  # pylint: disable=invalid-name

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
        flippable=None,
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
        obj = self
        new_y = table_height

        # The object already has the correct 'Y' value from the move.
        if "touch" in event.type or "click" in event.type:
            new_y = float(obj.attrs["y"])
            mylog.warning(
                "PlayingCard.play_handler: Touch event: obj.id=%s new_y=%f",
                obj.id,
                new_y,
            )

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
            mylog.warning(
                "PlayingCard.play_handler: Mouse event: obj.id=%s new_y=%f",
                obj.id,
                new_y,
            )

        # Determine whether the card is now in a position to be considered thrown.
        if new_y >= card_height and "click" not in event.type:
            # New Y is greater than one card_height from the top.
            return  # Not thrown.

        mylog.warning(
            "PlayingCard.play_handler: Throwing obj.id=%s (obj.face_value=%s) obj.canvas=%s",
            obj.id,
            obj.face_value,
            obj.canvas,
        )
        parent_canvas = obj.canvas
        card_tag = GAME_MODES[GAME_MODE]

        # Protect the player's deck during meld process.
        # Create a reference to the appropriate deck by mode.
        receiving_deck = []
        # This "should never be called" during GAME_MODEs 0 or 1.
        add_only = False
        if GAME_MODES[GAME_MODE] in ["meld"]:  # Meld
            if True or "player" in obj.id:
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

        :param event: The event object passed in during callback, defaults to None
        :type event: Event(?), optional
        """
        global players_hand, players_meld_deck  # pylint: disable=global-statement, invalid-name
        mylog.error("Entering PlayingCard.card_click_handler()")
        if event and "click" in event.type:
            if (
                GAME_MODES[GAME_MODE] in ["bid", "bidfinal", "reveal"]
                and self.flippable
            ):
                self.show_face = not self.show_face
                self.flippable = False
                # TODO: Call game API to notify the other players this particular card was
                # flipped over and add it to the player's hand.
                players_hand.append(self.face_value)
                players_meld_deck.append(self.face_value)
                self.face_update_dom()
            if GAME_MODES[GAME_MODE] == ["meld"]:
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
    mylog.warning("on_complete_teams: team_list=%s", team_list)

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
    team_dict[temp["team_id"]] = temp
    mylog.warning("on_complete_team_names: team_dict=%s", team_dict)
    display_game_options()


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

    # Set the global deck of cards for the player's hand.
    player_dict[temp["player_id"]] = temp
    mylog.warning("In on_complete_players: player_dict=%s", player_dict)
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

    advance_mode()
    update_display()


def on_complete_common(req):
    """
    Common function for AJAX callbacks.

    :param req: Request object from callback.
    :type req: [type]
    :return: Object returned in the request as decoded by JSON.
    :rtype: [type]
    """
    mylog.error("In on_complete_common.")
    if req.status == 200 or req.status == 0:
        temp = json.loads(req.text)
        return temp
    else:
        mylog.warning("on_complete_common: req=%s", req)


def get(url, callback):
    """
    Wrapper for the AJAX GET call.

    :param url: The part of the URL that is being requested.
    :type url: str
    :param callback: Function to be called when the AJAX request is complete.
    :type callback: function
    """
    req = ajax.ajax()
    req.bind("complete", callback)
    mylog.warning("Calling GET /api%s", url)
    req.open("GET", "/api" + url, True)
    req.set_header("content-type", "application/x-www-form-urlencoded")
    req.send()


# def put(url):
#     req = ajax.ajax()
#     a = doc['A'].value
#     b = doc['B'].value
#     req.bind('complete',on_complete)
#     req.open('PUT',url,True)
#     req.set_header('content-type','application/x-www-form-urlencoded')
#     req.send({"a": a, "b":b})


# def post(url):
#     req = ajax.ajax()
#     a = doc['A'].value
#     b = doc['B'].value
#     req.bind('complete',on_complete)
#     req.open('POST',url,True)
#     req.set_header('content-type','application/x-www-form-urlencoded')
#     req.send({"a": a, "b":b})


# def delete(url):
#     req = ajax.ajax()
#     a = doc['A'].value
#     b = doc['B'].value
#     req.bind('complete',on_complete)
#     # pass the arguments in the query string
#     req.open('DELETE',url+"?a=%s&b=%s" %(a, b),True)
#     req.set_header('content-type','application/x-www-form-urlencoded')
#     req.send()


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
        # if not isinstance(node, PlayingCard):
        if not node.setPosition:
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


def display_game_options():
    """
    Conditional ladder for early game data selection. This needs to be done better and
    have new game/team/player capability.
    """
    global canvas, game_dict, player_dict, team_list, team_dict  # pylint: disable=global-statement, invalid-name

    xpos = 10
    ypos = 0
    # Grab the game_id, team_ids, and players. Display and allow player to choose.
    if GAME_ID == "":
        mylog.warning("display_game_options: game_dict=%s", game_dict)
        for item in game_dict:
            mylog.warning("display_game_options: game_dict item: item=%s", item)
            game_button = SVG.Button(
                position=(xpos, ypos),
                size=(450, 35),
                text=f"Game: {game_dict[item]['timestamp'].replace('T',' ')}",
                onclick=choose_game,
                fontsize=18,
                objid=item,
            )
            canvas <= game_button  # pylint: disable=pointless-statement
            ypos += 40
    elif ROUND_ID == "":
        get(f"/game/{GAME_ID}/round", on_complete_rounds)
    elif team_list == []:
        get(f"/round/{ROUND_ID}/teams", on_complete_teams)
    elif player_dict == {}:
        for team in team_dict:
            for item in team_dict[team]["player_ids"]:
                get(f"/player/{item}", on_complete_players)
    elif PLAYER_ID == "":
        clear_display()
        for item in player_dict:
            mylog.warning("player_dict[item]=%s", player_dict[item])
            round_button = SVG.Button(
                position=(xpos, ypos),
                size=(450, 35),
                text=f"Player: {player_dict[item]['name']}",
                onclick=choose_player,
                fontsize=18,
                objid=player_dict[item]["player_id"],
            )
            mylog.warning("display_game_options: player_dict item: item=%s", item)
            canvas <= round_button  # pylint: disable=pointless-statement
            ypos += 40

    canvas.fitContents()


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

    # TODO: If there is no kitty in this game, don't bother showing the kitty
    # deck during bid process.

    # Place the desired decks on the display.
    if not canvas.objectDict:
        if mode in ["game"] and GAME_ID == "":  # Choose game, player
            get("/game", on_complete_games)
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


def clear_display(event=None):  # pylint: disable=unused-argument
    """
    Clear the display by removing everything from the canvas object, the canvas object
    itself, then re-adding everything back. It also works for the initial creation and
    addition of the canvas to the overall DOM.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    global canvas  # pylint: disable=global-statement, invalid-name
    mode = GAME_MODES[GAME_MODE]
    mylog.error("Entering clear_display (mode=%s)", mode)
    try:
        document.getElementById("canvas").remove()
    except AttributeError:
        pass
    mylog.warning("Destroying canvas with mode: %s", canvas.attrs["mode"])
    canvas.deleteAll()

    # Create the base SVG object for the card table.
    canvas = SVG.CanvasObject("95vw", "95vh", None, objid="canvas")
    canvas.attrs["mode"] = mode

    # Attach the new canvas to the card_table div of the document.
    CardTable <= canvas  # pylint: disable=pointless-statement
    calculate_dimensions()
    update_display()

    # Update buttons
    if GAME_MODE > 0:  # Only display sort cards button when there are cards.
        canvas.addObject(button_sort_player)
    canvas.addObject(button_clear)
    canvas.addObject(button_refresh)
    canvas.addObject(button_advance_mode)

    canvas.fitContents()
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
    global players_hand, players_meld_deck  # pylint: disable=global-statement, invalid-name
    players_hand.sort(
        key=lambda x: DECK_SORTED.index(x)  # pylint: disable=unnecessary-lambda
    )
    players_meld_deck.sort(
        key=lambda x: DECK_SORTED.index(x)  # pylint: disable=unnecessary-lambda
    )
    clear_display()


def choose_game(event=None):
    """
    Callback for a button press of the choose game button.

    :param event: The event object passed in during callback, defaults to None
    :type event: [type], optional
    """
    global GAME_ID, KITTY_SIZE, kitty_deck  # pylint: disable=global-statement, invalid-name
    GAME_ID = event.currentTarget.id
    KITTY_SIZE = game_dict[GAME_ID]["kitty_size"]
    mylog.warning("choose_game: GAME_ID=%s", GAME_ID)
    mylog.warning("choose_game: KITTY_SIZE=%s", KITTY_SIZE)
    kitty_deck = ["card-base" for _ in range(KITTY_SIZE)]
    display_game_options()


def choose_player(event=None):
    """
    Callback for a button press of the choose player button.

    :param event: The event object passed in during callback, defaults to None
    :type event: [type], optional
    """
    global PLAYER_ID, TEAM_ID  # pylint: disable=global-statement

    PLAYER_ID = event.currentTarget.id
    mylog.warning("choose_player: PLAYER_ID=%s", PLAYER_ID)

    # Set the TEAM_ID variable based on the player id chosen.
    for _temp in team_dict:
        mylog.warning("Key: %s Value: %r", _temp, team_dict[_temp]["player_ids"])
        if PLAYER_ID in team_dict[_temp]["player_ids"]:
            TEAM_ID = team_dict[_temp]["team_id"]
    mylog.warning(
        "In choose_player: TEAM_ID=%s, Team name: %s",
        TEAM_ID,
        team_dict[TEAM_ID]["team_name"],
    )

    get(f"/player/{PLAYER_ID}/hand", on_complete_player_cards)
    display_game_options()


# Make the update_display function easily available to scripts.
window.update_display = update_display
window.clear_display = clear_display
window.advance_mode = advance_mode

# Locate the card table in the HTML document.
CardTable = document["card_table"]

# Attach the card graphics file
document[  # pylint: disable=pointless-statement, expression-not-assigned
    "card_definitions"
] <= SVG.Definitions(filename=CARD_URL)

# Create the base SVG object for the card table.
canvas = SVG.CanvasObject("95vw", "95vh", None, objid="canvas")
calculate_dimensions()
canvas.attrs["mode"] = "initial"

# TODO: Add buttons & display to facilitate bidding. Tie into API.

# Collect cards into discard, kitty and player's hand
discard_deck = ["card-base" for _ in range(PLAYERS)]

# TODO: Figure out how better to calculate HAND_SIZE.
HAND_SIZE = int(48 / PLAYERS)
meld_deck = ["card-base" for _ in range(HAND_SIZE)]

# Button to call clear_display on demand
button_advance_mode = SVG.Button(
    position=(-70, 0),
    size=(70, 35),
    text=GAME_MODES[GAME_MODE].capitalize(),
    onclick=advance_mode,
    fontsize=18,
    objid="button_advance_mode",
)

# Button to call update_display on demand
button_refresh = SVG.Button(
    position=(-70, 40),
    size=(70, 35),
    text="Refresh",
    onclick=update_display,
    fontsize=18,
    objid="button_refresh",
)

# Button to call clear_display on demand
button_clear = SVG.Button(
    position=(-70, 80),
    size=(70, 35),
    text="Clear",
    onclick=clear_display,
    fontsize=18,
    objid="button_clear",
)

# Button to call sort_player_cards on demand
button_sort_player = SVG.Button(
    position=(-70, card_height * 2),
    size=(70, 35),
    text="Sort",
    onclick=sort_player_cards,
    fontsize=18,
    objid="button_sort_player",
)

mylog.critical("Critical... %d", mylog.getEffectiveLevel())
mylog.error("Error...")
mylog.warning("Warning...")
mylog.warning("Info...")
mylog.debug("Debug...")
document.getElementById("please_wait").remove()
clear_display()
