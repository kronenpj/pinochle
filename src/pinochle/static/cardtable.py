"""
In-browser script to handle the card-table user interface.
"""
import copy
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import browser

import brySVG.dragcanvas as SVG  # pylint: disable=import-error
from browser import ajax, document, html, svg, websocket, window
from browser.widgets.dialog import Dialog, InfoDialog

# Disable some pylint complaints because this code is more like javascript than python.
# pylint: disable=global-statement
# pylint: disable=pointless-statement
# Similarly, disable some pyright complaints
# pyright: reportGeneralTypeIssues=false

mylog = logging.getLogger("cardtable")
mylog.setLevel(logging.CRITICAL)  # No output
# mylog.setLevel(logging.ERROR)  # Function entry/exit
# mylog.setLevel(logging.WARNING)  # Everything

CARD_URL = "/static/playingcards.svg"

# Intrinsic dimensions of the cards in the deck.
CARD_WIDTH = 170
CARD_HEIGHT = 245
CARD_SMALLER_WIDTH = CARD_WIDTH * 0.75
CARD_SMALLER_HEIGHT = CARD_HEIGHT * 0.75

# NOTE: Also contained in play_pinochle.py
#                0      1        2           3        4       5
GAME_MODES = ["game", "bid", "bidfinal", "reveal", "meld", "trick"]

# These are a lot less dynamic than I thought they'd be.
DECK_CONFIG = {
    "player": {
        1: {"flippable": False, "movable": False, "show_face": True},  # Bid
        2: {"flippable": False, "movable": False, "show_face": True},  # Bidfinal
        3: {"flippable": False, "movable": False, "show_face": True},  # Reveal
        4: {"flippable": False, "movable": True, "show_face": True},  # Meld
        5: {"flippable": False, "movable": True, "show_face": True},  # Trick
    },
    "kitty": {
        1: {"flippable": False, "movable": False, "show_face": False},  # Bid (Kitty)
        2: {
            "flippable": False,
            "movable": False,
            "show_face": False,
        },  # Bidfinal (Kitty)
        3: {"flippable": False, "movable": False, "show_face": True},  # Reveal (Kitty)
        4: {"flippable": False, "movable": False, "show_face": True},  # Meld (Meld)
        5: {"flippable": False, "movable": False, "show_face": True},  # Trick (Discard)
    },
    "meld": {
        1: {"flippable": False, "movable": False, "show_face": False},  # Bid (Kitty)
        2: {
            "flippable": False,
            "movable": False,
            "show_face": False,
        },  # Bidfinal (Kitty)
        3: {"flippable": False, "movable": False, "show_face": False},  # Reveal (Kitty)
        4: {"flippable": False, "movable": False, "show_face": True},  # Meld (Meld)
        5: {"flippable": False, "movable": False, "show_face": True},  # Trick (Discard)
    },
    "trick": {
        1: {"flippable": False, "movable": False, "show_face": False},  # Bid (Kitty)
        2: {
            "flippable": False,
            "movable": False,
            "show_face": False,
        },  # Bidfinal (Kitty)
        3: {"flippable": False, "movable": False, "show_face": False},  # Reveal (Kitty)
        4: {"flippable": False, "movable": False, "show_face": True},  # Meld (Meld)
        5: {"flippable": False, "movable": False, "show_face": True},  # Trick (Discard)
    },
}

SUITS = ["spade", "heart", "club", "diamond"]

ZEROS_UUID = "00000000-0000-0000-0000-000000000000"


@dataclass(frozen=True)
class GuId:
    """
    Parent container for string-ified GUIDs / UUIDs used as identifers by the card
    service.
    """

    value: str

    def __init__(self, value: str = ZEROS_UUID) -> None:
        object.__setattr__(self, "value", str(value))

    def __str__(self) -> str:
        return str(self.value)


class GameID(GuId):  # pylint: disable=too-few-public-methods
    """
    Game ID data
    """


class RoundID(GuId):  # pylint: disable=too-few-public-methods
    """
    Round ID data
    """


class TeamID(GuId):  # pylint: disable=too-few-public-methods
    """
    Team ID data
    """


class PlayerID(GuId):  # pylint: disable=too-few-public-methods
    """
    Player ID data
    """


class PlayingCard(SVG.UseObject):
    """
    PlayingCard class to hold additional attributes than available from UseObject,
    specific to the Pinochle game.

    :param UseObject: brySVG.UseObject class
    :type UseObject: brySVG.UseObject
    """

    def __init__(
        self, href=None, objid=None, face_value="back", show_face=True, flippable=False,
    ):
        # Set the initial face to be shown.
        if href is None:
            href = "#back"
        self.face_value = face_value
        self.show_face = show_face
        SVG.UseObject.__init__(self, href=href, objid=objid)
        self.flippable = flippable
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

    def play_handler(self, event_type):
        """
        Handler for when a card is "played." This can mean one of two things.
        1. The card is chosen as meld either by moving or clicking on the card.
        2. The card is 'thrown' during trick play.

        :param event_type: Whether the event is a click or a drag
        :type event: string
        """
        (__, new_y) = self.origin

        # Determine whether the card is now in a position to be considered thrown.
        if new_y >= CARD_HEIGHT and event_type == "drag":
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
        if GAME_MODES[g_game_mode] in ["reveal"]:  # Bury
            if "player" in self.id:
                parent_canvas.translateObject(
                    parent_canvas.objectDict[f"{self.id}"], (0, CARD_HEIGHT / 1.9)
                )
        elif GAME_MODES[g_game_mode] in ["meld"]:  # Meld
            if True or "player" in self.id:
                sending_deck = g_players_meld_deck  # Deep copy
                receiving_deck = g_meld_deck  # Reference
            else:
                add_only = True
                card_tag = "player"
                sending_deck = g_meld_deck  # Reference
                receiving_deck = g_players_meld_deck  # Deep copy
        elif GAME_MODES[g_game_mode] in ["trick"]:  # Trick
            sending_deck = g_players_hand  # Reference
            receiving_deck = discard_deck  # Reference

        # TODO: Finish implementation option for player to move card from meld deck back into their hand. The list manipulation should be ok, but the DOM is missing a card in the player's deck for the code below to work as written.

        # Decide which card in receiving_deck to replace - identify the index of the
        # first remaining instance of 'card-base'
        if add_only and "card-base" not in receiving_deck:
            receiving_deck.append("card-base")

        # The only time this is used is during 'meld' and 'trick' mode.
        self.handle_discard_placement(
            sending_deck, receiving_deck, card_tag, parent_canvas
        )

        self.face_update_dom()
        rebuild_display()

    def handle_discard_placement(
        self, sending_deck, receiving_deck, card_tag, parent_canvas
    ):
        # Cards are placed in a specific order when in trick mode. Otherwise,
        # the first available empty (card-base) slot is used.
        if GAME_MODES[g_game_mode] in ["trick"]:
            p_list: List[PlayerID] = order_player_id_list_for_trick()
            placement: int = p_list.index(g_player_id)
        elif GAME_MODES[g_game_mode] in ["meld"]:
            placement = receiving_deck.index("card-base")
        else:
            return
        mylog.warning(
            "PlayingCard.play_handler: Locating %s%s\nPlayingCard.play_handler: %s: %s",
            card_tag,
            placement,
            parent_canvas.mode,
            [objid for (objid, _) in parent_canvas.objectDict.items()],
        )

        # Locate the ID of the target card in the DOM.
        discard_object = parent_canvas.objectDict[f"{card_tag}{placement}"]

        # Delete the original card from the UI.
        parent_canvas.deleteObject(self)
        # Remove the original card from the player's hand and put it in the
        # discard deck.
        sending_deck.remove(self.face_value)
        receiving_deck[placement] = self.face_value
        # Replace the discard face with that of the original, moved card.
        discard_object.face_value = self.face_value
        discard_object.attrs["href"] = self.attrs["href"]

        # TODO: Remove this when taking meld back is implemented above.
        discard_object.movable = False
        discard_object.unbind("click")
        # TODO: Remove this when taking meld back is implemented above.

        if GAME_MODES[g_game_mode] in ["trick"]:
            mylog.warning("Throwing card: %s", self.face_value)
            # Convey the played card to the server.
            put(
                f"/play/{g_round_id.value}/play_card?player_id={g_player_id.value}&card={self.face_value}"
            )

    def card_click_handler(self):
        """
        Click handler for the playing card. The action depends on the game mode.
        Since the only time this is done is during the meld process, also call the API to
        notify it that a kitty card has been flipped over and which card that is.
        """
        # pylint: disable=invalid-name
        global g_players_hand, g_players_meld_deck
        mylog.error("Entering PlayingCard.card_click_handler()")

        if GAME_MODES[g_game_mode] in ["reveal"] and self.flippable:
            mylog.warning(
                "PlayingCard.card_click_handler: flippable=%r", self.flippable
            )
            # self.show_face = not self.show_face
            # self.flippable = False
            # self.face_update_dom()
            # TODO: Call API to notify the other players this particular card was
            # flipped over and add it to the player's hand.
            send_websocket_message(
                {
                    "action": "reveal_kitty",
                    "game_id": g_game_id.value,
                    "player_id": g_player_id.value,
                    "card": self.face_value,
                }
            )
        if GAME_MODES[g_game_mode] in ["reveal", "meld", "trick"]:
            self.play_handler(event_type="click")


# Websocket holder
g_websocket: Optional[websocket.WebSocket] = None

# Programmatically create a pre-sorted deck to compare to when sorting decks of cards.
# Importing a statically-defined list from constants doesn't work for some reason.
# "9", "jack", "queen", "king", "10", "ace"
# "ace", "10", "king", "queen", "jack", "9"
DECK_SORTED: List[str] = []
for _suit in SUITS:
    for _card in ["ace", "10", "king", "queen", "jack", "9"]:
        DECK_SORTED.append(f"{_suit}_{_card}")

# API "Constants"
AJAX_URL_ENCODING = "application/x-www-form-urlencoded"

# Game-related globals
g_game_id: GameID = GameID()
g_game_mode: int = -1
g_hand_size: int = 0
g_kitty_size: int = 0
g_my_team_score: int = 0
g_meld_score: int = 0
g_other_team_score: int = 0
g_player_id: PlayerID = PlayerID()
g_players: int = 4
g_round_bid: int = 0
g_round_id: RoundID = RoundID()
g_team_id: TeamID = TeamID()
g_trump: str = ""

# Various state globals
g_ajax_outstanding_requests: int = 0
g_game_dict: Dict[GameID, Dict[str, Any]] = {}
g_kitty_deck: List[str] = []
g_meld_deck: List[str] = []
g_player_dict: Dict[PlayerID, Dict[str, str]] = {}
g_player_list: List[PlayerID] = []
g_players_hand: List[str] = []
g_players_meld_deck: List[str] = []
g_team_dict: Dict[TeamID, Dict[str, str]] = {}
g_team_list: List[TeamID] = []

# Track the user who is the round's bid winner, and each trick winner.
g_round_bid_trick_winner: PlayerID  # pylint: disable=invalid-name

button_advance_mode = None  # pylint: disable=invalid-name
g_registered_with_server = False  # pylint: disable=invalid-name


class CardTable(SVG.CanvasObject):  # pylint: disable=too-few-public-methods
    """
    Class to encapsulate aspects of the card table.
    """

    def __init__(self):
        super().__init__("95vw", "90vh", "none", objid="canvas")
        self.mode = "initial"
        self.bind("mouseup", self.move_handler)
        self.bind("touchend", self.move_handler)

    def move_handler(self, event=None):
        """
        Inspect the object's attributes and determine whether additional action needs to
        be taken during a move action.

        :param event: The event object passed in during callback, defaults to None
        :type event: Event(?), optional
        """
        mylog.error("Entering CardTable.move_handler")
        selected_card = self.getSelectedObject(event.target.id)

        currentcoords = self.getSVGcoords(event)
        offset = currentcoords - self.dragStartCoords
        # Moving a card within a CARD_HEIGHT of the top "throws" that card.
        if selected_card:
            if (
                # Only play cards from player's hand
                # Only throw cards that are face-up
                selected_card.id.startswith("player")
                and selected_card.show_face
            ):
                if offset == (0, 0):  # We have a click, not a drag
                    selected_card.card_click_handler()
                else:  # It's a drag
                    selected_card.play_handler(event_type="drag")
            elif (
                # Check cards from kitty deck
                # Only flip cards that are face-down
                selected_card.id.startswith("kitty")
                and not selected_card.show_face
            ):
                if offset == (0, 0):  # We have a click, not a drag
                    selected_card.card_click_handler()


class BidDialog:
    """
    Class to handle the bid dialog display
    """

    bid_dialog = None
    last_bid = -1

    def on_click_bid_dialog(self, event=None):
        """
        Handle the click event for the bid/pass buttons.

        :param event: [description], defaults to None
        :type event: [type], optional
        """
        if "Pass" in event.currentTarget.text:
            bid = -1
        else:
            bid = int(self.bid_dialog.select_one("INPUT").value)
        if bid < -1 or (bid > 0 and self.last_bid >= bid):
            # Bid won't be accepted by server.
            return
        self.last_bid = bid
        self.bid_dialog.close()
        put(
            f"/play/{g_round_id.value}/submit_bid?player_id={g_player_id.value}&bid={bid}"
        )

    def display_bid_dialog(self, bid_data: str):
        """
        Display the meld hand submitted by a player in a pop-up.

        :param bid_data: Data from the event as a JSON string.
        :type bid_data: str
        """
        mylog.error("Entering display_bid_dialog.")
        data = json.loads(bid_data)
        player_id: PlayerID = PlayerID(data["player_id"])
        self.last_bid = int(data["bid"])
        player_name = g_player_dict[player_id]["name"].capitalize()

        remove_dialogs()

        # Don't display a dialog box if this isn't the player bidding.
        if g_player_id != player_id:
            InfoDialog(
                "Bid Update",
                f"Current bid is: {self.last_bid}<br/>Next bid to: {player_name}",
                top=25,
                left=25,
            )
            return

        self.bid_dialog = Dialog(
            "Bid or Pass", ok_cancel=["Bid", "Pass"], top=25, left=25,
        )
        # pylint: disable=expression-not-assigned
        self.bid_dialog.panel <= html.DIV(
            f"{player_name}, enter your bid or pass: "
            + html.INPUT(value=f"{self.last_bid+1}")
        )

        self.bid_dialog.ok_button.bind("click", self.on_click_bid_dialog)
        self.bid_dialog.cancel_button.bind("click", self.on_click_bid_dialog)


class TrumpSelectDialog:
    """
    Class to handle the trump dialog display
    """

    trump_dialog = None
    d_canvas = None

    def on_click_trump_dialog(self, event=None):
        """
        Handle the click event for the OK button. Ignore the cancel button.

        :param event: [description], defaults to None
        :type event: [type], optional
        """
        mylog.error("Entering on_click_trump_dialog")
        trump = event.target.id
        cards_buried = locate_cards_below_hand()
        mylog.warning("on_click_trump_dialog: You buried these cards: %r", cards_buried)
        if not trump:
            return
        if len(cards_buried) != g_kitty_size:
            InfoDialog(
                "Try again...",
                f"You buried {len(cards_buried)}, but {g_kitty_size} cards are required."
                + "Pressing the sort button will reset your choices.",
                ok=True,
                remove_after=15,
            )
            return
        self.trump_dialog.close()
        # Notify the server of trump.
        put(
            f"/play/{g_round_id.value}/set_trump?player_id={g_player_id.value}&trump={trump}"
        )
        # Transfer cards into the team's collection and out of the player's hand.
        buried_trump = 0
        for card in cards_buried:
            put(f"/round/{g_round_id.value}/{g_team_id.value}?card={card}")
            delete(f"/player/{g_player_id.value}/hand/{card}")
            g_players_hand.remove(card)
            g_players_meld_deck.remove(card)
            if trump in card:
                buried_trump += 1
        if buried_trump > 0:
            send_websocket_message(
                {
                    "action": "trump_buried",
                    "game_id": g_game_id.value,
                    "player_id": g_player_id.value,
                    "count": buried_trump,
                }
            )

    def display_trump_dialog(self):
        """
        Prompt the player to select trump.
        """
        mylog.error("Entering display_trump_dialog.")

        # Clear previous dialog_trump instances.
        try:
            previous = g_canvas.getSelectedObject("dialog_trump")
            g_canvas.removeObject(previous)
        except AttributeError:
            pass
        # Don't display a trump select dialog box if this isn't the player who won the
        # bid. Instead let the players know we're waiting for input.
        if g_player_id != g_round_bid_trick_winner:
            try:
                bid_winner_name = g_player_dict[g_round_bid_trick_winner][
                    "name"
                ].capitalize()
                InfoDialog(
                    "Waiting...",
                    f"Waiting for {bid_winner_name} to select trump.",
                    ok=False,
                )
                # Add an ID attribute so we can find it later if needed.
                for item in document.getElementsByClassName("brython-dialog-main"):
                    mylog.warning("display_trump_dialog: Item: %r", item)
                    if not item.id and "Waiting" in item.text:
                        # Assume this is the one we just created.
                        item.id = "dialog_trump"
            except KeyError:
                pass
            return

        self.trump_dialog = Dialog(
            "Select Trump Suit", ok_cancel=False, top=40, left=30,
        )
        self.d_canvas = SVG.CanvasObject("20vw", "20vh", "none", objid="dialog_canvas")
        glyph_width = 50
        xpos = 0
        for suit in SUITS:
            # pylint: disable=expression-not-assigned
            self.d_canvas <= SVG.UseObject(
                angle=180,
                href=f"#{suit}",
                objid=f"{suit}",
                origin=(xpos, 0),
                width=glyph_width,
            )
            xpos += glyph_width + 5

        player_name = g_player_dict[g_player_id]["name"].capitalize()
        if g_kitty_size:
            instructions = f"{player_name}, please move {g_kitty_size} cards BELOW your hand, then select a suit to be trump."
        else:
            instructions = f"{player_name}, please select a suit to be trump."
        # pylint: disable=expression-not-assigned
        self.trump_dialog.panel <= html.DIV(instructions + html.BR() + self.d_canvas)
        self.d_canvas.fitContents()

        self.trump_dialog.bind("click", self.on_click_trump_dialog)


class MeldFinalDialog:
    """
    Class to handle the meld dialog display
    """

    meld_final_dialog = None

    def on_click_meld_dialog(self, event=None):  # pylint: disable=unused-argument
        """
        Handle the click event for the OK button. Ignore the cancel button.

        :param event: [description], defaults to None
        :type event: [type], optional
        """
        mylog.error("Entering on_click_meld_dialog")
        # Notify the server of my meld is final.
        put(f"/play/{g_round_id.value}/finalize_meld?player_id={g_player_id.value}")
        self.meld_final_dialog.close()

    def display_meld_final_dialog(self):
        """
        Prompt the player to select whether their meld is final.
        """
        mylog.error("Entering display_meld_final_dialog.")

        self.meld_final_dialog = Dialog(
            "Is your meld submission final?", ok_cancel=["Yes", "No"]
        )
        player_name = g_player_dict[g_player_id]["name"].capitalize()
        # pylint: disable=expression-not-assigned
        self.meld_final_dialog.panel <= html.DIV(f"{player_name}, Is your meld final?")

        self.meld_final_dialog.ok_button.bind("click", self.on_click_meld_dialog)


class TrickWonDialog:
    """
    Class to handle the trick won dialog display
    """

    trick_won_dialog = None

    def on_click_trick_won_dialog(self, event=None):
        """
        Handle the click event for the next trick/ok buttons.

        :param event: [description], defaults to None
        :type event: [type], optional
        """
        if not event.currentTarget.text:
            return

        mylog.error("In on_click_trick_won_dialog")
        # Convey to the server that play is continuing.
        put(f"/play/{g_round_id.value}/next_trick?player_id={g_player_id.value}")
        self.trick_won_dialog.close()

    def on_click_final_trick_won_dialog(self, event=None):
        """
        Handle the click event for the next round/ok buttons.

        :param event: [description], defaults to None
        :type event: [type], optional
        """
        if not event.currentTarget.text:
            return

        mylog.error("In on_click_final_trick_won_dialog")
        # Convey to the server that to start the next round.
        put(f"/game/{g_game_id.value}?state=true", advance_mode_callback, False)
        self.trick_won_dialog.close()

    def display_trick_won_dialog(self):
        """
        Display the trick has been won dialog to the player who won the trick.
        """
        mylog.error("Entering display_trick_won_dialog.")

        self.trick_won_dialog = Dialog(
            "Trick complete", ok_cancel=["Next trick", "Ok"], top=25,
        )
        # pylint: disable=expression-not-assigned
        self.trick_won_dialog.panel <= html.DIV(
            f"{g_player_dict[g_player_id]['name']}, you won the trick!"
        )

        self.trick_won_dialog.ok_button.bind("click", self.on_click_trick_won_dialog)
        # TODO: See if there's a way to delete the cancel button.
        self.trick_won_dialog.cancel_button.bind(
            "click", self.on_click_trick_won_dialog
        )

    def display_final_trick_dialog(
        self, my_team: str, my_scores: int, other_team: str, other_scores: int
    ):
        """
        Display notification that the final trick has been won by this player.

        :param my_team: This player's team name
        :type my_team: str
        :param my_scores: This player's team trick score
        :type my_scores: int
        :param other_team: The other team's name
        :type other_team: str
        :param other_scores: The other team's trick score
        :type other_scores: int
        """
        mylog.error("Entering display_final_trick_dialog.")

        self.trick_won_dialog = Dialog(
            "Final trick complete", ok_cancel=["Next round", "Ok"], top=25,
        )
        # pylint: disable=expression-not-assigned
        self.trick_won_dialog.panel <= html.DIV(
            f"{g_player_dict[g_player_id]['name']}, you won the trick! "
            f"Trick Scores: {my_team}: {my_scores} points / {other_team}: {other_scores} points",
        )

        self.trick_won_dialog.ok_button.bind(
            "click", self.on_click_final_trick_won_dialog
        )
        # TODO: See if there's a way to delete the cancel button.
        self.trick_won_dialog.cancel_button.bind(
            "click", self.on_click_final_trick_won_dialog
        )


def dump_globals() -> None:
    """
    Debugging assistant to output the value of selected globals.
    """
    variables = {
        # "canvas": canvas,
        # "g_game_id": g_game_id,
        # "g_game_mode": g_game_mode,
        # "g_round_id": g_round_id,
        # "g_team_list": g_team_list,
        # "g_player_id": g_player_id,
        # "g_player_list": g_player_list,
        # "g_players_hand": g_players_hand,
        # "g_game_dict": g_game_dict,
        "g_kitty_size": g_kitty_size,
        "g_kitty_deck": g_kitty_deck,
    }
    for var_name, value in variables.items():
        if value:
            print(f"dgo: {var_name}={value} ({type(value)})")
        else:
            print(f"dgo: {var_name} is None")


def find_protocol_server():
    """
    Gather information from the environment about the protocol and server name
    from where we're being served.

    :return: Tuple with strings representing protocol and server with port.
    :rtype: (str, str)
    """
    start = os.environ["HOME"].find("//") + 2
    end = os.environ["HOME"].find("/", start) + 1
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
    # pylint: disable=invalid-name
    global g_websocket

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
    global g_websocket, g_registered_with_server  # pylint: disable=invalid-name

    g_websocket = None
    g_registered_with_server = False
    # set_timeout(ws_open, 1000)


def on_ws_error(event=None):
    """
    Callback for Websocket error event.
    """
    mylog.error("on_ws_error: Connection has experienced an error")
    mylog.warning("%r", event)


def on_ws_event(event=None):
    """
    Callback for Websocket event from server. This method handles much of the state
    change in the user interface.

    :param event: Event object from ws event.
    :type event: [type]
    """
    mylog.error("In on_ws_event.")
    # pylint: disable=invalid-name
    global g_game_mode, g_player_list

    t_data = json.loads(event.data)
    mylog.warning("on_ws_event: %s", event.data)

    if "action" not in t_data:
        return
    if "game_start" in t_data["action"]:
        g_game_mode = t_data["state"]
        mylog.warning("on_ws_event: game_start: g_player_list=%r", g_player_list)
        clear_globals_for_round_change()
    elif "notification_player_list" in t_data["action"]:
        update_player_names(event.data)
    elif "game_state" in t_data["action"]:
        g_game_mode = t_data["state"]
        display_game_options()
    elif "bid_prompt" in t_data["action"]:
        bid_dialog = BidDialog()
        bid_dialog.display_bid_dialog(event.data)
    elif "bid_winner" in t_data["action"]:
        display_bid_winner(event.data)
    elif "reveal_kitty" in t_data["action"]:
        reveal_kitty_card(event.data)
    elif "trump_selected" in t_data["action"]:
        record_trump_selection(event.data)
    elif "trump_buried" in t_data["action"]:
        notify_trump_buried(event.data)
    elif "meld_update" in t_data["action"]:
        display_player_meld(event.data)
    elif "team_score" in t_data["action"]:
        update_team_scores(event.data)
    elif "trick_card" in t_data["action"]:
        update_trick_card(event.data)
    elif "trick_won" in t_data["action"]:
        update_trick_winner(event.data)
    elif "trick_next" in t_data["action"]:
        clear_globals_for_trick_change()
    elif "score_round" in t_data["action"]:
        update_round_final_score(event.data)


def update_round_final_score(event=None):
    """
    Notify players that the final trick has been won.

    :param event: [description], defaults to None
    :type event: [type], optional
    """
    mylog.error("Entering update_round_final_score.")
    # pylint: disable=invalid-name
    global g_round_bid_trick_winner, g_my_team_score, g_other_team_score

    data = json.loads(event)
    mylog.warning("update_round_final_score: data=%s", data)
    assert isinstance(data, dict)
    t_player_id = PlayerID(data["player_id"])
    assert isinstance(data["team_trick_scores"], dict)
    mylog.warning(
        "update_round_final_score: data['team_trick_scores']: %r",
        data["team_trick_scores"],
    )
    t_team_trick_scores = {TeamID(x): y for (x, y) in data["team_trick_scores"].items()}
    assert isinstance(data["team_scores"], dict)
    mylog.warning(
        "update_round_final_score: data['team_scores']: %r", data["team_scores"],
    )
    t_team_scores = {TeamID(x): y for (x, y) in data["team_scores"].items()}
    mylog.warning("update_round_final_score: t_player_id=%s", t_player_id)
    mylog.warning(
        "update_round_final_score: t_team_trick_scores=%r", t_team_trick_scores
    )
    mylog.warning("update_round_final_score: t_team_scores=%r", t_team_scores)

    # Record that information.
    g_round_bid_trick_winner = t_player_id

    # Obtain the other team's ID
    t_other_team_id = [x for x in g_team_dict if x != g_team_id][0]

    mylog.warning("update_round_final_score: Setting my team name")
    my_team = g_team_dict[g_team_id]["team_name"].capitalize()
    mylog.warning("update_round_final_score: Setting other team's name")
    other_team = [g_team_dict[x]["team_name"] for x in g_team_dict if x != g_team_id][
        0
    ].capitalize()
    mylog.warning("update_round_final_score: Setting score variables")
    my_scores, other_scores = (
        t_team_trick_scores[g_team_id],
        t_team_trick_scores[t_other_team_id],
    )

    # TODO: Handle case where bid winner's team doesn't make the bid.
    mylog.warning("update_round_final_score: Setting global team scores.")
    g_my_team_score, g_other_team_score = (
        t_team_scores[g_team_id],
        t_team_scores[t_other_team_id],
    )

    mylog.warning("g_player_id=%s / t_player_id=%s", g_player_id, t_player_id)
    if g_player_id == t_player_id:
        mylog.warning(
            "update_round_final_score: Displaying final trick dialog for this player."
        )
        TrickWonDialog().display_final_trick_dialog(
            my_team, my_scores, other_team, other_scores
        )
    else:
        mylog.warning(
            "update_round_final_score: Displaying generic final trick dialog for this player."
        )
        InfoDialog(
            "Last Trick Won",
            f"{g_player_dict[t_player_id]['name'].capitalize()} won the final trick. "
            + f"Trick Scores: {my_team}: {my_scores} points / {other_team}: {other_scores} points",
            top=25,
            left=25,
        )


def update_trick_winner(event=None):
    """
    Notify players that the trick has been won.

    :param event: [description], defaults to None
    :type event: [type], optional
    """
    mylog.error("Entering update_trick_winner.")
    # pylint: disable=invalid-name
    global g_round_bid_trick_winner

    data = json.loads(event)
    mylog.warning("update_trick_winner: data=%s", data)
    assert isinstance(data, dict)
    t_player_id = PlayerID(data["player_id"])
    t_card = data["winning_card"]
    mylog.warning("update_trick_winner: t_player_id=%s", t_player_id)
    mylog.warning("update_trick_winner: t_card=%s", t_card)

    # Find the first instance of the winning card in the list.
    card_index = discard_deck.index(t_card)
    # Correlate that to the player_id who threw it.
    t_player_id = order_player_id_list_for_trick()[card_index]
    mylog.warning("update_trick_winner: t_player_id=%s", t_player_id)
    # Record that information.
    g_round_bid_trick_winner = t_player_id

    if g_player_id == t_player_id:
        TrickWonDialog().display_trick_won_dialog()
    else:
        InfoDialog(
            "Trick Won",
            f"{g_player_dict[t_player_id]['name'].capitalize()} won the trick.",
            top=25,
            left=25,
        )


def update_trick_card(event=None):
    """
    Place the thrown card in the player's slot for this trick.

    :param event: [description], defaults to None
    :type event: [type], optional
    """
    mylog.error("Entering update_trick_card.")
    data = json.loads(event)
    mylog.warning("update_trick_card: data=%s", data)
    assert isinstance(data, dict)
    t_player_id: PlayerID = PlayerID(data["player_id"])
    t_card = data["card"]
    mylog.warning("update_trick_card: t_player_id=%s", t_player_id)
    mylog.warning("update_trick_card: t_card=%s", t_card)
    discard_deck[order_player_id_list_for_trick().index(t_player_id)] = t_card

    # Set the player's hand to unmovable until the trick is over.
    rebuild_display()


def update_team_scores(event=None):
    """
    Notify players that trump has been buried.

    :param event: [description], defaults to None
    :type event: [type], optional
    """
    mylog.error("Entering update_team_scores.")
    # pylint: disable=invalid-name
    global g_my_team_score, g_other_team_score, g_meld_score
    data = json.loads(event)
    mylog.warning("update_team_scores: data=%r", data)
    assert isinstance(data, dict)
    if g_team_id == TeamID(data["team_id"]):
        g_my_team_score = data["score"]
        g_meld_score = data["meld_score"]
    else:  # Other team
        g_other_team_score = data["score"]

    update_status_line()


def notify_trump_buried(event=None):
    """
    Notify players that trump has been buried.

    :param event: [description], defaults to None
    :type event: [type], optional
    """
    mylog.error("Entering notify_trump_buried.")
    data = json.loads(event)
    mylog.warning("notify_trump_buried: data=%r", data)
    assert isinstance(data, dict)
    if "player_id" in data:
        mylog.warning("notify_trump_buried: About to retrieve player_id from data")
        t_player_id: PlayerID = PlayerID(data["player_id"])
    else:
        t_player_id = PlayerID()
    mylog.warning("notify_trump_buried: t_player_id=%r", t_player_id)
    player_name = ""
    if t_player_id == g_player_id:
        player_name = "You have"
    else:
        player_name = "{} has".format(g_player_dict[t_player_id]["name"])
    mylog.warning("notify_trump_buried: player_name=%s", player_name)
    count = data["count"]
    mylog.warning("notify_trump_buried: count=%d", count)

    InfoDialog(
        "Trump Buried",
        html.P(f"{player_name} buried {count} trump cards."),
        left=25,
        top=25,
        ok=True,
        remove_after=15,
    )


def record_trump_selection(event=None):
    """
    Convey the chosen trump to the user, as provided by the server.
    """
    mylog.error("Entering record_trump_selection.")
    # pylint: disable=invalid-name
    global g_trump
    data = json.loads(event)
    g_trump = str(data["trump"])

    remove_dialogs()
    InfoDialog(
        "Trump Selected",
        f"Trump for this round is: {g_trump.capitalize()}s",
        remove_after=15,
        ok=True,
        left=25,
        top=25,
    )


def reveal_kitty_card(event=None):
    """
    Reveal the provided card in the kitty.
    """
    mylog.error("Entering reveal_kitty_card.")
    data = json.loads(event)
    revealed_card = str(data["card"])

    if revealed_card not in g_kitty_deck:
        mylog.warning("%s is not in %r", revealed_card, g_kitty_deck)
        return

    for (objid, node) in g_canvas.objectDict.items():
        if (
            isinstance(node, SVG.UseObject)
            and "kitty" in objid
            and node.attrs["href"] == revealed_card
            and not node.attrs["show_face"]
        ):
            node.show_face = True
            node.flippable = False
            node.face_update_dom()


def display_bid_winner(event=None):
    """
    Display the round's bid winner.

    :param event: [description], defaults to None
    :type event: [type], optional
    """
    mylog.error("Entering display_bid_winner.")
    # pylint: disable=invalid-name
    global g_round_bid_trick_winner, g_round_bid
    data = json.loads(event)
    t_player_id = PlayerID(data["player_id"])
    player_name = g_player_dict[t_player_id]["name"]
    bid = int(data["bid"])

    remove_dialogs()

    InfoDialog(
        "Bid Winner",
        html.P(f"{player_name} has won the bid for {bid} points!"),
        left=25,
        top=25,
        ok=True,
        remove_after=15,
    )

    # You may have won...
    g_round_bid_trick_winner = t_player_id
    g_round_bid = bid


def display_player_meld(meld_data: str):
    """
    Display the meld hand submitted by a player in a pop-up.

    :param meld_data: Data from the event as a JSON string.
    :type meld_data: str
    """
    mylog.error("Entering display_player_meld.")
    data = json.loads(meld_data)
    player_id = PlayerID(data["player_id"])
    player_name = g_player_dict[player_id]["name"]
    card_list = data["card_list"]
    try:
        # If a dialog already exists, delete it.
        if existing_dialog := document.getElementById(f"dialog_{player_id.value}"):
            existing_dialog.parentNode.removeChild(existing_dialog)
    except Exception as e:  # pylint: disable=invalid-name,broad-except
        mylog.warning("display_player_meld: Caught exception: %r", e)
    try:
        # Construct the new dialog to display the meld cards.
        xpos = 0.0
        d_canvas = SVG.CanvasObject("40vw", "20vh", "none", objid="dialog_canvas")
        for card in card_list:
            # pylint: disable=expression-not-assigned
            d_canvas <= SVG.UseObject(href=f"#{card}", origin=(xpos, 0))
            xpos += CARD_WIDTH / 2.0
    except Exception as e:  # pylint: disable=invalid-name,broad-except
        mylog.warning("display_player_meld: Caught exception: %r", e)
        return
    InfoDialog(
        "Meld Cards",
        html.P(f"{player_name}'s meld cards are:") + d_canvas,
        left=25,
        top=25,
        ok=True,
    )
    mylog.warning(
        "display_player_meld: Items: %r",
        document.getElementsByClassName("brython-dialog-main"),
    )
    # Add an ID attribute so we can find it later if needed.
    for item in document.getElementsByClassName("brython-dialog-main"):
        mylog.warning("display_player_meld: Item: %r", item)
        if not item.id:
            # Assume this is the one we just created.
            item.id = f"dialog_{player_id.value}"

    d_canvas.fitContents()


def update_player_names(player_data: str):
    """
    Update the player names in the UI.

    :param player_data: JSON-formatted message from the server.
    :type player_data: str
    """
    # pylint: disable=invalid-name
    global g_registered_with_server, g_player_list

    data = json.loads(player_data)
    g_player_list = [PlayerID(x) for x in data["player_order"]]
    my_player_list = [PlayerID(x) for x in data["player_ids"]]
    # Display the player's name in the UI
    if my_player_list != [] and g_player_id in my_player_list:
        mylog.warning("Players: %r", my_player_list)

        g_registered_with_server = True
        document.getElementById("player_name").clear()
        document.getElementById("player_name").attach(
            html.SPAN(
                g_player_dict[g_player_id]["name"].capitalize(), Class="player_name",
            )
        )

        # TODO: Do something more useful like a line of names with color change when
        # the player's client registers.
        document.getElementById("other_players").clear()
        document.getElementById("other_players").attach(
            html.SPAN(
                ", ".join(
                    sorted(
                        y["name"].capitalize()
                        for y in [
                            g_player_dict[x] for x in my_player_list if x != g_player_id
                        ]
                    )
                ),
                Class="other_players",
            )
        )


def update_status_line():
    """
    Update the player status line with current information from globals.
    """
    document.getElementById("game_status").clear()
    document.getElementById("game_status").attach(html.BR())
    document.getElementById("game_status").attach(
        html.SPAN(
            f"Score: {g_my_team_score} / {g_other_team_score} ", Class="game_status"
        )
    )
    if g_trump:
        document.getElementById("game_status").attach(
            html.SPAN(f"Trump: {g_trump.capitalize()}s ", Class="game_status")
        )
    if g_round_bid:
        document.getElementById("game_status").attach(
            html.SPAN(f"Bid: {g_round_bid} ", Class="game_status")
        )
    if g_meld_score:
        document.getElementById("game_status").attach(
            html.SPAN(f"Meld score: {g_meld_score} ", Class="game_status")
        )


def send_registration():
    """
    Send registration structure to server.
    """
    mylog.error("In send_registration")
    if g_registered_with_server:
        return

    send_websocket_message(
        {
            "action": "register_client",
            "game_id": g_game_id.value,
            "player_id": g_player_id.value,
        }
    )


def send_websocket_message(message: dict):
    """
    Send message to server.
    """
    if g_websocket is None:
        mylog.warning("send_registration: Opening WebSocket.")
        ws_open()

    mylog.warning("send_registration: Sending message.")
    g_websocket.send(json.dumps(message))


def ajax_request_tracker(direction: int = 0):
    """
    Keep a tally of the currently outstanding AJAX requests.

    :param direction: Whether to increase or decrease the counter,
    defaults to 0 which does not affect the counter.
    :type direction: int, optional
    """
    # pylint: disable=invalid-name
    global g_ajax_outstanding_requests

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
        g_game_dict[GameID(item["game_id"])] = item

    display_game_options()


def on_complete_rounds(req: ajax.Ajax):
    """
    Callback for AJAX request for the list of rounds.

    :param req: Request object from callback.
    :type req: [type]
    """
    # pylint: disable=invalid-name
    global g_round_id, g_team_list
    mylog.error("Entering on_complete_rounds.")

    ajax_request_tracker(-1)
    g_team_list.clear()

    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the round ID.
    g_round_id = RoundID(temp["round_id"])
    mylog.warning("on_complete_rounds: round_id=%s", g_round_id)

    display_game_options()


def on_complete_teams(req: ajax.Ajax):
    """
    Callback for AJAX request for the information on the teams associated with the round.

    :param req: Request object from callback.
    :type req: [type]
    """
    # pylint: disable=invalid-name
    global g_team_list
    mylog.error("Entering on_complete_teams.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global list of teams for this round.
    g_team_list.clear()
    g_team_list = [TeamID(x) for x in temp["team_ids"]]
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
    # pylint: disable=invalid-name
    global g_team_dict
    mylog.error("Entering on_complete_team_names.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global dict of team names for this round.
    mylog.warning(
        "on_complete_team_names: Setting team_dict[%s]=%r", temp["team_id"], temp
    )
    g_team_dict[TeamID(temp["team_id"])] = temp
    mylog.warning("on_complete_team_names: team_dict=%s", g_team_dict)

    # Only call API once per team, per player.
    for item in g_team_dict[TeamID(temp["team_id"])]["player_ids"]:
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
    g_player_dict[PlayerID(temp["player_id"])] = temp
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
    # pylint: disable=invalid-name
    global g_game_mode, g_game_id, g_player_id, g_kitty_size, g_team_id, g_kitty_deck
    global g_hand_size, g_meld_deck
    mylog.error("Entering on_complete_getcookie.")

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
        g_game_id = GameID(response_data["ident"])
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
        # TODO: Figure out how better to calculate g_hand_size.
        g_hand_size = int((48 - g_kitty_size) / g_players)
        g_meld_deck = ["card-base" for _ in range(g_hand_size)]

    elif "player_id" in response_data["kind"]:
        g_player_id = PlayerID(response_data["ident"])
        mylog.warning(
            "on_complete_getcookie: Setting PLAYER_ID=%s", response_data["ident"]
        )
        get(f"/player/{g_player_id.value}/hand", on_complete_player_cards)

    display_game_options()


def on_complete_kitty(req: ajax.Ajax):
    """
    Callback for AJAX request for the round's kitty cards, if any.

    :param req: Request object from callback.
    :type req: [type]
    """
    # pylint: disable=invalid-name
    global g_kitty_deck
    mylog.error("Entering on_complete_kitty.")

    ajax_request_tracker(-1)
    mylog.warning("on_complete_kitty: req.text=%r", req.text)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global deck of cards for the kitty.
    g_kitty_deck.clear()
    g_kitty_deck = temp["cards"]
    mylog.warning("on_complete_kitty: kitty_deck=%s", g_kitty_deck)
    if g_player_id == g_round_bid_trick_winner:
        # Add the kitty cards to the bid winner's deck
        for card in g_kitty_deck:
            g_players_hand.append(card)
            g_players_meld_deck.append(card)
        advance_mode()


def on_complete_player_cards(req: ajax.Ajax):
    """
    Callback for AJAX request for the player's cards.

    :param req: Request object from callback.
    :type req: [type]
    """
    # pylint: disable=invalid-name
    global g_players_hand, g_players_meld_deck
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

    if req.status in [200, 0]:
        mylog.error("on_complete_get_meld_score: req.text: %s", req.text)
        mylog.warning("on_complete_get_meld_score: req.text: %s", req.text)
        temp = json.loads(req.text)
        InfoDialog(
            "Meld Score",
            f"Your meld score is {temp['score']}",
            remove_after=5,
            top=25,
            left=25,
        )
        mfd = MeldFinalDialog()
        mfd.display_meld_final_dialog()
        return

    mylog.warning("on_complete_get_meld_score: score: %r", req)


def on_complete_common(req: ajax.Ajax) -> Optional[str]:
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
    return None


def order_player_index_list_for_trick() -> List[int]:
    """
    Generate a list of indices in g_player_list starting with the current
    g_round_bid_trick_winner.

    :return: Re-ordered list of player indices.
    :rtype: List[str]
    """
    player_list_len = len(g_player_list)
    # Locate the index of the winner in the player list
    starting_index = g_player_list.index(g_round_bid_trick_winner)
    # Generate a list of indices for the players, starting with the
    # g_round_bid_trick_winner.
    return [(x + starting_index) % player_list_len for x in range(player_list_len)]


def order_player_id_list_for_trick() -> List[PlayerID]:
    """
    Generate a list of players from g_player_list starting with the current
    g_round_bid_trick_winner.

    :return: Re-ordered list of player ids.
    :rtype: List[str]
    """
    return [g_player_list[idx] for idx in order_player_index_list_for_trick()]


def order_player_name_list_for_trick() -> List[str]:
    """
    Generate a list of player names from g_player_list starting with the current
    g_round_bid_trick_winner.

    :return: Re-ordered list of player names.
    :rtype: List[str]
    """
    return [
        g_player_dict[p_id]["name"].capitalize()
        for p_id in order_player_id_list_for_trick()
    ]


def advance_mode_callback(req: ajax.Ajax):
    """
    Routine to capture the response of the server when advancing the game mode.

    :param req:   The request response passed in during callback
    :type req:    Request
    """
    # pylint: disable=invalid-name
    global g_game_mode
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

    remove_dialogs()

    display_game_options()


def game_mode_query_callback(req: ajax.Ajax):
    """
    Routine to capture the response of the server when advancing the game mode.

    :param req:   The request response passed in during callback
    :type req:    Request
    """
    # pylint: disable=invalid-name
    global g_game_mode
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

    display_game_options()


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


def put(url: str, callback=None, async_call=True):
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
    # mylog.warning("Calling PUT /api%s with data: %r", url, data)
    mylog.warning("Calling PUT /api%s", url)
    req.open("PUT", "/api" + url, async_call)
    req.set_header("content-type", AJAX_URL_ENCODING)
    # req.send({"a": a, "b":b})
    # req.send(data)
    req.send({})


def post(url: str, callback=None, async_call=True):
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
    # mylog.warning("Calling POST /api%s with data: %r", url, data)
    mylog.warning("Calling POST /api%s", url)
    req.open("POST", "/api" + url, async_call)
    req.set_header("content-type", AJAX_URL_ENCODING)
    # req.send(data)
    req.send({})


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


def locate_cards_below_hand() -> List[str]:
    """
    Identify cards that have been moved below the player's hand.
    """
    mylog.error("Entering locate_cards_below_hand.")
    return_list = []
    potential_cards = []
    min_y_coord = float(g_canvas.attrs["height"]) + 20
    for card in g_canvas.objectDict.values():
        if not isinstance(card, SVG.UseObject) or "player" not in card.id:
            continue
        min_y_coord = min(min_y_coord, float(card.attrs["y"]))
        potential_cards.append(card)
    for card in potential_cards:
        if float(card.attrs["y"]) > min_y_coord + CARD_HEIGHT / 4:
            mylog.warning(
                f"Card {card.attrs['href'].lstrip('#')} "
                + f"Y-coordinate: {card.attrs['y']}"
            )
            return_list.append(card.attrs["href"].lstrip("#"))

    return return_list


def clear_globals_for_round_change():
    """
    Clear some global variables in preparation for a new round.
    """
    # pylint: disable=invalid-name
    global discard_deck, g_round_id, g_round_bid_trick_winner, g_meld_deck
    mylog.error("Entering clear_globals_for_round_change.")

    g_round_id = RoundID()
    g_players_hand.clear()
    g_players_meld_deck.clear()
    g_meld_deck = ["card-base" for _ in range(g_hand_size)]
    discard_deck = ["card-base" for _ in range(len(g_player_list))]
    display_game_options()


def clear_globals_for_trick_change():
    """
    Clear some global variables in preparation for a new round.
    """
    # pylint: disable=invalid-name
    global discard_deck
    mylog.error("Entering clear_globals_for_trick_change.")

    discard_deck = ["card-base" for _ in range(len(g_player_list))]
    display_game_options()


def populate_canvas(deck, target_canvas: SVG.CanvasObject, deck_type="player"):
    """
    Populate given canvas with the deck of cards but without specific placement.

    :param deck: card names in the format that svg-cards.svg wants.
    :type deck: list
    :param target_canvas: [description]
    :type target_canvas: [type]
    :param deck_type: The "type" of deck populating the UI.
    :type deck_type: str
    """
    mylog.error("Entering populate_canvas.")

    if GAME_MODES[g_game_mode] in ["game"]:
        mylog.error("Exiting populate_canvas. Still in 'game' mode.")
        return

    mylog.warning(
        "populate_canvas(deck=%s target_canvas=%s deck_type=%s).",
        deck,
        target_canvas,
        deck_type,
    )

    # DOM ID Counter
    for counter, card_value in enumerate(deck):
        flippable = False
        movable = True
        show_face = True
        flippable = DECK_CONFIG[deck_type][g_game_mode]["flippable"]
        movable = DECK_CONFIG[deck_type][g_game_mode]["movable"]
        show_face = DECK_CONFIG[deck_type][g_game_mode]["show_face"]
        if "reveal" in GAME_MODES[g_game_mode]:
            if "kitty" in deck_type:
                flippable = g_player_id == g_round_bid_trick_winner
                # show_face = True
            if "player" in deck_type:
                movable = g_player_id == g_round_bid_trick_winner
        if "trick" in GAME_MODES[g_game_mode] and "player" in deck_type:
            # This makes the player's deck movable based on whether their card place
            # in the discard deck is 'blank' or occupied.
            player_index_in_discard_deck = order_player_id_list_for_trick().index(
                g_player_id
            )
            movable = discard_deck[player_index_in_discard_deck] == "card-base"
            mylog.warning(
                "populate_canvas: player_idx_in_discard: %d",
                player_index_in_discard_deck,
            )
            mylog.warning("populate_canvas: movable: %r", movable)

        # Add the card to the canvas.
        piece = PlayingCard(
            face_value=card_value,
            objid=f"{deck_type}{counter}",
            show_face=show_face,
            flippable=flippable,
            # movable=movable,
        )
        target_canvas.addObject(piece, fixed=not movable)
        if "trick" in deck_type:
            # Place player names under the trick deck in the order
            # they will be playing cards during the trick.
            mylog.warning("%s %s", counter, order_player_name_list_for_trick()[counter])
            player_name = order_player_name_list_for_trick()[counter]
            text = browser.svg.text(
                f"{player_name}",
                x=CARD_WIDTH * 0.75 * (counter - 1.5),
                y=CARD_HEIGHT * 0.85,
                text_anchor="middle",
                font_size=24,
                style={"stroke": "white", "fill": "white"},
                id=f"name_{deck_type}{counter}",
            )
            target_canvas <= text


def generate_place_static_box(canvas: SVG.CanvasObject):
    """
    Generate and place an SVG box that is the same size as a full player's hand.
    This should prevent excessive resizing of the display as the player's hand depletes
    during trick play.
    """
    start_y = 2.25 * CARD_HEIGHT
    xincr = CARD_WIDTH / 2
    start_x = -xincr * (g_hand_size / 2 + 0.5)

    # pylint: disable=expression-not-assigned
    canvas <= SVG.RectangleObject(
        pointlist=[
            (start_x - 10, start_y - 10),
            (start_x + 10 + (xincr * (g_hand_size + 1)), start_y + 10),
        ],
        fillcolour="#076324",
        linecolour="#076324",
    )


def place_cards(deck, target_canvas, location="top", deck_type="player"):
    """
    Place the supplied deck / list of cards in the correct position on the display.

    :param deck: card names in the format that svg-cards.svg wants.
    :type deck: list
    :param location: String of "top", "bottom", defaults to "top", instructing routine
    where to place the cards vertically.
    :type location: str, optional
    :param deck_type: The type of (sub)-deck this is.
    :type deck_type: str, optional # TODO: Should probably be enum-like
    """
    mylog.error("Entering place_cards(deck=%s, deck_type=%s).", deck, deck_type)

    # Determine the starting point and step size for the location and deck being placed.
    start_y = 0 if location.lower() == "top" else 1.25 * CARD_HEIGHT
    xincr = CARD_WIDTH / 2 if len(deck) > 4 else CARD_SMALLER_WIDTH
    start_x = (
        -xincr * (len(deck) / 2 + 0.5) if len(deck) > 4 else -xincr * len(deck) / 2
    )

    # Set the initial position
    xpos = start_x
    ypos = start_y
    mylog.warning("place_cards: Start position: (%4.2f, %4.2f)", xpos, ypos)

    # Iterate over canvas's child nodes and move any node
    # where deck_type matches the node's id
    for (objid, node) in target_canvas.objectDict.items():
        if isinstance(node, SVG.UseObject) and deck_type in objid:
            # NOTE: The centre argument to setPosition takes a tuple, so the double
            # parentheses are necessary.
            node.setPosition(
                (xpos, ypos),
                width=None if deck_type == "player" else CARD_SMALLER_WIDTH,
                height=None if deck_type == "player" else CARD_SMALLER_HEIGHT,
            )

            mylog.warning(
                "place_cards: Processing node %s. (xpos=%4.2f, ypos=%4.2f)",
                node.id,
                xpos,
                ypos,
            )

            # Each time through the loop, move the next card's starting position.
            xpos += xincr


def create_game_select_buttons(xpos, ypos) -> None:
    """
    Create a list of buttons for the player to choose a game to join.

    :param xpos:    Starting X position
    :type xpos:     float
    :param ypos:    Starting Y position
    :type ypos:     float
    """
    mylog.error("Entering create_game_select_buttons")
    mylog.warning("create_game_select_buttons: game_dict=%s", g_game_dict)

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
    else:
        mylog.warning("cgsb: Clearing canvas (%r)", g_canvas)
        g_canvas.deleteAll()

    # If there's only one game, choose that one.
    if len(g_game_dict) == 1:
        one_game_id = list(g_game_dict.keys())[0]
        get(f"/setcookie/game_id/{one_game_id.value}", on_complete_set_gamecookie)
        return

    mylog.warning("cgsb: Enumerating games for buttons (%d).", len(g_game_dict))
    for item, temp_dict in g_game_dict.items():
        mylog.warning("create_game_select_buttons: game_dict item: item=%s", item)
        game_button = SVG.Button(
            position=(xpos, ypos),
            size=(450, 35),
            text=f"Game: {temp_dict['timestamp'].replace('T',' ')}",
            onclick=choose_game,
            fontsize=18,
            objid=item.value,
        )
        g_canvas.attach(game_button)
        ypos += 40

    g_canvas.fitContents()
    mylog.warning("Exiting create_game_select_buttons")


def create_player_select_buttons(xpos, ypos) -> None:
    """
    Create a list of buttons for the player to identify themselves.

    :param xpos:    Starting X position
    :type xpos:     float
    :param ypos:    Starting Y position
    :type ypos:     float
    """
    g_canvas.deleteAll()

    for item in g_player_dict:
        mylog.warning("player_dict[item]=%s", g_player_dict[item])
        if not document.getElementById(g_player_dict[item]["player_id"]):
            player_button = SVG.Button(
                position=(xpos, ypos),
                size=(450, 35),
                text=f"Player: {g_player_dict[item]['name']}",
                onclick=choose_player,
                fontsize=18,
                objid=g_player_dict[item]["player_id"],
            )
            mylog.warning(
                "create_player_select_buttons: player_dict item: item=%s", item
            )
            g_canvas.attach(player_button)
        ypos += 40

    g_canvas.fitContents()
    mylog.warning("Exiting create_player_select_buttons")


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
    if g_game_id != GameID() and g_player_id != PlayerID():
        put(f"/game/{g_game_id.value}?state=true", advance_mode_callback, False)
    else:
        display_game_options()


def sort_player_cards(event=None):  # pylint: disable=unused-argument
    """
    Sort the player's cards.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    # pylint: disable=unnecessary-lambda
    g_players_hand.sort(key=lambda x: DECK_SORTED.index(x))
    g_players_meld_deck.sort(key=lambda x: DECK_SORTED.index(x))
    display_game_options()


def send_meld(event=None):  # pylint: disable=unused-argument
    """
    Send the meld deck to the server.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    card_string = ",".join(x for x in g_meld_deck if x != "card-base")

    mylog.error(
        "send_meld: /round/%s/score_meld?player_id=%s&cards=%s",
        g_round_id.value,
        g_player_id.value,
        card_string,
    )

    get(
        f"/round/{g_round_id.value}/score_meld?player_id={g_player_id.value}&cards={card_string}",
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
    # pylint: disable=invalid-name
    global g_game_mode, g_team_id, g_meld_score, g_round_bid, g_round_bid_trick_winner, g_trump
    mylog.error("Entering display_game_options.")

    xpos = 10
    ypos = 0

    # Grab the game_id, team_ids, and players. Display and allow player to choose.
    if g_game_id == GameID():
        mylog.warning("dgo: In g_game_id=''")
        create_game_select_buttons(xpos, ypos)
    elif g_game_mode is None:
        mylog.warning("dgo: In g_game_mode is None")
        get(f"/game/{g_game_id.value}?state=false", game_mode_query_callback)
    elif g_round_id == RoundID():
        mylog.warning("dgo: In g_round_id=''")
        # Open the websocket if needed.
        if g_websocket is None:
            ws_open()

        get(f"/game/{g_game_id.value}/round", on_complete_rounds)
    elif g_team_list == []:
        mylog.warning("dgo: In g_team_list=[]")
        get(f"/round/{g_round_id.value}/teams", on_complete_teams)
    elif g_player_id == PlayerID():
        mylog.warning("dgo: In g_player_id=''")
        create_player_select_buttons(xpos, ypos)
    elif g_players_hand == []:
        mylog.warning("dgo: In g_players_hand=[]")
        get(f"/player/{g_player_id.value}/hand", on_complete_player_cards)
    else:
        mylog.warning("dgo: In else clause")
        # Send the registration message.
        send_registration()

        if g_game_mode == 1:
            g_meld_score = 0
            g_round_bid = 0
            g_round_bid_trick_winner = PlayerID()
            g_trump = ""
            # update_status_line()

        if g_team_id == TeamID():
            # Set the g_team_id variable based on the player id chosen.
            for _temp in g_team_dict:
                mylog.warning(
                    "dgo: Key: %s Value: %r", _temp, g_team_dict[_temp]["player_ids"]
                )
                if g_player_id.value in g_team_dict[_temp]["player_ids"]:
                    g_team_id = TeamID(g_team_dict[_temp]["team_id"])
                    mylog.warning("dgo: Set g_team_id=%s", g_team_id)

        rebuild_display()


def rebuild_display(event=None):  # pylint: disable=unused-argument
    """
    Clear the display by removing everything from the canvas object, then re-add
    everything back. It also works for the initial creation and addition of the canvas to
    the overall DOM.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    # pylint: disable=invalid-name
    global g_game_mode, button_advance_mode, g_canvas
    mylog.error("Entering rebuild_display")

    if g_game_mode is None and not g_game_dict:
        g_game_mode = 0

    if g_ajax_outstanding_requests > 0:
        mylog.warning(
            "There are %d outstanding requests. Skipping clear.",
            g_ajax_outstanding_requests,
        )
        return

    update_status_line()

    mode = GAME_MODES[g_game_mode]
    mylog.warning("rebuild_display: Current mode=%s", mode)

    mylog.warning(
        "rebuild_display: Destroying canvas contents with mode: %s", g_canvas.mode
    )
    g_canvas.deleteAll()

    # Set the current game mode in the canvas.
    g_canvas.mode = mode

    # Get the dimensions of the canvas and update the display.
    set_card_positions()

    _buttons = {}  # Dict[str, SVG.Button]
    if "game" not in GAME_MODES[g_game_mode]:
        # Update/create buttons

        # # Button to call advance_mode on demand
        # _buttons["button_advance_mode"] = SVG.Button(
        #     position=(-80 * 3.5, -40),
        #     size=(70, 35),
        #     text=GAME_MODES[g_game_mode].capitalize(),
        #     onclick=advance_mode,
        #     fontsize=18,
        #     objid="button_advance_mode",
        # )
        # # Button to call update_display on demand
        # _buttons["button_refresh"] = SVG.Button(
        #     position=(-80 * 2.5, -40),
        #     size=(70, 35),
        #     text="Refresh",
        #     onclick=set_card_positions,
        #     fontsize=18,
        #     objid="button_refresh",
        # )

        # # Button to call clear_display on demand
        # _buttons["button_clear"] = SVG.Button(
        #     position=(-80 * 1.5, -40),
        #     size=(70, 35),
        #     text="Clear",
        #     onclick=rebuild_display,
        #     fontsize=18,
        #     objid="button_clear",
        # )

        # # Button to call clear_game on demand
        # _buttons["button_clear_game"] = SVG.Button(
        #     position=(80 * 0.5, -40),
        #     size=(70, 35),
        #     text="Clear\nGame",
        #     onclick=clear_game,
        #     fontsize=16,
        #     objid="button_clear_game",
        # )

        # # Button to call clear_player on demand
        # _buttons["button_clear_player"] = SVG.Button(
        #     position=(80 * 1.5, -40),
        #     size=(70, 35),
        #     text="Clear\nPlayer",
        #     onclick=clear_player,
        #     fontsize=16,
        #     objid="button_clear_player",
        # )

        # # Button to call window reload on demand
        # _buttons["button_reload_page"] = SVG.Button(
        #     position=(80 * 2.5, -40),
        #     size=(70, 35),
        #     text="Reload",
        #     onclick=window.location.reload,  # pylint: disable=no-member
        #     fontsize=16,
        #     objid="button_reload_page",
        # )

        # Button to call sort_player_cards on demand
        _buttons["button_sort_player"] = SVG.Button(
            position=(-80 * 0.5, CARD_HEIGHT * 1.1),
            size=(70, 35),
            text="Sort",
            onclick=sort_player_cards,
            fontsize=18,
            objid="button_sort_player",
        )

    if GAME_MODES[g_game_mode] in ["reveal"]:
        mylog.warning("rebuild_display: Creating trump selection dialog.")
        tsd = TrumpSelectDialog()
        tsd.display_trump_dialog()

    if GAME_MODES[g_game_mode] in ["meld"]:
        # Button to call submit_meld on demand
        _buttons["button_send_meld"] = SVG.Button(
            position=(-80 * 0.5, -40),
            size=(70, 35),
            text="Send\nMeld",
            onclick=send_meld,
            fontsize=16,
            objid="button_send_meld",
        )

    for item, button in _buttons.items():
        mylog.warning("rebuild_display: Adding %s button to canvas.", item)
        g_canvas.addObject(button)

    g_canvas.fitContents()
    # pylint: disable=attribute-defined-outside-init, invalid-name
    g_canvas.mouseMode = SVG.MouseMode.DRAG
    mylog.warning("Leaving rebuild_display")


def set_card_positions(event=None):  # pylint: disable=unused-argument
    """
    Populate and place cards based on the game's current mode. This needs a little more
    work to support more aspects of the game.

    :param event: The event object passed in during callback, defaults to None
    :type event: [type], optional
    """
    # pylint: disable=invalid-name
    global g_game_mode
    mode = GAME_MODES[g_game_mode]
    mylog.error("Entering update_display. (mode=%s)", mode)

    # Place the desired decks on the display.
    if not g_canvas.objectDict:
        if mode in ["game"] and g_game_id == GameID():  # Choose game, player
            display_game_options()
        if mode not in ["game"]:
            generate_place_static_box(g_canvas)
        if mode in ["bid", "bidfinal"]:  # Bid
            # Use empty deck to prevent peeking at the kitty.
            populate_canvas(g_kitty_deck, g_canvas, "kitty")
            populate_canvas(g_players_hand, g_canvas, "player")
        if mode in ["bidfinal"]:  # Bid submitted
            # The kitty doesn't need to remain 'secret' now that the bidding is done.
            # Ask the server for the cards in the kitty.
            if g_round_id != RoundID():
                get(f"/round/{g_round_id.value}/kitty", on_complete_kitty)
        elif mode in ["reveal"]:  # Reveal
            populate_canvas(g_kitty_deck, g_canvas, "kitty")
            populate_canvas(g_players_hand, g_canvas, "player")
        elif mode in ["meld"]:  # Meld
            populate_canvas(g_meld_deck, g_canvas, mode)
            populate_canvas(g_players_meld_deck, g_canvas, "player")
        elif mode in ["trick"]:  # Trick
            populate_canvas(discard_deck, g_canvas, mode)
            populate_canvas(g_players_hand, g_canvas, "player")

    # Last-drawn are on top (z-index wise)
    # TODO: Retrieve events from API to show kitty cards when they are flipped over.
    if mode in ["bid", "bidfinal", "reveal"]:  # Bid & Reveal
        place_cards(g_kitty_deck, g_canvas, location="top", deck_type="kitty")
        place_cards(g_players_hand, g_canvas, location="bottom", deck_type="player")
    elif mode in ["meld"]:  # Meld
        # TODO: Expand display to show all four players.
        place_cards(g_meld_deck, g_canvas, location="top", deck_type=mode)
        place_cards(
            g_players_meld_deck, g_canvas, location="bottom", deck_type="player"
        )
    elif mode in ["trick"]:  # Trick
        # Remove any dialogs from the meld phase.
        remove_dialogs()
        place_cards(discard_deck, g_canvas, location="top", deck_type=mode)
        place_cards(g_players_hand, g_canvas, location="bottom", deck_type="player")

    # pylint: disable=attribute-defined-outside-init, invalid-name
    g_canvas.mouseMode = SVG.MouseMode.DRAG


def resize_canvas(event=None):  # pylint: disable=unused-argument
    """
    Resize the canvas to make use of available screen space.
    :param event: The event object passed in during callback, defaults to None
    """
    mylog.error("Entering resize_canvas")
    _height: float = 0.95 * window.innerHeight - document["game_header"].height
    g_canvas.style.height = f"{_height}px"
    g_canvas.fitContents()


## END Function definitions.

# Gather information about where we're coming from.
(PROTOCOL, SERVER) = find_protocol_server()

# Make the clear_display function easily available to plain javascript code.
window.bind("resize", resize_canvas)  # pylint: disable=no-member

# Fix the height of the space for player names by using dummy names
document["player_name"].height = document["player_name"].offsetHeight

# Attach the card graphics file
document["card_definitions"].attach(SVG.Definitions(filename=CARD_URL))

# Create the base SVG object for the card table.
g_canvas = CardTable()
document["card_table"] <= g_canvas
resize_canvas()

# Declare temporary decks
discard_deck = ["card-base" for _ in range(g_players)]

document.getElementById("please_wait").remove()

# Pre-populate some data. Each of these calls display_game_options.
get("/game", on_complete_games)
get("/getcookie/game_id", on_complete_getcookie)
get("/getcookie/player_id", on_complete_getcookie)
