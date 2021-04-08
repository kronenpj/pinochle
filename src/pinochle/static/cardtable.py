"""
In-browser script to handle the card-table user interface.
"""
import copy
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import brySVG.dragcanvas as SVG  # pylint: disable=import-error
from browser import ajax, document, html, websocket, window
from browser.widgets.dialog import InfoDialog

from constants import CARD_HEIGHT, CARD_URL, CARD_WIDTH, DECK_CONFIG, GAME_MODES

# pylint: disable=global-statement

# Websocket holder
g_websocket: Optional[websocket.WebSocket] = None

# Programmatically create a pre-sorted deck to compare to when sorting decks of cards.
# Importing a statically-defined list from constants doesn't work for some reason.
# "9", "jack", "queen", "king", "10", "ace"
# "ace", "10", "king", "queen", "jack", "9"
DECK_SORTED: List[str] = []
for _suit in ["spade", "diamond", "club", "heart"]:
    for _card in ["ace", "10", "king", "queen", "jack", "9"]:
        DECK_SORTED.append(f"{_suit}_{_card}")

mylog = logging.getLogger("cardtable")
mylog.setLevel(logging.CRITICAL)  # No output
# mylog.setLevel(logging.ERROR)  # Function entry/exit
# mylog.setLevel(logging.WARNING)  # Everything

# API "Constants"
AJAX_URL_ENCODING = "application/x-www-form-urlencoded"
g_game_id: str = ""
g_game_mode: Optional[int] = None
g_kitty_size: int = 0
g_player_id: str = ""
g_players: int = 4
g_round_id: str = ""
g_team_id: str = ""

# Various state globals
g_game_dict: Dict[str, Dict[str, Any]] = {}
g_kitty_deck: List[str] = []
g_ajax_outstanding_requests: int = 0
g_player_dict: Dict[str, Dict[str, str]] = {}
g_players_hand: List[str] = []
g_players_meld_deck: List[str] = []
g_team_dict: Dict[str, Dict[str, str]] = {}
g_team_list: List[str] = []

# Track whether this user is the round's bid winner.
g_round_bid_winner = False  # pylint: disable=invalid-name

g_table_width = 0  # pylint: disable=invalid-name
g_table_height = 0  # pylint: disable=invalid-name
button_advance_mode = None  # pylint: disable=invalid-name
g_registered_with_server = False  # pylint: disable=invalid-name


class PlayingCard(SVG.UseObject):
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
        SVG.UseObject.__init__(self, href=href, objid=objid)
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
            "Entering PlayingCard.move_handler: %s, %s",
            self.attrs["y"],
            self.style["transform"],
        )

        # Moving a card within a CARD_HEIGHT of the top "throws" that card.
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
        new_y = g_table_height

        # The object already has the correct 'Y' value from the move.
        if "touch" in event.type or "click" in event.type:
            new_y = float(self.attrs["y"])
            mylog.warning(
                "PlayingCard.play_handler: Touch event: id=%4.2s new_y=%4.2f",
                self.id,
                new_y,
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
                "PlayingCard.play_handler: Mouse event: id=%s new_y=%4.2f",
                self.id,
                new_y,
            )

        # Determine whether the card is now in a position to be considered thrown.
        if new_y >= CARD_HEIGHT and "click" not in event.type:
            # New Y is greater than one CARD_HEIGHT from the top.
            return  # Not thrown.

        mylog.warning(
            "PlayingCard.play_handler: Throwing id=%s (face_value=%s) canvas=%s",
            self.id,
            self.face_value,
            self.canvas,
        )
        parent_canvas = self.canvas
        card_tag = GAME_MODES[g_game_mode]

        # Protect the player's deck during meld process.
        # Create a reference to the appropriate deck by mode.
        receiving_deck = []
        sending_deck = []
        # This "should never be called" during GAME_MODEs 0 or 1.
        add_only = False
        if GAME_MODES[g_game_mode] in ["meld"]:  # Meld
            if True or "player" in self.id:
                sending_deck = g_players_meld_deck  # Deep copy
                receiving_deck = g_meld_deck  # Reference
            else:
                add_only = True
                card_tag = "player"
                sending_deck = meld_deck  # Reference
                receiving_deck = players_meld_deck  # Deep copy
        elif GAME_MODES[g_game_mode] in ["trick"]:  # Trick
            sending_deck = g_players_hand  # Reference
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
        try:
            parent_canvas.deleteObject(self.hitTarget)
        except AttributeError:
            pass
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
        set_card_positions()

    def card_click_handler(self, event=None):
        """
        Click handler for the playing card. The action depends on the game mode.
        Since the only time this is done is during the meld process, also call the API to
        notify it that a kitty card has been flipped over and which card that is.

        :param event: The event object passed in during callback, defaults to None
        :type event: Event(?), optional
        """
        global g_players_hand, g_players_meld_deck  # pylint: disable=invalid-name
        mylog.error("Entering PlayingCard.card_click_handler()")
        if event and "click" in event.type:
            if GAME_MODES[g_game_mode] in ["reveal"] and self.flippable:
                mylog.warning(
                    "PlayingCard.card_click_handler: flippable=%r", self.flippable
                )
                self.show_face = not self.show_face
                self.flippable = False
                # TODO: Call API to notify the other players this particular card was
                # flipped over and add it to the player's hand.
                g_players_hand.append(self.face_value)
                g_players_meld_deck.append(self.face_value)
                self.face_update_dom()
            if GAME_MODES[g_game_mode] in ["meld"]:
                self.play_handler(event)


def dump_globals() -> None:
    variables = {
        # "canvas": canvas,
        # "g_game_id": g_game_id,
        # "g_game_mode": g_game_mode,
        # "g_round_id": g_round_id,
        # "g_team_list": g_team_list,
        # "g_player_id": g_player_id,
        # "g_players_hand": g_players_hand,
        # "g_game_dict": g_game_dict,
        "g_kitty_size": g_kitty_size,
        "g_kitty_deck": g_kitty_deck,
    }
    for var_name, value in variables.items():
        if value is None:
            print(f"dgo: {var_name} is None")
        else:
            print(f"dgo: {var_name}={value} ({type(value)})")


def find_protocol_server():
    """
    Gather information from the environment about the protocol and server name
    from where we're being served.

    :return: Tuple with strings representing protocol and server with port.
    :rtype: (str, str)
    """
    start = os.environ["HOME"].find("//") + 2
    end = os.environ["HOME"].find("/", start=start) + 1
    proto = os.environ["HOME"][: start - 3]
    if end <= start:
        hostname = os.environ["HOME"][start:]
    else:
        hostname = os.environ["HOME"][start:end]

    return (proto, hostname)


def ws_open():
    """
    Open a websocket connection back to the originating server.
    """
    mylog.error("In ws_open.")
    if not websocket.supported:
        InfoDialog("websocket", "WebSocket is not supported by your browser")
        return
    global g_websocket  # pylint: disable=global-statement
    # open a web socket
    proto = PROTOCOL.replace("http", "ws")
    g_websocket = websocket.WebSocket(f"{proto}://{SERVER}/stream")
    # bind functions to web socket events
    g_websocket.bind("open", on_ws_open)
    g_websocket.bind("message", on_ws_event)
    g_websocket.bind("close", on_ws_close)


def on_ws_open(event=None):  # pylint: disable=unused-argument
    """
    Callback for Websocket open event.
    """
    mylog.error("on_ws_open: Connection is open")


def on_ws_close(event=None):  # pylint: disable=unused-argument
    """
    Callback for Websocket close event.
    """
    mylog.error("on_ws_close: Connection has closed")
    global g_websocket  # pylint: disable=global-statement
    g_websocket = None
    # set_timeout(ws_open, 1000)


def on_ws_error(event=None):
    """
    Callback for Websocket error event.
    """
    mylog.error("on_ws_error: Connection has experienced an error")
    mylog.warning("%r", event)


def on_ws_event(event=None):
    """
    Callback for Websocket event from server.

    :param evt: Event object from ws event.
    :type evt: [type]
    """
    mylog.error("In on_ws_event.")
    global g_game_mode  # pylint: disable=invalid-name

    mylog.warning("on_ws_event: %s", event.data)

    if "action" not in event.data:
        return
    if "game_start" in event.data:
        clear_globals_for_round_change()
        put({}, f"/game/{g_game_id}?state=false", game_mode_query_callback, False)
    elif "notification_player_list" in event.data:
        update_player_names(event.data)
    elif "game_state" in event.data:
        g_game_mode = json.loads(event.data)["state"]
        display_game_options()
    elif "meld_update" in event.data:
        display_player_meld(event.data)


def display_player_meld(meld_data: str):
    data = json.loads(meld_data)
    player_name = g_player_dict[str(data["player_id"])]["name"]
    card_list = data["card_list"]
    dialog = InfoDialog("Meld Score", f"{player_name}'s meld cards are:", ok=True)
    try:
        xpos = 0
        d_canvas = SVG.CanvasObject(objid="dialog_canvas")
        dialog.panel <= d_canvas
        for card in card_list:
            d_canvas <= SVG.UseObject(href=f"#{card}", origin=(xpos, 0))
            xpos += CARD_WIDTH / 5.0
    except Exception as e:
        mylog.warning("display_player_meld: Caught exception: %r", e)


def update_player_names(player_data: str):
    """
    Update the player names in the UI.

    :param player_data: JSON-formatted message from the server.
    :type player_data: str
    """
    global g_registered_with_server  # pylint: disable=invalid-name

    data = json.loads(player_data)
    my_player_list = data["player_ids"]
    # Display the player's name in the UI
    if my_player_list != [] and g_player_id in my_player_list:
        mylog.warning("Players: %r", my_player_list)

        g_registered_with_server = True
        document.getElementById("player_name").clear()
        document.getElementById("player_name").attach(
            html.BIG(g_player_dict[g_player_id]["name"].capitalize())
        )

        # TODO: Do something more useful like a line of names with color change when
        # the player's client registers.
        document.getElementById("player_name").attach(html.BR())
        document.getElementById("player_name").attach(
            html.SMALL(
                ", ".join(
                    y["name"].capitalize()
                    for y in [
                        g_player_dict[x] for x in my_player_list if x != g_player_id
                    ]
                )
            )
        )


def send_registration():
    """
    Send registration structure to server.
    """
    mylog.error("In send_registration")
    if g_registered_with_server:
        return

    if g_websocket is None:
        mylog.warning("send_registration: Opening WebSocket.")
        ws_open()

    g_websocket.send(
        json.dumps(
            {
                "action": "register_client",
                "game_id": str(g_game_id),
                "player_id": str(g_player_id),
            }
        )
    )


def ajax_request_tracker(direction: int = 0):
    """
    Keep a tally of the currently outstanding AJAX requests.

    :param direction: Whether to increase or decrease the counter, defaults to 0 which does not affect the counter.
    :type direction: int, optional
    """
    global g_ajax_outstanding_requests  # pylint: disable=invalid-name

    if direction > 0:
        g_ajax_outstanding_requests += 1
    elif direction < 0:
        g_ajax_outstanding_requests -= 1


def on_complete_games(req: ajax.Ajax):
    """
    Callback for AJAX request for the list of games.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("Entering on_complete_games.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global game list.
    g_game_dict.clear()
    for item in temp:
        mylog.warning("on_complete_games: item=%s", item)
        g_game_dict[item["game_id"]] = item
        # game_list.append(item["game_id"])

    display_game_options()


def on_complete_rounds(req: ajax.Ajax):
    """
    Callback for AJAX request for the list of rounds.

    :param req: Request object from callback.
    :type req: [type]
    """
    global g_round_id, g_team_list  # pylint: disable=invalid-name
    mylog.error("Entering on_complete_rounds.")

    ajax_request_tracker(-1)
    g_team_list.clear()

    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the round ID.
    g_round_id = temp["round_id"]
    mylog.warning("on_complete_rounds: round_id=%s", g_round_id)

    display_game_options()


def on_complete_teams(req: ajax.Ajax):
    """
    Callback for AJAX request for the information on the teams associated with the round.

    :param req: Request object from callback.
    :type req: [type]
    """
    global g_team_list  # pylint: disable=invalid-name
    mylog.error("Entering on_complete_teams.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global list of teams for this round.
    g_team_list.clear()
    g_team_list = temp["team_ids"]
    mylog.warning("on_complete_teams: team_list=%r", g_team_list)

    # Clear the team dict here because of the multiple callbacks.
    g_team_dict.clear()
    for item in g_team_list:
        get(f"/team/{item}", on_complete_team_names)


def on_complete_team_names(req: ajax.Ajax):
    """
    Callback for AJAX request for team information.

    :param req: Request object from callback.
    :type req: [type]
    """
    global g_team_dict  # pylint: disable=invalid-name
    mylog.error("Entering on_complete_team_names.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global dict of team names for this round.
    mylog.warning(
        "on_complete_team_names: Setting team_dict[%s]=%r", temp["team_id"], temp
    )
    g_team_dict[temp["team_id"]] = temp
    mylog.warning("on_complete_team_names: team_dict=%s", g_team_dict)

    # Only call API once per team, per player.
    for item in g_team_dict[temp["team_id"]]["player_ids"]:
        mylog.warning("on_complete_team_names: calling get/player/%s", item)
        get(f"/player/{item}", on_complete_players)


def on_complete_players(req: ajax.Ajax):
    """
    Callback for AJAX request for player information.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("Entering on_complete_players.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global dict of players for reference later.
    g_player_dict[temp["player_id"]] = temp
    mylog.warning("In on_complete_players: player_dict=%s", g_player_dict)
    display_game_options()


def on_complete_set_gamecookie(req: ajax.Ajax):
    """
    Callback for AJAX request for setcookie information.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("Entering on_complete_set_gamecookie.")

    ajax_request_tracker(-1)
    if req.status in [200, 0]:
        get("/getcookie/game_id", on_complete_getcookie)


def on_complete_set_playercookie(req: ajax.Ajax):
    """
    Callback for AJAX request for setcookie information.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("Entering on_complete_set_playercookie.")

    ajax_request_tracker(-1)
    if req.status in [200, 0]:
        get("/getcookie/player_id", on_complete_getcookie)


def on_complete_getcookie(req: ajax.Ajax):
    """
    Callback for AJAX request for setcookie information.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("Entering on_complete_getcookie.")
    global g_game_mode, g_game_id, g_player_id, g_kitty_size, g_team_id, g_kitty_deck  # pylint: disable=invalid-name

    ajax_request_tracker(-1)
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
        g_game_id = response_data["ident"]
        mylog.warning(
            "on_complete_getcookie: Setting GAME_ID=%s", response_data["ident"]
        )
        # put({}, f"/game/{g_game_id}?state=false", advance_mode_initial_callback, False)

        try:
            g_kitty_size = int(g_game_dict[g_game_id]["kitty_size"])
            mylog.warning("on_complete_getcookie: KITTY_SIZE=%s", g_kitty_size)
            if g_kitty_size > 0:
                g_kitty_deck = ["card-base" for _ in range(g_kitty_size)]
            else:
                g_kitty_deck.clear()
        except KeyError:
            pass
    elif "player_id" in response_data["kind"]:
        g_player_id = response_data["ident"]
        mylog.warning(
            "on_complete_getcookie: Setting PLAYER_ID=%s", response_data["ident"]
        )
        get(f"/player/{g_player_id}/hand", on_complete_player_cards)
        # FIXME: This is temporary. The server will decide when to advance the game state.
        # put({}, f"/game/{g_game_id}?state=false", advance_mode_initial_callback)
        # FIXME: This is temporary. The server will decide when to advance the game state.

        # Set the TEAM_ID variable based on the player id chosen.
        for _temp in g_team_dict:
            mylog.warning("Key: %s Value: %r", _temp, g_team_dict[_temp]["player_ids"])
            if g_player_id in g_team_dict[_temp]["player_ids"]:
                g_team_id = g_team_dict[_temp]["team_id"]

    display_game_options()


def on_complete_kitty(req: ajax.Ajax):
    """
    Callback for AJAX request for the round's kitty cards, if any.

    :param req: Request object from callback.
    :type req: [type]
    """
    global g_kitty_deck  # pylint: disable=invalid-name
    mylog.error("Entering on_complete_kitty.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global deck of cards for the kitty.
    g_kitty_deck.clear()
    g_kitty_deck = temp["cards"]
    mylog.warning("on_complete_kitty: kitty_deck=%s", g_kitty_deck)


def on_complete_player_cards(req: ajax.Ajax):
    """
    Callback for AJAX request for the player's cards.

    :param req: Request object from callback.
    :type req: [type]
    """
    global g_players_hand, g_players_meld_deck  # pylint: disable=invalid-name
    mylog.error("Entering on_complete_player_cards.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global deck of cards for the player's hand.
    g_players_hand.clear()
    g_players_meld_deck.clear()
    g_players_hand = [x["card"] for x in temp]
    mylog.warning("on_complete_player_cards: players_hand=%s", g_players_hand)
    g_players_meld_deck = copy.deepcopy(g_players_hand)  # Deep copy

    display_game_options()


def on_complete_get_meld_score(req: ajax.Ajax):
    """
    Callback for AJAX request for the player's meld.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("Entering on_complete_get_meld_score.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    # TODO: Do something with the response.
    if req.status in [200, 0]:
        mylog.warning("on_complete_get_meld_score: req.text: %s", req.text)
        temp = json.loads(req.text)
        InfoDialog("Meld Score", f"Your meld score is {temp['score']}", remove_after=5)
        return temp

    mylog.warning("on_complete_get_meld_score: score: %r", req)


def on_complete_common(req: ajax.Ajax):
    """
    Common function for AJAX callbacks.

    :param req: Request object from callback.
    :type req: [type]
    :return: Object returned in the request as decoded by JSON.
    :rtype: [type]
    """
    mylog.error("Entering on_complete_common.")

    ajax_request_tracker(-1)
    if req.status in [200, 0]:
        return json.loads(req.text)

    mylog.warning("on_complete_common: req=%s", req)


def get(url: str, callback=None, async_call=True):
    """
    Wrapper for the AJAX GET call.

    :param url: The part of the URL that is being requested.
    :type url: str
    :param callback: Function to be called when the AJAX request is complete.
    :type callback: function, optional
    """
    req = ajax.Ajax()
    if callback is not None:
        ajax_request_tracker(1)
        req.bind("complete", callback)
    mylog.warning("Calling GET /api%s", url)
    req.open("GET", "/api" + url, async_call)
    req.set_header("content-type", "application/x-www-form-urlencoded")

    req.send()


def put(data: dict, url: str, callback=None, async_call=True):
    """
    Wrapper for the AJAX PUT call.

    :param data: The data to be submitted.
    :param data: dict
    :param url: The part of the URL that is being requested.
    :type url: str
    :param callback: Function to be called when the AJAX request is complete.
    :type callback: function, optional
    """
    req = ajax.Ajax()
    if callback is not None:
        ajax_request_tracker(1)
        req.bind("complete", callback)
    mylog.warning("Calling PUT /api%s with data: %r", url, data)
    req.open("PUT", "/api" + url, async_call)
    req.set_header("content-type", AJAX_URL_ENCODING)
    # req.send({"a": a, "b":b})
    req.send(data)


def post(data: dict, url: str, callback=None, async_call=True):
    """
    Wrapper for the AJAX POST call.

    :param data: The data to be submitted.
    :param data: Any
    :param url: The part of the URL that is being requested.
    :type url: str
    :param callback: Function to be called when the AJAX request is complete.
    :type callback: function, optional
    """
    req = ajax.Ajax()
    if callback is not None:
        ajax_request_tracker(1)
        req.bind("complete", callback)
    mylog.warning("Calling POST /api%s with data: %r", url, data)
    req.open("POST", "/api" + url, async_call)
    req.set_header("content-type", AJAX_URL_ENCODING)
    req.send(data)


def delete(url: str, callback=None, async_call=True):
    """
    Wrapper for the AJAX Data call.

    :param url: The part of the URL that is being requested.
    :type url: str
    :param callback: Function to be called when the AJAX request is complete.
    :type callback: function, optional
    """
    req = ajax.Ajax()
    if callback is not None:
        ajax_request_tracker(1)
        req.bind("complete", callback)
    # pass the arguments in the query string
    req.open("DELETE", "/api" + url, async_call)
    req.set_header("content-type", AJAX_URL_ENCODING)
    req.send()


def clear_globals_for_round_change():
    global g_round_id, g_team_list, g_players_hand, g_players_meld_deck, g_meld_deck  # pylint: disable=invalid-name
    mylog.error("Entering clear_globals_for_round_change.")

    g_round_id = ""
    g_players_hand.clear()
    g_players_meld_deck.clear()
    g_meld_deck = ["card-base" for _ in range(HAND_SIZE)]
    display_game_options()


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
        if g_game_mode > 0:
            flippable = DECK_CONFIG[deck_type][g_game_mode]["flippable"]
            movable = DECK_CONFIG[deck_type][g_game_mode]["movable"]
            show_face = DECK_CONFIG[deck_type][g_game_mode]["show_face"]
            if "kitty" in deck_type:
                flippable = g_round_bid_winner

        # Add the card to the canvas.
        piece = PlayingCard(
            face_value=card_value,
            objid=f"{deck_type}{counter}",
            show_face=show_face,
            flippable=flippable,
            movable=movable,
        )
        target_canvas.addObject(piece, fixed=not movable)
        if "player" not in deck_type:
            # print("Scaling %r", piece)
            target_canvas.scaleElement(piece, 0.15)
        if False and "trick" in deck_type:
            # TODO: This needs to start with the player who won the bid or the last trick.
            mylog.warning("%s %s", counter, g_player_dict[g_player_id]["name"])
            text = SVG.TextObject(
                f"{g_player_dict[g_player_id]['name']}",
                fontsize=24,
                objid=f"t_{deck_type}{counter}",
            )
            target_canvas.addObject(text, fixed=True)
        counter += 1


def calculate_y(location: str) -> Tuple[float, float]:
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
    yincr = int(CARD_HEIGHT / 4)

    # Where to vertically place first card on the table
    if location.lower() == "top":
        start_y = 0.0
    elif location.lower() == "bottom":
        # Place cards one card height above the bottom, plus "a bit."
        start_y = g_table_height - CARD_HEIGHT * 1.25
        # Keep the decks relatively close together.
        if start_y > CARD_HEIGHT * 2.5:
            start_y = CARD_HEIGHT * 2.5 + CARD_HEIGHT / 20
    else:
        # Place cards in the middle.
        start_y = g_table_height / 2 - CARD_HEIGHT / 2
        start_y = min(start_y, CARD_HEIGHT * 2)
    return start_y, yincr


def calculate_x(deck: list) -> Tuple[float, float]:
    """
    Calculate how far to move each card horizontally then based on that,
    calculate the starting horizontal position.

    :param deck: card names in the format that svg-cards.svg wants.
    :type deck: list
    :return: A tuple containing the Y-starting position and Y-increment.
    :rtype: tuple(float, float)
    """
    xincr = int(g_table_width / (len(deck) + 0.5))  # Spacing to cover entire width
    start_x = 0.0
    mylog.warning("calculate_x: Calculated: xincr=%4.2f, start_x=%4.2f", xincr, start_x)
    if xincr > CARD_WIDTH:
        xincr = int(CARD_WIDTH)
        # Start deck/2 cards from table's midpoint horizontally
        start_x = int(g_table_width / 2 - xincr * (float(len(deck))) / 2)
        mylog.warning(
            "calculate_x: Reset to CARD_WIDTH: xincr=%4.2f, start_x=%4.2f",
            xincr,
            start_x,
        )
    if xincr < int(
        CARD_WIDTH / 20
    ):  # Make sure at least the value of the card is visible.
        xincr = int(CARD_WIDTH / 20)

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
    mylog.warning("place_cards: Start position: (%4.2f, %4.2f)", xpos, ypos)

    # Iterate over canvas's child nodes and move any node
    # where deck_type matches the node's id
    for node in [
        x for (objid, x) in target_canvas.objectDict.items() if deck_type in objid
    ]:
        if not isinstance(node, SVG.UseObject):
            continue

        mylog.warning(
            "place_cards: Processing node %s. (xpos=%4.2f, ypos=%4.2f)",
            node.id,
            xpos,
            ypos,
        )

        # Move the node into the new position.
        # NOTE: setPosition takes a tuple, so the double parenthesis are necessary.
        node.setPosition((xpos, ypos))

        # Each time through the loop, move the next card's starting position.
        xpos += xincr
        if xpos > g_table_width - xincr:
            mylog.warning("place_cards: Exceeded x.max, resetting position. ")
            mylog.warning(
                "    (xpos=%4.2f, table_width=%4.2f, xincr=%4.2f",
                xpos,
                g_table_width,
                xincr,
            )
            xpos = xincr
            ypos += yincr


def calculate_dimensions():
    """
    Run setDimensions and set global variables on demand.
    """
    global g_table_width, g_table_height  # pylint: disable=invalid-name
    # Gather information about the display environment
    (g_table_width, g_table_height) = g_canvas.setDimensions()


def create_game_select_buttons(xpos, ypos) -> bool:
    mylog.error("Entering create_game_select_buttons")
    mylog.warning("create_game_select_buttons: game_dict=%s", g_game_dict)
    added_button = False
    if g_game_dict == {}:
        mylog.warning("cgsb: In g_game_dict={}")
        no_game_button = SVG.Button(
            position=(xpos, ypos),
            size=(450, 35),
            text="No games found, create one and press here.",
            onclick=lambda x: get("/game", on_complete_games),
            fontsize=18,
            objid="nogame",
        )
        g_canvas.attach(no_game_button)
        added_button = True
    else:
        mylog.warning("cgsb: Clearing canvas (%r)", g_canvas)
        g_canvas.deleteAll()
    mylog.warning("cgsb: Enumerating games for buttons (%d).", len(g_game_dict))
    for item, temp_dict in g_game_dict.items():
        mylog.warning("create_game_select_buttons: game_dict item: item=%s", item)
        game_button = SVG.Button(
            position=(xpos, ypos),
            size=(450, 35),
            text=f"Game: {temp_dict['timestamp'].replace('T',' ')}",
            onclick=choose_game,
            fontsize=18,
            objid=item,
        )
        g_canvas.attach(game_button)
        added_button = True
        ypos += 40
    mylog.warning("Exiting create_game_select_buttons")
    return added_button


def create_player_select_buttons(xpos, ypos) -> bool:
    added_button = False
    for item in g_player_dict:
        mylog.warning("player_dict[item]=%s", g_player_dict[item])
        player_button = SVG.Button(
            position=(xpos, ypos),
            size=(450, 35),
            text=f"Player: {g_player_dict[item]['name']}",
            onclick=choose_player,
            fontsize=18,
            objid=g_player_dict[item]["player_id"],
        )
        mylog.warning("create_player_select_buttons: player_dict item: item=%s", item)
        g_canvas.attach(player_button)
        ypos += 40
        added_button = True
    return added_button


def remove_dialogs():
    """
    Remove dialog boxes.
    """
    mylog.error("Entering remove_dialogs.")
    dialogs = document.getElementsByClassName("brython-dialog-main")
    for item in dialogs:
        mylog.warning("Removing dialog item=%r", item)
        item.remove()


def advance_mode(event=None):  # pylint: disable=unused-argument
    """
    Routine to advance the game mode locally. This should be temporary as the game mode
    should be determined and maintained on the server. It can be called directly or via
    callback from an event.

    :param event: The event object passed in during callback, defaults to None
    :type event: [type], optional
    """
    mylog.error("advance_mode: Calling API (current mode=%s)", GAME_MODES[g_game_mode])
    if g_game_id != "" and g_player_id != "":
        put({}, f"/game/{g_game_id}?state=true", advance_mode_callback, False)
    else:
        display_game_options()


# FIXME: This is temporary. The server will decide when to advance the game state.
def advance_mode_callback(req: ajax.Ajax):
    """
    Routine to capture the response of the server when advancing the game mode.

    :param req:   The request response passed in during callback
    :type req:    Request
    """
    global g_game_mode  # pylint: disable=invalid-name
    mylog.error(
        "Entering advance_mode_callback (current mode=%s)", GAME_MODES[g_game_mode]
    )

    ajax_request_tracker(-1)
    if req.status not in [200, 0]:
        return

    if "Round" in req.text and "started" in req.text:
        mylog.warning("advance_mode_callback: Starting new round.")
        g_game_mode = 0
        clear_globals_for_round_change()

        # display_game_options()
        return

    mylog.warning("advance_mode_callback: req.text=%s", req.text)
    data = json.loads(req.text)
    mylog.warning("advance_mode_callback: data=%r", data)
    g_game_mode = data["state"]

    mylog.warning(
        "Leaving advance_mode_callback (current mode=%s)", GAME_MODES[g_game_mode]
    )
    display_game_options()
    # FIXME: This is temporary. The server will decide when to advance the game state.


def game_mode_query_callback(req: ajax.Ajax):
    """
    Routine to capture the response of the server when advancing the game mode.

    :param req:   The request response passed in during callback
    :type req:    Request
    """
    global g_game_mode  # pylint: disable=invalid-name
    if g_game_mode is not None:
        mylog.error(
            "Entering game_mode_query_callback (current mode=%s)",
            GAME_MODES[g_game_mode],
        )

    ajax_request_tracker(-1)
    # TODO: Handle a semi-corner case where in the middle of a round, a player loses /
    # destroys a cookie and reloads the page.
    if req.status not in [200, 0]:
        mylog.warning(
            "game_mode_query_callback: Not setting game_mode - possibly because g_player_id is empty (%s).",
            g_player_id,
        )
        return

    mylog.warning("game_mode_query_callback: req.text=%s", req.text)
    data = json.loads(req.text)
    mylog.warning("game_mode_query_callback: data=%r", data)
    g_game_mode = data["state"]

    mylog.warning(
        "Leaving game_mode_query_callback (current mode=%s)", GAME_MODES[g_game_mode],
    )
    if g_game_mode == 0:
        clear_globals_for_round_change()
    else:
        display_game_options()


def sort_player_cards(event=None):  # pylint: disable=unused-argument
    """
    Sort the player's cards.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    g_players_hand.sort(
        key=lambda x: DECK_SORTED.index(x)  # pylint: disable=unnecessary-lambda
    )
    g_players_meld_deck.sort(
        key=lambda x: DECK_SORTED.index(x)  # pylint: disable=unnecessary-lambda
    )
    display_game_options()


def send_meld(event=None):  # pylint: disable=unused-argument
    """
    Send the meld deck to the server.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    card_string = ",".join(x for x in g_meld_deck if x != "card-base")

    mylog.warning(
        "send_meld: /round/%s/score_meld?player_id=%s&cards=%s",
        g_round_id,
        g_player_id,
        card_string,
    )

    get(
        f"/round/{g_round_id}/score_meld?player_id={g_player_id}&cards={card_string}",
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
    get("/setcookie/player_id/clear", on_complete_set_playercookie)


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
        mylog.warning("choose_game: Caught AttributeError.")
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
        mylog.warning("choose_player: Caught AttributeError.")
        return


def display_game_options():
    """
    Conditional ladder for early game data selection. This needs to be done better and
    have new game/team/player capability.
    """
    global g_game_mode  # pylint: disable=invalid-name
    dump_globals()

    added_button = False
    xpos = 10
    ypos = 0

    # Grab the game_id, team_ids, and players. Display and allow player to choose.
    if g_game_id == "":
        mylog.warning("dso: In g_game_id=''")
        added_button = create_game_select_buttons(xpos, ypos)
    elif g_game_mode is None:
        mylog.warning("dso: In g_game_mode is None")
        get(f"/game/{g_game_id}?state=false", game_mode_query_callback)
    elif g_round_id == "":
        mylog.warning("dso: In g_round_id=''")
        # Open the websocket if needed.
        if g_websocket is None:
            ws_open()

        get(f"/game/{g_game_id}/round", on_complete_rounds)
    elif g_team_list == []:
        mylog.warning("dso: In g_team_list=[]")
        get(f"/round/{g_round_id}/teams", on_complete_teams)
    elif g_player_id == "":
        mylog.warning("dso: In g_player_id=''")
        added_button = create_player_select_buttons(xpos, ypos)
    elif g_players_hand == []:
        mylog.warning("dso: In g_players_hand=[]")
        get(f"/player/{g_player_id}/hand", on_complete_player_cards)
    else:
        mylog.warning("dso: In else clause")
        # Send the registration message.
        send_registration()

        rebuild_display()

    mylog.warning("dso: Considering fitCanvas (added_button=%r)", added_button)
    try:
        if added_button:
            calculate_dimensions()
            g_canvas.fitContents()
    except ZeroDivisionError as e1:
        mylog.warning("dso: Caught ZeroDivisionError from fitContents. %s", e1)
    except AttributeError as e2:
        mylog.warning("dso: Caught AttributeError from fitContents. %s", e2)
    mylog.error("Leaving display_game_options()")


def rebuild_display(event=None):  # pylint: disable=unused-argument
    """
    Clear the display by removing everything from the canvas object, then re-add 
    everything back. It also works for the initial creation and addition of the canvas to 
    the overall DOM.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    global g_game_mode, button_advance_mode, g_canvas  # pylint: disable=invalid-name
    mylog.error("Entering clear_display")

    if g_game_mode is None and not g_game_dict:
        g_game_mode = 0

    if g_ajax_outstanding_requests > 0:
        mylog.warning(
            "There are %d outstanding requests. Skipping clear.",
            g_ajax_outstanding_requests,
        )
        return

    mode = GAME_MODES[g_game_mode]
    mylog.warning("Current mode=%s", mode)

    mylog.warning("Destroying canvas contents with mode: %s", g_canvas.attrs["mode"])
    g_canvas.deleteAll()

    # Set the current game mode in the canvas.
    g_canvas.attrs["mode"] = mode

    # Get the dimensions of the canvas and update the display.
    calculate_dimensions()
    set_card_positions()

    half_table = g_table_width / 2 - 35

    # Update/create buttons
    # Button to call advance_mode on demand
    # FIXME: This is temporary. The server will decide when to advance the game state.
    button_advance_mode = SVG.Button(
        position=(half_table - 80 * 3, -40),
        size=(70, 35),
        text=GAME_MODES[g_game_mode].capitalize(),
        onclick=advance_mode,
        fontsize=18,
        objid="button_advance_mode",
    )
    # Button to call update_display on demand
    button_refresh = SVG.Button(
        position=(half_table - 80 * 2, -40),
        size=(70, 35),
        text="Refresh",
        onclick=set_card_positions,
        fontsize=18,
        objid="button_refresh",
    )

    # Button to call clear_display on demand
    button_clear = SVG.Button(
        position=(half_table - 80 * 1, -40),
        size=(70, 35),
        text="Clear",
        onclick=rebuild_display,
        fontsize=18,
        objid="button_clear",
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
        onclick=window.location.reload,  # pylint: disable=no-member
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

    for item in [
        button_clear,
        button_refresh,
        button_advance_mode,
        button_clear_game,
        button_clear_player,
        button_reload_page,
        button_sort_player,
    ]:
        g_canvas.addObject(item)

    # TODO: Add buttons & display to facilitate bidding. Tie into API.

    if GAME_MODES[g_game_mode] in ["meld"]:
        # Button to call submit_meld on demand
        button_send_meld = SVG.Button(
            position=(half_table, -40),
            size=(70, 35),
            text="Send\nMeld",
            onclick=send_meld,
            fontsize=16,
            objid="button_send_meld",
        )
        g_canvas.addObject(button_send_meld)

    try:
        g_canvas.fitContents()
    except ZeroDivisionError:
        pass
    except AttributeError:
        pass
    g_canvas.mouseMode = SVG.MouseMode.DRAG
    mylog.warning("Leaving clear_display")


def set_card_positions(event=None):  # pylint: disable=unused-argument
    """
    Populate and place cards based on the game's current mode. This needs a little more
    work to support more aspects of the game.

    :param event: The event object passed in during callback, defaults to None
    :type event: [type], optional
    """
    global g_game_mode  # pylint: disable=invalid-name
    mode = GAME_MODES[g_game_mode]
    mylog.error("Entering update_display. (mode=%s)", mode)
    calculate_dimensions()

    # FIXME: I don't think this should be needed.
    if g_player_id != "" and not g_players_hand:
        get(f"/player/{g_player_id}/hand", on_complete_player_cards)
        return

    # Place the desired decks on the display.
    if not g_canvas.objectDict:
        if mode in ["game"] and g_game_id == "":  # Choose game, player
            display_game_options()
        if mode in ["bid", "bidfinal"]:  # Bid
            # Use empty deck to prevent peeking at the kitty.
            populate_canvas(g_kitty_deck, g_canvas, "kitty")
            populate_canvas(g_players_hand, g_canvas, "player")
        if mode in ["bidfinal"]:  # Bid submitted
            # The kitty doesn't need to remain 'secret' now that the bidding is done.
            if g_round_id != "":
                get(f"/round/{g_round_id}/kitty", on_complete_kitty)
        elif mode in ["reveal"]:  # Reveal
            # Ask the server for the cards in the kitty.
            populate_canvas(g_kitty_deck, g_canvas, "kitty")
            populate_canvas(g_players_hand, g_canvas, "player")
        elif mode in ["meld"]:  # Meld
            # TODO: IF bid winner, need way to select trump & communicate with other players - BEFORE they have the chance to choose / submit their meld.
            # TODO: Add a score meld button to submit temporary deck and retrieve and display a numerical score, taking into account trump.
            populate_canvas(g_meld_deck, g_canvas, GAME_MODES[g_game_mode])
            populate_canvas(g_players_meld_deck, g_canvas, "player")
        elif mode in ["trick"]:  # Trick
            populate_canvas(discard_deck, g_canvas, GAME_MODES[g_game_mode])
            populate_canvas(g_players_hand, g_canvas, "player")

    # Last-drawn are on top (z-index wise)
    # TODO: Add buttons/input for this player's meld.
    # TODO: Figure out how to convey the bidding process across the players.
    # TODO: Retrieve events from API to show kitty cards when they are flipped over.
    if mode in ["bid", "bidfinal", "reveal"]:  # Bid & Reveal
        place_cards(g_kitty_deck, g_canvas, location="top", deck_type="kitty")
        place_cards(g_players_hand, g_canvas, location="bottom", deck_type="player")
    elif mode in ["meld"]:  # Meld
        # TODO: Expand display to show all four players.
        # TODO: Retrieve events from API to show other player's meld.
        place_cards(g_meld_deck, g_canvas, location="top", deck_type=mode)
        place_cards(
            g_players_meld_deck, g_canvas, location="bottom", deck_type="player"
        )
    elif mode in ["trick"]:  # Trick
        # Remove any dialogs from the meld phase.
        remove_dialogs()
        # TODO: Retrieve/send events from API to show cards as they are played.
        place_cards(discard_deck, g_canvas, location="top", deck_type=mode)
        place_cards(g_players_hand, g_canvas, location="bottom", deck_type="player")

    g_canvas.mouseMode = SVG.MouseMode.DRAG


## END Function definitions.

# Gather information about where we're coming from.
(PROTOCOL, SERVER) = find_protocol_server()

# Make the clear_display function easily available to plain javascript code.
window.rebuild_display = rebuild_display

# Locate the card table in the HTML document.
CardTable = document["card_table"]

# Attach the card graphics file
document["card_definitions"].attach(SVG.Definitions(filename=CARD_URL))

# Create the base SVG object for the card table.
g_canvas = SVG.CanvasObject("95vw", "90vh", None, objid="canvas")
CardTable <= g_canvas  # pylint: disable=pointless-statement
calculate_dimensions()
g_canvas.attrs["mode"] = "initial"

# Declare temporary decks
discard_deck = ["card-base" for _ in range(g_players)]

# TODO: Figure out how better to calculate HAND_SIZE.
HAND_SIZE = int(48 / g_players)
g_meld_deck = ["card-base" for _ in range(HAND_SIZE)]

document.getElementById("please_wait").remove()
display_game_options()

# See if some steps can be bypassed because we refreshed in the middle of the game.
get("/game", on_complete_games)
get("/getcookie/game_id", on_complete_getcookie)
get("/getcookie/player_id", on_complete_getcookie)
