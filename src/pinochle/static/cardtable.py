"""
In-browser script to handle the card-table user interface.
"""
import copy
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import brySVG.dragcanvas as SVG  # pylint: disable=import-error
from browser import ajax, document, html, websocket, window
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


@dataclass(frozen=True)
class BaseID:
    """
    Parent container for string-ified GUIDs / UUIDs used as identifers by the card
    service.
    """

    zeros_uuid = "00000000-0000-0000-0000-000000000000"
    value: str

    def __init__(self, value: str = zeros_uuid) -> None:
        object.__setattr__(self, "value", str(value))

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other) -> bool:
        return self.value == other.value


class GameID(BaseID):  # pylint: disable=too-few-public-methods
    """
    Game ID data
    """


class RoundID(BaseID):  # pylint: disable=too-few-public-methods
    """
    Round ID data
    """


class TeamID(BaseID):  # pylint: disable=too-few-public-methods
    """
    Team ID data
    """


class PlayerID(BaseID):  # pylint: disable=too-few-public-methods
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
        mylog.error("In PlayingCard.__init__.")

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
        mylog.error("In PlayingCard.face_update_dom.")

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
        mylog.error("In PlayingCard: play_handler.")

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
        card_tag = GAME_MODES[GameState.game_mode]

        # Protect the player's deck during meld process.
        # Create a reference to the appropriate deck by mode.
        receiving_deck = []
        sending_deck = []
        # This "should never be called" during GAME_MODEs 0 or 1.
        add_only = False
        if GAME_MODES[GameState.game_mode] in ["reveal"]:  # Bury
            if "player" in self.id:
                parent_canvas.translateObject(
                    parent_canvas.objectDict[f"{self.id}"], (0, CARD_HEIGHT / 1.9)
                )
        elif GAME_MODES[GameState.game_mode] in ["meld"]:  # Meld
            if True or "player" in self.id:
                sending_deck = GameState.players_meld_deck  # Deep copy
                receiving_deck = GameState.meld_deck  # Reference
            else:
                add_only = True
                card_tag = "player"
                sending_deck = GameState.meld_deck  # Reference
                receiving_deck = GameState.players_meld_deck  # Deep copy
        elif GAME_MODES[GameState.game_mode] in ["trick"]:  # Trick
            sending_deck = GameState.players_hand  # Reference
            receiving_deck = g_discard_deck  # Reference

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
        mylog.error("In PlayingCard: handle_discard_placement.")

        # Cards are placed in a specific order when in trick mode. Otherwise,
        # the first available empty (card-base) slot is used.
        if GAME_MODES[GameState.game_mode] in ["trick"]:
            p_list: List[PlayerID] = order_player_id_list_for_trick()
            placement: int = p_list.index(GameState.player_id)
        elif GAME_MODES[GameState.game_mode] in ["meld"]:
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

        if GAME_MODES[GameState.game_mode] in ["trick"]:
            mylog.warning("Throwing card: %s", self.face_value)
            # Convey the played card to the server.
            put(
                f"/play/{GameState.round_id.value}/play_card?player_id={GameState.player_id.value}&card={self.face_value}"
            )

    def card_click_handler(self):
        """
        Click handler for the playing card. The action depends on the game mode.
        Since the only time this is done is during the meld process, also call the API to
        notify it that a kitty card has been flipped over and which card that is.
        """
        mylog.error("In PlayingCard.card_click_handler()")

        if GAME_MODES[GameState.game_mode] in ["reveal"] and self.flippable:
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
                    "game_id": GameState.game_id.value,
                    "player_id": GameState.player_id.value,
                    "card": self.face_value,
                }
            )
        if GAME_MODES[GameState.game_mode] in ["reveal", "meld", "trick"]:
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


class GameState:
    """
    Class to maintain state of the game from this player's point of view.
    """

    # ID of the game I'm playing
    game_id: GameID = GameID()
    # Round ID of the game I'm playing
    round_id: RoundID = RoundID()
    # My team ID
    team_id: TeamID = TeamID()
    # My player ID
    player_id: PlayerID = PlayerID()

    game_mode: int = -1
    hand_size: int = 0
    kitty_size: int = 0
    meld_score: int = 0
    my_team_score: int = 0
    other_team_score: int = 0
    players: int = 4
    round_bid: int = 0
    trump: str = ""

    # Games available on the server
    game_dict: Dict[GameID, Dict[str, Any]] = {}
    # Teams associated with this game/round
    team_dict: Dict[TeamID, Dict[str, str]] = {}
    team_list: List[TeamID] = []
    # Players associated with this game/round
    player_dict: Dict[PlayerID, Dict[str, str]] = {}
    player_list: List[PlayerID] = []
    # Track the user who is the round's bid winner, and each trick winner.
    round_bid_trick_winner: PlayerID

    # My hand of cards
    players_hand: List[str] = []
    # Deck of cards for the kitty.
    kitty_deck: List[str] = []
    # Deck of cards submitted to the server as meld.
    meld_deck: List[str] = []
    # Temporary deck for filling meld deck.
    players_meld_deck: List[str] = []

    @classmethod
    def other_team_id(cls) -> TeamID:
        """
        Given the class's knowledge of my team, return the ID of the other team.

        :return: ID of the "other" team
        :rtype: TeamID
        """
        return [x for x in cls.team_dict if x != cls.team_id][0]

    @classmethod
    def my_team_name(cls) -> str:
        """
        Return my team's name.

        :return: String representing the name of my team.
        :rtype: str
        """
        return cls.team_dict[cls.team_id]["team_name"].capitalize()

    @classmethod
    def other_team_name(cls) -> str:
        """
        Return my team's name.

        :return: String representing the name of my team.
        :rtype: str
        """
        return cls.team_dict[cls.other_team_id()]["team_name"].capitalize()

    @classmethod
    def my_name(cls) -> str:
        """
        Return my name.

        :return: String representing my name.
        :rtype: str
        """
        return cls.player_dict[cls.player_id]["name"].capitalize()

    @classmethod
    def other_players_name(cls, player_id: PlayerID) -> str:
        """
        Return my name.

        :return: String representing my name.
        :rtype: str
        """
        return cls.player_dict[player_id]["name"].capitalize()


# Various state globals
g_ajax_outstanding_requests: int = 0
# button_advance_mode = None  # pylint: disable=invalid-name
g_registered_with_server = False  # pylint: disable=invalid-name


class CardTable(SVG.CanvasObject):  # pylint: disable=too-few-public-methods
    """
    Class to encapsulate aspects of the card table.
    """

    def __init__(self):
        mylog.error("In CardTable.__init__.")

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
        mylog.error("In CardTable.move_handler")

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
        mylog.error("In BidDialog.on_click_bid_dialog.")

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
            f"/play/{GameState.round_id.value}/submit_bid?player_id={GameState.player_id.value}&bid={bid}"
        )

    def display_bid_dialog(self, data: Dict):
        """
        Display the meld hand submitted by a player in a pop-up.

        :param bid_data: Data from the event as a JSON string.
        :type bid_data: str
        """
        mylog.error("Entering display_bid_dialog.")
        t_player_id: PlayerID = PlayerID(data["player_id"])
        self.last_bid = int(data["bid"])
        player_name = GameState.my_name()

        remove_dialogs()

        # Don't display a dialog box if this isn't the player bidding.
        if GameState.player_id != t_player_id:
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
        mylog.error("In TrumpSelectDialog.on_click_trump_dialog")

        trump = event.target.id
        cards_buried = locate_cards_below_hand()
        mylog.warning("on_click_trump_dialog: You buried these cards: %r", cards_buried)
        if not trump:
            return
        if len(cards_buried) != GameState.kitty_size:
            InfoDialog(
                "Try again...",
                f"You buried {len(cards_buried)}, but {GameState.kitty_size} cards are required."
                + "Pressing the sort button will reset your choices.",
                ok=True,
                remove_after=15,
            )
            return
        self.trump_dialog.close()
        # Notify the server of trump.
        put(
            f"/play/{GameState.round_id.value}/set_trump?player_id={GameState.player_id.value}&trump={trump}"
        )
        # Transfer cards into the team's collection and out of the player's hand.
        buried_trump = 0
        for card in cards_buried:
            put(
                f"/round/{GameState.round_id.value}/{GameState.team_id.value}?card={card}"
            )
            delete(f"/player/{GameState.player_id.value}/hand/{card}")
            GameState.players_hand.remove(card)
            GameState.players_meld_deck.remove(card)
            if trump in card:
                buried_trump += 1
        if buried_trump > 0:
            send_websocket_message(
                {
                    "action": "trump_buried",
                    "game_id": GameState.game_id.value,
                    "player_id": GameState.player_id.value,
                    "count": buried_trump,
                }
            )

    def display_trump_dialog(self):
        """
        Prompt the player to select trump.
        """
        mylog.error("In TrumpSelectDialog.display_trump_dialog.")

        # Clear previous dialog_trump instances.
        try:
            previous = g_canvas.getSelectedObject("dialog_trump")
            g_canvas.removeObject(previous)
        except AttributeError:
            pass
        # Don't display a trump select dialog box if this isn't the player who won the
        # bid. Instead let the players know we're waiting for input.
        if GameState.player_id != GameState.round_bid_trick_winner:
            try:
                bid_winner_name = GameState.player_dict[
                    GameState.round_bid_trick_winner
                ]["name"].capitalize()
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

        player_name = GameState.my_name()
        if GameState.kitty_size:
            instructions = f"{player_name}, please move {GameState.kitty_size} cards BELOW your hand, then select a suit to be trump."
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
        mylog.error("In MeldFinalDialog.on_click_meld_dialog")

        # Notify the server of my meld is final.
        put(
            f"/play/{GameState.round_id.value}/finalize_meld?player_id={GameState.player_id.value}"
        )
        self.meld_final_dialog.close()

    def display_meld_final_dialog(self):
        """
        Prompt the player to select whether their meld is final.
        """
        mylog.error("In MeldFinalDialog.display_meld_final_dialog.")

        self.meld_final_dialog = Dialog(
            "Is your meld submission final?", ok_cancel=["Yes", "No"]
        )
        player_name = GameState.my_name()
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
        mylog.error("In TrickWonDialog.on_click_trick_won_dialog.")

        if not event.currentTarget.text:
            return

        # Convey to the server that play is continuing.
        put(
            f"/play/{GameState.round_id.value}/next_trick?player_id={GameState.player_id.value}"
        )
        self.trick_won_dialog.close()

    def on_click_final_trick_won_dialog(self, event=None):
        """
        Handle the click event for the next round/ok buttons.

        :param event: [description], defaults to None
        :type event: [type], optional
        """
        mylog.error("In TrickWonDialog.on_click_final_trick_won_dialog")

        if not event.currentTarget.text:
            return

        # Convey to the server that to start the next round.
        put(f"/game/{GameState.game_id.value}?state=true", advance_mode_callback, False)
        self.trick_won_dialog.close()

    def display_trick_won_dialog(self):
        """
        Display the trick has been won dialog to the player who won the trick.
        """
        mylog.error("In TrickWonDialog.display_trick_won_dialog.")

        self.trick_won_dialog = Dialog(
            "Trick complete", ok_cancel=["Next trick", "Ok"], top=25,
        )
        # pylint: disable=expression-not-assigned
        self.trick_won_dialog.panel <= html.DIV(
            f"{GameState.my_name()}, you won the trick!"
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
        mylog.error("In TrickWonDialog.display_final_trick_dialog.")

        self.trick_won_dialog = Dialog(
            "Final trick complete", ok_cancel=["Next round", "Ok"], top=25,
        )
        # pylint: disable=expression-not-assigned
        self.trick_won_dialog.panel <= html.DIV(
            f"{GameState.my_name()}, you won the trick! "
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
        # "g_canvas": g_canvas,
        # "GameState.game_id":      GameState.game_id,
        # "GameState.game_mode":    GameState.game_mode,
        # "GameState.round_id":     GameState.round_id,
        # "GameState.team_list":    GameState.team_list,
        # "GameState.player_id":    GameState.player_id,
        # "GameState.player_list":  GameState.player_list,
        # "GameState.players_hand": GameState.players_hand,
        # "GameState.game_dict":    GameState.game_dict,
        "GameState.kitty_size": GameState.kitty_size,
        "GameState.kitty_deck": GameState.kitty_deck,
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
    mylog.error("In find_protocol_server.")

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
    # pylint: disable=invalid-name
    global g_websocket
    mylog.error("In ws_open.")

    if not websocket.supported:
        InfoDialog("websocket", "WebSocket is not supported by your browser")
        return

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
    global g_websocket, g_registered_with_server  # pylint: disable=invalid-name
    mylog.error("on_ws_close: Connection has closed")

    g_websocket = None
    g_registered_with_server = False
    # set_timeout(ws_open, 1000)


def on_ws_error(event=None):
    """
    Callback for Websocket error event.
    """
    mylog.error("on_ws_error: Connection has experienced an error")
    mylog.warning("on_ws_error: event=%r", event)


def on_ws_event(event=None):
    """
    Callback for Websocket event from server. This method handles much of the state
    change in the user interface.

    :param event: Event object from ws event.
    :type event: [type]
    """
    mylog.error("In on_ws_event.")

    t_data = json.loads(event.data)
    mylog.warning("on_ws_event: %s", event.data)

    if "action" not in t_data:
        return

    actions = {
        "game_start": start_game_and_clear_round_globals,
        "notification_player_list": update_player_names,
        "game_state": set_game_state_from_server,
        "bid_prompt": BidDialog().display_bid_dialog,
        "bid_winner": display_bid_winner,
        "reveal_kitty": reveal_kitty_card,
        "trump_selected": record_trump_selection,
        "trump_buried": notify_trump_buried,
        "meld_update": display_player_meld,
        "team_score": update_team_scores,
        "trick_card": update_trick_card,
        "trick_won": update_trick_winner,
        "trick_next": clear_globals_for_trick_change,
        "score_round": update_round_final_score,
    }

    # Dispatch action
    actions[t_data["action"]](t_data)


def update_round_final_score(data: Dict):
    """
    Notify players that the final trick has been won.

    :param event: [description], defaults to None
    :type event: [type], optional
    """
    mylog.error("In update_round_final_score.")

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
    GameState.round_bid_trick_winner = t_player_id

    # Obtain the other team's ID
    t_other_team_id = GameState.other_team_id()

    mylog.warning("update_round_final_score: Setting my team name")
    my_team = GameState.my_team_name()
    mylog.warning("update_round_final_score: Setting other team's name")
    other_team = GameState.other_team_name()
    mylog.warning("update_round_final_score: Setting score variables")
    my_scores, other_scores = (
        t_team_trick_scores[GameState.team_id],
        t_team_trick_scores[t_other_team_id],
    )

    # TODO: Handle case where bid winner's team doesn't make the bid.
    mylog.warning("update_round_final_score: Setting global team scores.")
    GameState.my_team_score, GameState.other_team_score = (
        t_team_scores[GameState.team_id],
        t_team_scores[t_other_team_id],
    )

    mylog.warning(
        "GameState.player_id=%s / t_player_id=%s", GameState.player_id, t_player_id
    )
    if GameState.player_id == t_player_id:
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
            f"{GameState.other_players_name(t_player_id)} won the final trick. "
            + f"Trick Scores: {my_team}: {my_scores} points / {other_team}: {other_scores} points",
            top=25,
            left=25,
        )


def update_trick_winner(data: Dict):
    """
    Notify players that the trick has been won.

    :param event: [description], defaults to None
    :type event: [type], optional
    """
    mylog.error("In update_trick_winner.")
    mylog.warning("update_trick_winner: data=%s", data)

    assert isinstance(data, dict)
    t_player_id = PlayerID(data["player_id"])
    t_card = data["winning_card"]
    mylog.warning("update_trick_winner: t_player_id=%s", t_player_id)
    mylog.warning("update_trick_winner: t_card=%s", t_card)

    # Find the first instance of the winning card in the list.
    card_index = g_discard_deck.index(t_card)
    # Correlate that to the player_id who threw it.
    t_player_id = order_player_id_list_for_trick()[card_index]
    mylog.warning("update_trick_winner: t_player_id=%s", t_player_id)
    # Record that information.
    GameState.round_bid_trick_winner = t_player_id

    if GameState.player_id == t_player_id:
        TrickWonDialog().display_trick_won_dialog()
    else:
        InfoDialog(
            "Trick Won",
            f"{GameState.other_players_name(t_player_id)} won the trick.",
            top=25,
            left=25,
        )


def update_trick_card(data: Dict):
    """
    Place the thrown card in the player's slot for this trick.

    :param event: [description], defaults to None
    :type event: [type], optional
    """
    mylog.error("Entering update_trick_card.")
    mylog.warning("update_trick_card: data=%s", data)

    assert isinstance(data, dict)
    t_player_id: PlayerID = PlayerID(data["player_id"])
    t_card = data["card"]
    mylog.warning("update_trick_card: t_player_id=%s", t_player_id)
    mylog.warning("update_trick_card: t_card=%s", t_card)
    g_discard_deck[order_player_id_list_for_trick().index(t_player_id)] = t_card

    # Set the player's hand to unmovable until the trick is over.
    rebuild_display()


def update_team_scores(data: Dict):
    """
    Notify players that trump has been buried.

    :param event: [description], defaults to None
    :type event: [type], optional
    """
    # pylint: disable=invalid-name

    mylog.warning("update_team_scores: data=%r", data)
    assert isinstance(data, dict)
    if GameState.team_id == TeamID(data["team_id"]):
        GameState.my_team_score = data["score"]
        GameState.meld_score = data["meld_score"]
    else:  # Other team
        GameState.other_team_score = data["score"]

    update_status_line()


def notify_trump_buried(data: Dict):
    """
    Notify players that trump has been buried.

    :param event: [description], defaults to None
    :type event: [type], optional
    """
    mylog.error("Entering notify_trump_buried.")
    mylog.warning("notify_trump_buried: data=%r", data)

    assert isinstance(data, dict)
    if "player_id" in data:
        mylog.warning("notify_trump_buried: About to retrieve player_id from data")
        t_player_id: PlayerID = PlayerID(data["player_id"])
    else:
        t_player_id = PlayerID()
    mylog.warning("notify_trump_buried: t_player_id=%r", t_player_id)
    player_name = ""
    if t_player_id == GameState.player_id:
        player_name = "You have"
    else:
        player_name = "{} has".format(GameState.other_players_name(t_player_id))
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


def record_trump_selection(data: Dict):
    """
    Convey the chosen trump to the user, as provided by the server.
    """

    GameState.trump = str(data["trump"])

    remove_dialogs()
    InfoDialog(
        "Trump Selected",
        f"Trump for this round is: {GameState.trump.capitalize()}s",
        remove_after=15,
        ok=True,
        left=25,
        top=25,
    )


def reveal_kitty_card(data: Dict):
    """
    Reveal the provided card in the kitty.
    """
    mylog.error("Entering reveal_kitty_card.")

    revealed_card = str(data["card"])

    if revealed_card not in GameState.kitty_deck:
        mylog.warning("%s is not in %r", revealed_card, GameState.kitty_deck)
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


def display_bid_winner(data: Dict):
    """
    Display the round's bid winner.

    :param event: [description], defaults to None
    :type event: [type], optional
    """

    t_player_id = PlayerID(data["player_id"])
    player_name = GameState.other_players_name(t_player_id)
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
    GameState.round_bid_trick_winner = t_player_id
    GameState.round_bid = bid


def display_player_meld(data: Dict):
    """
    Display the meld hand submitted by a player in a pop-up.

    :param meld_data: Data from the event as a JSON string.
    :type meld_data: str
    """
    mylog.error("Entering display_player_meld.")

    player_id = PlayerID(data["player_id"])
    player_name = GameState.other_players_name(player_id)
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


def update_player_names(data: Dict):
    """
    Update the player names in the UI.

    :param player_data: JSON-formatted message from the server.
    :type player_data: str
    """
    # pylint: disable=invalid-name
    global g_registered_with_server
    mylog.error("In update_player_names.")

    GameState.player_list = [PlayerID(x) for x in data["player_order"]]
    my_player_list = [PlayerID(x) for x in data["player_ids"]]
    # Display the player's name in the UI
    if my_player_list != [] and GameState.player_id in my_player_list:
        mylog.warning("Players: %r", my_player_list)

        g_registered_with_server = True
        document.getElementById("player_name").clear()
        document.getElementById("player_name").attach(
            html.SPAN(GameState.my_name(), Class="player_name",)
        )

        # TODO: Do something more useful like a line of names with color change when
        # the player's client registers.
        document.getElementById("other_players").clear()
        document.getElementById("other_players").attach(
            html.SPAN(
                ", ".join(
                    sorted(
                        GameState.other_players_name(x)
                        for x in my_player_list
                        if x != GameState.player_id
                    )
                ),
                Class="other_players",
            )
        )
        if len(my_player_list) < len(GameState.player_dict):
            document.getElementById(
                "please_wait"
            ).text = "Waiting for all players to join the game."
        else:
            document.getElementById("please_wait").remove()


def set_game_state_from_server(data: Dict):
    """
    Set game state from webservice message.

    :param data: Data from the webservice message.
    :type data: Dict
    """
    mylog.error("In set_game_state_from_server.")

    GameState.game_mode = data["state"]
    display_game_options()


def start_game_and_clear_round_globals(data: Dict):
    """
    Start game and clear round globals.

    :param data: Data from the webservice message.
    :type data: Dict
    """
    mylog.error("In start_game_and_clear_round_globals.")

    GameState.game_mode = data["state"]
    mylog.warning(
        "on_ws_event: game_start: GameState.player_list=%r", GameState.player_list
    )
    clear_globals_for_round_change()


def update_status_line():
    """
    Update the player status line with current information from globals.
    """
    mylog.error("In update_status_line.")

    document.getElementById("game_status").clear()
    document.getElementById("game_status").attach(html.BR())
    document.getElementById("game_status").attach(
        html.SPAN(
            f"Score: {GameState.my_team_score} / {GameState.other_team_score} ",
            Class="game_status",
        )
    )
    if GameState.trump:
        document.getElementById("game_status").attach(
            html.SPAN(f"Trump: {GameState.trump.capitalize()}s ", Class="game_status")
        )
    if GameState.round_bid:
        document.getElementById("game_status").attach(
            html.SPAN(f"Bid: {GameState.round_bid} ", Class="game_status")
        )
    if GameState.meld_score:
        document.getElementById("game_status").attach(
            html.SPAN(f"Meld score: {GameState.meld_score} ", Class="game_status")
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
            "game_id": GameState.game_id.value,
            "player_id": GameState.player_id.value,
        }
    )


def send_websocket_message(message: dict):
    """
    Send message to server.
    """
    mylog.error("In send_websocket_message.")

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
    mylog.error("In ajax_request_tracker.")

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
    mylog.error("In on_complete_games.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global game list.
    GameState.game_dict.clear()
    for item in temp:
        mylog.warning("on_complete_games: item=%s", item)
        GameState.game_dict[GameID(item["game_id"])] = item

    display_game_options()


def on_complete_rounds(req: ajax.Ajax):
    """
    Callback for AJAX request for the list of rounds.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_rounds.")

    ajax_request_tracker(-1)
    GameState.team_list.clear()

    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the round ID.
    GameState.round_id = RoundID(temp["round_id"])
    mylog.warning("on_complete_rounds: round_id=%s", GameState.round_id)

    display_game_options()


def on_complete_teams(req: ajax.Ajax):
    """
    Callback for AJAX request for the information on the teams associated with the round.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_teams.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global list of teams for this round.
    GameState.team_list.clear()
    GameState.team_list = [TeamID(x) for x in temp["team_ids"]]
    mylog.warning("on_complete_teams: team_list=%r", GameState.team_list)

    # Clear the team dict here because of the multiple callbacks.
    GameState.team_dict.clear()
    for item in GameState.team_list:
        get(f"/team/{item}", on_complete_team_names)


def on_complete_team_names(req: ajax.Ajax):
    """
    Callback for AJAX request for team information.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_team_names.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global dict of team names for this round.
    mylog.warning(
        "on_complete_team_names: Setting team_dict[%s]=%r", temp["team_id"], temp
    )
    GameState.team_dict[TeamID(temp["team_id"])] = temp
    mylog.warning("on_complete_team_names: team_dict=%s", GameState.team_dict)

    # Only call API once per team, per player.
    for item in GameState.team_dict[TeamID(temp["team_id"])]["player_ids"]:
        mylog.warning("on_complete_team_names: calling get/player/%s", item)
        get(f"/player/{item}", on_complete_players)


def on_complete_players(req: ajax.Ajax):
    """
    Callback for AJAX request for player information.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_players.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global dict of players for reference later.
    GameState.player_dict[PlayerID(temp["player_id"])] = temp
    mylog.warning("In on_complete_players: player_dict=%s", GameState.player_dict)
    display_game_options()


def on_complete_set_gamecookie(req: ajax.Ajax):
    """
    Callback for AJAX request for setcookie information.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_set_gamecookie.")

    ajax_request_tracker(-1)
    if req.status in [200, 0]:
        get("/getcookie/game_id", on_complete_getcookie)


def on_complete_set_playercookie(req: ajax.Ajax):
    """
    Callback for AJAX request for setcookie information.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_set_playercookie.")

    ajax_request_tracker(-1)
    if req.status in [200, 0]:
        get("/getcookie/player_id", on_complete_getcookie)


def on_complete_getcookie(req: ajax.Ajax):
    """
    Callback for AJAX request for setcookie information.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_getcookie.")

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
        GameState.game_id = GameID(response_data["ident"])
        mylog.warning(
            "on_complete_getcookie: Setting GAME_ID=%s", response_data["ident"]
        )
        # put({}, f"/game/{GameState.game_id}?state=false", advance_mode_initial_callback, False)

        try:
            GameState.kitty_size = int(
                GameState.game_dict[GameState.game_id]["kitty_size"]
            )
            mylog.warning("on_complete_getcookie: KITTY_SIZE=%s", GameState.kitty_size)
            if GameState.kitty_size > 0:
                GameState.kitty_deck = [
                    "card-base" for _ in range(GameState.kitty_size)
                ]
            else:
                GameState.kitty_deck.clear()
        except KeyError:
            pass
        # TODO: Figure out how better to calculate GameState.hand_size.
        GameState.hand_size = int((48 - GameState.kitty_size) / GameState.players)
        GameState.meld_deck = ["card-base" for _ in range(GameState.hand_size)]

    elif "player_id" in response_data["kind"]:
        GameState.player_id = PlayerID(response_data["ident"])
        mylog.warning(
            "on_complete_getcookie: Setting PLAYER_ID=%s", response_data["ident"]
        )
        get(f"/player/{GameState.player_id.value}/hand", on_complete_player_cards)

    display_game_options()


def on_complete_kitty(req: ajax.Ajax):
    """
    Callback for AJAX request for the round's kitty cards, if any.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_kitty.")

    ajax_request_tracker(-1)
    mylog.warning("on_complete_kitty: req.text=%r", req.text)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global deck of cards for the kitty.
    GameState.kitty_deck.clear()
    GameState.kitty_deck = temp["cards"]
    mylog.warning("on_complete_kitty: kitty_deck=%s", GameState.kitty_deck)
    if GameState.player_id == GameState.round_bid_trick_winner:
        # Add the kitty cards to the bid winner's deck
        for card in GameState.kitty_deck:
            GameState.players_hand.append(card)
            GameState.players_meld_deck.append(card)
        advance_mode()


def on_complete_player_cards(req: ajax.Ajax):
    """
    Callback for AJAX request for the player's cards.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_player_cards.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    # Set the global deck of cards for the player's hand.
    GameState.players_hand.clear()
    GameState.players_meld_deck.clear()
    GameState.players_hand = [x["card"] for x in temp]
    mylog.warning("on_complete_player_cards: players_hand=%s", GameState.players_hand)
    GameState.players_meld_deck = copy.deepcopy(GameState.players_hand)  # Deep copy

    display_game_options()


def on_complete_get_meld_score(req: ajax.Ajax):
    """
    Callback for AJAX request for the player's meld.

    :param req: Request object from callback.
    :type req: [type]
    """
    mylog.error("In on_complete_get_meld_score.")

    ajax_request_tracker(-1)
    temp = on_complete_common(req)
    if temp is None:
        return

    if req.status in [200, 0]:
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
    mylog.error("In on_complete_common.")

    ajax_request_tracker(-1)
    if req.status in [200, 0]:
        return json.loads(req.text)

    mylog.warning("on_complete_common: req=%s", req)
    return None


def order_player_index_list_for_trick() -> List[int]:
    """
    Generate a list of indices in GameState.player_list starting with the current
    GameState.round_bid_trick_winner.

    :return: Re-ordered list of player indices.
    :rtype: List[str]
    """
    mylog.error("In order_player_index_list_for_trick.")

    player_list_len = len(GameState.player_list)
    # Locate the index of the winner in the player list
    starting_index = GameState.player_list.index(GameState.round_bid_trick_winner)
    # Generate a list of indices for the players, starting with the
    # GameState.round_bid_trick_winner.
    return [(x + starting_index) % player_list_len for x in range(player_list_len)]


def order_player_id_list_for_trick() -> List[PlayerID]:
    """
    Generate a list of players from GameState.player_list starting with the current
    GameState.round_bid_trick_winner.

    :return: Re-ordered list of player ids.
    :rtype: List[str]
    """
    mylog.error("In order_player_id_list_for_trick.")

    return [GameState.player_list[idx] for idx in order_player_index_list_for_trick()]


def order_player_name_list_for_trick() -> List[str]:
    """
    Generate a list of player names from GameState.player_list starting with the current
    GameState.round_bid_trick_winner.

    :return: Re-ordered list of player names.
    :rtype: List[str]
    """
    mylog.error("In order_player_name_list_for_trick.")

    return [
        GameState.other_players_name(p_id) for p_id in order_player_id_list_for_trick()
    ]


def advance_mode_callback(req: ajax.Ajax):
    """
    Routine to capture the response of the server when advancing the game mode.

    :param req:   The request response passed in during callback
    :type req:    Request
    """
    mylog.error("In advance_mode_callback.")
    mylog.warning(
        "advance_mode_callback: (current mode=%s)", GAME_MODES[GameState.game_mode]
    )

    ajax_request_tracker(-1)
    if req.status not in [200, 0]:
        return

    if "Round" in req.text and "started" in req.text:
        mylog.warning("advance_mode_callback: Starting new round.")
        GameState.game_mode = 0
        clear_globals_for_round_change()

        # display_game_options()
        return

    mylog.warning("advance_mode_callback: req.text=%s", req.text)
    data = json.loads(req.text)
    mylog.warning("advance_mode_callback: data=%r", data)
    GameState.game_mode = data["state"]

    mylog.warning(
        "Leaving advance_mode_callback (current mode=%s)",
        GAME_MODES[GameState.game_mode],
    )

    remove_dialogs()

    display_game_options()


def game_mode_query_callback(req: ajax.Ajax):
    """
    Routine to capture the response of the server when advancing the game mode.

    :param req:   The request response passed in during callback
    :type req:    Request
    """
    mylog.error("In game_mode_query_callback.")

    if GameState.game_mode is not None:
        mylog.warning(
            "Entering game_mode_query_callback (current mode=%s)",
            GAME_MODES[GameState.game_mode],
        )

    ajax_request_tracker(-1)
    # TODO: Handle a semi-corner case where in the middle of a round, a player loses /
    # destroys a cookie and reloads the page.
    if req.status not in [200, 0]:
        mylog.warning(
            "game_mode_query_callback: Not setting game_mode - possibly because GameState.player_id is empty (%s).",
            GameState.player_id,
        )
        return

    mylog.warning("game_mode_query_callback: req.text=%s", req.text)
    data = json.loads(req.text)
    mylog.warning("game_mode_query_callback: data=%r", data)
    GameState.game_mode = data["state"]

    mylog.warning(
        "Leaving game_mode_query_callback (current mode=%s)",
        GAME_MODES[GameState.game_mode],
    )
    if GameState.game_mode == 0:
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
    mylog.error("In get.")

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
    mylog.error("In put.")

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
    mylog.error("In post.")

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
    mylog.error("In delete.")

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
    mylog.error("In locate_cards_below_hand.")

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
    global g_discard_deck
    mylog.error("In clear_globals_for_round_change.")

    GameState.round_id = RoundID()
    GameState.players_hand.clear()
    GameState.players_meld_deck.clear()
    GameState.meld_deck = ["card-base" for _ in range(GameState.hand_size)]
    g_discard_deck = ["card-base" for _ in range(len(GameState.player_list))]
    display_game_options()


def clear_globals_for_trick_change(__: Any):
    """
    Clear some global variables in preparation for a new round.
    """
    # pylint: disable=invalid-name
    global g_discard_deck
    mylog.error("In clear_globals_for_trick_change.")

    g_discard_deck = ["card-base" for _ in range(len(GameState.player_list))]
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
    mylog.error("In populate_canvas.")

    if GAME_MODES[GameState.game_mode] in ["game"]:
        mylog.warning("Exiting populate_canvas. Still in 'game' mode.")
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
        flippable = DECK_CONFIG[deck_type][GameState.game_mode]["flippable"]
        movable = DECK_CONFIG[deck_type][GameState.game_mode]["movable"]
        show_face = DECK_CONFIG[deck_type][GameState.game_mode]["show_face"]
        if "reveal" in GAME_MODES[GameState.game_mode]:
            if "kitty" in deck_type:
                flippable = GameState.player_id == GameState.round_bid_trick_winner
                # show_face = True
            if "player" in deck_type:
                movable = GameState.player_id == GameState.round_bid_trick_winner
        if "trick" in GAME_MODES[GameState.game_mode] and "player" in deck_type:
            # This makes the player's deck movable based on whether their card place
            # in the discard deck is 'blank' or occupied.
            player_index_in_discard_deck = order_player_id_list_for_trick().index(
                GameState.player_id
            )
            movable = g_discard_deck[player_index_in_discard_deck] == "card-base"
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
            text = SVG.TextObject(
                string=f"{player_name}",
                anchorpoint=(
                    CARD_SMALLER_WIDTH * (counter - 1.5),
                    CARD_SMALLER_HEIGHT,
                ),
                anchorposition=2,
                fontsize=24,
                textcolour="white",
                objid=f"name_{deck_type}{counter}",
            )
            target_canvas <= text


def generate_place_static_box(canvas: SVG.CanvasObject):
    """
    Generate and place an SVG box that is the same size as a full player's hand.
    This should prevent excessive resizing of the display as the player's hand depletes
    during trick play.
    """
    mylog.error("In generate_place_static_box.")

    start_y = 2.25 * CARD_HEIGHT
    xincr = CARD_WIDTH / 2
    start_x = -xincr * (GameState.hand_size / 2 + 0.5)

    # pylint: disable=expression-not-assigned
    canvas <= SVG.RectangleObject(
        pointlist=[
            (start_x - 10, start_y - 10),
            (start_x + 10 + (xincr * (GameState.hand_size + 1)), start_y + 10),
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
    mylog.error("In place_cards.")
    mylog.warning("place_cards(deck=%s, deck_type=%s).", deck, deck_type)

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
    mylog.error("In create_game_select_buttons")
    mylog.warning("create_game_select_buttons: game_dict=%s", GameState.game_dict)

    if GameState.game_dict == {}:
        mylog.warning("cgsb: In GameState.game_dict={}")
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
    if len(GameState.game_dict) == 1:
        one_game_id = list(GameState.game_dict.keys())[0]
        get(f"/setcookie/game_id/{one_game_id.value}", on_complete_set_gamecookie)
        return

    mylog.warning("cgsb: Enumerating games for buttons (%d).", len(GameState.game_dict))
    for item, temp_dict in GameState.game_dict.items():
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
    mylog.error("In create_player_select_buttons.")

    g_canvas.deleteAll()

    for item in GameState.player_dict:
        mylog.warning("player_dict[item]=%s", GameState.player_dict[item])
        if not document.getElementById(GameState.player_dict[item]["player_id"]):
            player_button = SVG.Button(
                position=(xpos, ypos),
                size=(450, 35),
                text=f"Player: {GameState.player_dict[item]['name']}",
                onclick=choose_player,
                fontsize=18,
                objid=GameState.player_dict[item]["player_id"],
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
    mylog.error("In remove_dialogs.")

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
    mylog.error(
        "advance_mode: Calling API (current mode=%s)", GAME_MODES[GameState.game_mode]
    )

    if GameState.game_id != GameID() and GameState.player_id != PlayerID():
        put(f"/game/{GameState.game_id.value}?state=true", advance_mode_callback, False)
    else:
        display_game_options()


def sort_player_cards(event=None):  # pylint: disable=unused-argument
    """
    Sort the player's cards.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    mylog.error("In sort_player_cards.")

    # pylint: disable=unnecessary-lambda
    GameState.players_hand.sort(key=lambda x: DECK_SORTED.index(x))
    GameState.players_meld_deck.sort(key=lambda x: DECK_SORTED.index(x))
    display_game_options()


def send_meld(event=None):  # pylint: disable=unused-argument
    """
    Send the meld deck to the server.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    mylog.error("In send_meld.")

    card_string = ",".join(x for x in GameState.meld_deck if x != "card-base")

    mylog.warning(
        "send_meld: /round/%s/score_meld?player_id=%s&cards=%s",
        GameState.round_id.value,
        GameState.player_id.value,
        card_string,
    )

    get(
        f"/round/{GameState.round_id.value}/score_meld?player_id={GameState.player_id.value}&cards={card_string}",
        on_complete_get_meld_score,
    )


def clear_game(event=None):  # pylint: disable=unused-argument
    """
    Request the game cookie be cleared.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    mylog.error("In clear_game.")

    get("/setcookie/game_id/clear", on_complete_set_gamecookie)
    get("/setcookie/player_id/clear", on_complete_set_playercookie)


def clear_player(event=None):  # pylint: disable=unused-argument
    """
    Request the player cookie be cleared.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    mylog.error("In clear_player.")

    get("/setcookie/player_id/clear", on_complete_set_playercookie)


def choose_game(event=None):
    """
    Callback for a button press of the choose game button.

    :param event: The event object passed in during callback, defaults to None
    :type event: [type], optional
    """
    mylog.error("In choose_game.")

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
    mylog.error("In choose_player.")

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
    mylog.error("In display_game_options.")

    xpos = 10
    ypos = 0

    # Grab the game_id, team_ids, and players. Display and allow player to choose.
    if GameState.game_id == GameID():
        mylog.warning("dgo: In GameState.game_id=''")
        create_game_select_buttons(xpos, ypos)
    elif GameState.game_mode is None:
        mylog.warning("dgo: In GameState.game_mode is None")
        get(f"/game/{GameState.game_id.value}?state=false", game_mode_query_callback)
    elif GameState.round_id == RoundID():
        mylog.warning("dgo: In GameState.round_id=''")
        # Open the websocket if needed.
        if g_websocket is None:
            ws_open()

        get(f"/game/{GameState.game_id.value}/round", on_complete_rounds)
    elif GameState.team_list == []:
        mylog.warning("dgo: In GameState.team_list=[]")
        get(f"/round/{GameState.round_id.value}/teams", on_complete_teams)
    elif GameState.player_id == PlayerID():
        mylog.warning("dgo: In GameState.player_id=''")
        create_player_select_buttons(xpos, ypos)
    elif GameState.players_hand == []:
        mylog.warning("dgo: In GameState.players_hand=[]")
        get(f"/player/{GameState.player_id.value}/hand", on_complete_player_cards)
    else:
        mylog.warning("dgo: In else clause")
        # Send the registration message.
        send_registration()

        if GameState.game_mode == 1:
            GameState.meld_score = 0
            GameState.round_bid = 0
            GameState.round_bid_trick_winner = PlayerID()
            GameState.trump = ""
            # update_status_line()

        if GameState.team_id == TeamID():
            # Set the GameState.team_id variable based on the player id chosen.
            for _temp in GameState.team_dict:
                mylog.warning(
                    "dgo: Key: %s Value: %r",
                    _temp,
                    GameState.team_dict[_temp]["player_ids"],
                )
                if (
                    GameState.player_id.value
                    in GameState.team_dict[_temp]["player_ids"]
                ):
                    GameState.team_id = TeamID(GameState.team_dict[_temp]["team_id"])
                    mylog.warning("dgo: Set GameState.team_id=%s", GameState.team_id)

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
    global g_canvas
    mylog.error("In rebuild_display")

    if GameState.game_mode is None and not GameState.game_dict:
        GameState.game_mode = 0

    if g_ajax_outstanding_requests > 0:
        mylog.warning(
            "There are %d outstanding requests. Skipping clear.",
            g_ajax_outstanding_requests,
        )
        return

    update_status_line()

    mode = GAME_MODES[GameState.game_mode]
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
    if "game" not in GAME_MODES[GameState.game_mode]:
        # Update/create buttons

        # # Button to call advance_mode on demand
        # _buttons["button_advance_mode"] = SVG.Button(
        #     position=(-80 * 3.5, -40),
        #     size=(70, 35),
        #     text=GAME_MODES[GameState.game_mode].capitalize(),
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

    if GAME_MODES[GameState.game_mode] in ["reveal"]:
        mylog.warning("rebuild_display: Creating trump selection dialog.")
        tsd = TrumpSelectDialog()
        tsd.display_trump_dialog()

    if GAME_MODES[GameState.game_mode] in ["meld"]:
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
    mylog.error("In update_display.")
    mylog.warning("update_display. (mode=%s)", GAME_MODES[GameState.game_mode])

    # Place the desired decks on the display.
    if not g_canvas.objectDict:
        if (
            GAME_MODES[GameState.game_mode] in ["game"]
            and GameState.game_id == GameID()
        ):  # Choose game, player
            display_game_options()
        if GAME_MODES[GameState.game_mode] not in ["game"]:
            generate_place_static_box(g_canvas)
        if GAME_MODES[GameState.game_mode] in ["bid", "bidfinal"]:  # Bid
            # Use empty deck to prevent peeking at the kitty.
            populate_canvas(GameState.kitty_deck, g_canvas, "kitty")
            populate_canvas(GameState.players_hand, g_canvas, "player")
        if GAME_MODES[GameState.game_mode] in ["bidfinal"]:  # Bid submitted
            # The kitty doesn't need to remain 'secret' now that the bidding is done.
            # Ask the server for the cards in the kitty.
            if GameState.round_id != RoundID():
                get(f"/round/{GameState.round_id.value}/kitty", on_complete_kitty)
        elif GAME_MODES[GameState.game_mode] in ["reveal"]:  # Reveal
            populate_canvas(GameState.kitty_deck, g_canvas, "kitty")
            populate_canvas(GameState.players_hand, g_canvas, "player")
        elif GAME_MODES[GameState.game_mode] in ["meld"]:  # Meld
            populate_canvas(
                GameState.meld_deck, g_canvas, GAME_MODES[GameState.game_mode]
            )
            populate_canvas(GameState.players_meld_deck, g_canvas, "player")
        elif GAME_MODES[GameState.game_mode] in ["trick"]:  # Trick
            populate_canvas(g_discard_deck, g_canvas, GAME_MODES[GameState.game_mode])
            populate_canvas(GameState.players_hand, g_canvas, "player")

    # Last-drawn are on top (z-index wise)
    # TODO: Retrieve events from API to show kitty cards when they are flipped over.
    if GAME_MODES[GameState.game_mode] in ["bid", "bidfinal", "reveal"]:  # Bid & Reveal
        place_cards(GameState.kitty_deck, g_canvas, location="top", deck_type="kitty")
        place_cards(
            GameState.players_hand, g_canvas, location="bottom", deck_type="player"
        )
    elif GAME_MODES[GameState.game_mode] in ["meld"]:  # Meld
        # TODO: Expand display to show all four players.
        place_cards(
            GameState.meld_deck,
            g_canvas,
            location="top",
            deck_type=GAME_MODES[GameState.game_mode],
        )
        place_cards(
            GameState.players_meld_deck, g_canvas, location="bottom", deck_type="player"
        )
    elif GAME_MODES[GameState.game_mode] in ["trick"]:  # Trick
        # Remove any dialogs from the meld phase.
        remove_dialogs()
        place_cards(
            g_discard_deck,
            g_canvas,
            location="top",
            deck_type=GAME_MODES[GameState.game_mode],
        )
        place_cards(
            GameState.players_hand, g_canvas, location="bottom", deck_type="player"
        )

    # pylint: disable=attribute-defined-outside-init, invalid-name
    g_canvas.mouseMode = SVG.MouseMode.DRAG


def resize_canvas(event=None):  # pylint: disable=unused-argument
    """
    Resize the canvas to make use of available screen space.
    :param event: The event object passed in during callback, defaults to None
    """
    mylog.error("In resize_canvas")

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
g_discard_deck = ["card-base" for _ in range(GameState.players)]

document.getElementById("please_wait").text = ""

# Pre-populate some data. Each of these calls display_game_options.
get("/game", on_complete_games)
get("/getcookie/game_id", on_complete_getcookie)
get("/getcookie/player_id", on_complete_getcookie)
