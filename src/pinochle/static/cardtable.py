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

# Disable some pylint complaints because brython does some interesting things.
# pylint: disable=pointless-statement
# Disable some pyright complaints because _mockbrython is incomplete.
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


# Programmatically create a pre-sorted deck to compare to when sorting decks of cards.
# Importing a statically-defined list from constants doesn't work for some reason.
# "9", "jack", "queen", "king", "10", "ace"
# "ace", "10", "king", "queen", "jack", "9"
SUITS = ["spade", "heart", "club", "diamond"]
CARDS = ["ace", "10", "king", "queen", "jack", "9"]
DECK_SORTED = [f"{_suit}_{_card}" for _suit in SUITS for _card in CARDS]

# Various state globals
# button_advance_mode = None  # pylint: disable=invalid-name

## BEGIN Class definitions.


@dataclass(frozen=True)
class BaseID:
    """
    Parent container for string-ified GUIDs / UUIDs used as identifers by the card
    service.
    """

    zeros_uuid = "00000000-0000-0000-0000-000000000000"
    value: str

    def __init__(self, value: str = zeros_uuid) -> None:
        """
        BaseID initializer

        :param value: String representation of the UUID/GUID to store, defaults to zeros_uuid
        :type value: str, optional
        """
        mylog.error("In BaseID.__init__")
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
        """
        PlayingCard initializer.

        :param href: SVG href of the card, defaults to None
        :type href: str, optional
        :param objid: Browser DOM id attribute to set, defaults to None
        :type objid: str, optional
        :param face_value: SVG name for the card, defaults to "back"
        :type face_value: str, optional
        :param show_face: Whether or not to show the face or the back, defaults to True
        :type show_face: bool, optional
        :param flippable: Whether to allow the card to be 'flipped over', defaults to False
        :type flippable: bool, optional
        """
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
        mylog.error("In PlayingCard.play_handler.")

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
            receiving_deck = GameState.discard_deck  # Reference

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
        self,
        sending_deck: List[str],
        receiving_deck: List[str],
        card_tag: str,
        parent_canvas: SVG.CanvasObject,
    ):
        """
        Place 'discarded' cards sequentially or in player trick order depending on
        game_state.

        :param sending_deck: Source card deck
        :type sending_deck: List[str]
        :param receiving_deck: Destination card deck
        :type receiving_deck: List[str]
        :param card_tag: String reflecting what deck type is receiving the card.
        :type card_tag: str
        :param parent_canvas: Canvas that holds the card decks.
        :type parent_canvas: SVG.CanvasObject
        """
        mylog.error("In PlayingCard.handle_discard_placement.")

        # Cards are placed in a specific order when in trick mode. Otherwise,
        # the first available empty (card-base) slot is used.
        if GAME_MODES[GameState.game_mode] in ["trick"]:
            p_list: List[PlayerID] = GameState.order_player_id_list_for_trick()
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
            AjaxRequests.put(
                f"/play/{GameState.round_id.value}/play_card?player_id={GameState.player_id.value}&card={self.face_value}"
            )

    def card_click_handler(self):
        """
        Click handler for the playing card. The action depends on the game mode.
        Since the only time this is done is during the meld process, also call the API to
        notify it that a kitty card has been flipped over and which card that is.
        """
        mylog.error("In PlayingCard.card_click_handler.")

        if GAME_MODES[GameState.game_mode] in ["reveal"] and self.flippable:
            mylog.warning(
                "PlayingCard.card_click_handler: flippable=%r", self.flippable
            )
            # self.show_face = not self.show_face
            # self.flippable = False
            # self.face_update_dom()
            # TODO: Call API to notify the other players this particular card was
            # flipped over and add it to the player's hand.
            g_websocket.send_websocket_message(
                {
                    "action": "reveal_kitty",
                    "game_id": GameState.game_id.value,
                    "player_id": GameState.player_id.value,
                    "card": self.face_value,
                }
            )
        if GAME_MODES[GameState.game_mode] in ["reveal", "meld", "trick"]:
            self.play_handler(event_type="click")


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
    ordered_player_id_list: List[int] = []
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
    # Temporary deck to hold discards during trick phase.
    discard_deck: List[str] = []

    @classmethod
    def _dump_globals(cls) -> None:
        """
        Debugging assistant to output the value of selected globals.
        """
        variables = {
            # "g_canvas": g_canvas,
            # "cls.game_id":      cls.game_id,
            # "cls.game_mode":    cls.game_mode,
            # "cls.round_id":     cls.round_id,
            # "cls.team_list":    cls.team_list,
            # "cls.player_id":    cls.player_id,
            # "cls.player_list":  cls.player_list,
            # "cls.players_hand": cls.players_hand,
            # "cls.game_dict":    cls.game_dict,
            "cls.kitty_size": cls.kitty_size,
            "cls.kitty_deck": cls.kitty_deck,
        }
        for var_name, value in variables.items():
            if value:
                print(f"dgo: {var_name}={value} ({type(value)})")
            else:
                print(f"dgo: {var_name} is None")

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
        Return the other team's name.

        :return: String representing the name of the other team.
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
        Return player name for supplied PlayerID.

        :return: String representing the player's name.
        :rtype: str
        """
        return cls.player_dict[player_id]["name"].capitalize()

    @classmethod
    def set_game_parameters(cls):
        """
        Set various game parameters now that the player has chosen a game.
        """
        try:
            cls.kitty_size = int(cls.game_dict[cls.game_id]["kitty_size"])
            mylog.warning("on_complete_getcookie: KITTY_SIZE=%s", cls.kitty_size)
            if cls.kitty_size > 0:
                cls.kitty_deck = ["card-base" for _ in range(cls.kitty_size)]
            else:
                cls.kitty_deck.clear()
        except KeyError:
            pass
        # TODO: Figure out how better to calculate GameState.hand_size.
        cls.hand_size = int((48 - cls.kitty_size) / cls.players)
        cls.meld_deck = ["card-base" for _ in range(cls.hand_size)]
        cls.discard_deck = ["card-base" for _ in range(cls.players)]

    @classmethod
    def sort_player_hand(cls):
        """
        Sort the player's hand and the temporary hand.
        """
        mylog.error("In GameState.sort_player_hand.")

        # pylint: disable=unnecessary-lambda
        cls.players_hand.sort(key=lambda x: DECK_SORTED.index(x))
        cls.players_meld_deck.sort(key=lambda x: DECK_SORTED.index(x))

    @classmethod
    def prepare_for_round_change(cls):
        """
        Clear some variables in preparation for a new round.
        """
        mylog.error("In GameState.prepare_for_round_change.")

        cls.round_id = RoundID()
        cls.players_hand.clear()
        cls.players_meld_deck.clear()
        cls.meld_deck = ["card-base" for _ in range(cls.hand_size)]
        cls.prepare_for_trick_change()

    @classmethod
    def prepare_for_trick_change(cls):
        """
        Clear some variables in preparation for a new round.
        """
        mylog.error("In GameState.prepare_for_trick_change.")

        cls.discard_deck = ["card-base" for _ in range(len(cls.player_list))]
        cls.ordered_player_id_list = cls._order_player_index_list_for_trick()

    @classmethod
    def _order_player_index_list_for_trick(cls) -> List[int]:
        """
        Generate a list of indices in GameState.player_list starting with the current
        GameState.round_bid_trick_winner.

        :return: Re-ordered list of player indices.
        :rtype: List[str]
        """
        mylog.error("In GameState._order_player_index_list_for_trick.")

        player_list_len = len(cls.player_list)

        mylog.error("GameState._order_player_index_list_for_trick: Section 1")
        # Locate the index of the winner in the player list
        try:
            starting_index = cls.player_list.index(cls.round_bid_trick_winner)
        except ValueError as e:
            return []
        except Exception as e:
            mylog.error(
                "GameState._order_player_index_list_for_trick: Section 2. Exception: (%r)",
                e,
            )
            return []
        mylog.error("GameState._order_player_index_list_for_trick: Section 3")
        # Generate a list of indices for the players, starting with the
        # GameState.round_bid_trick_winner.
        return [(x + starting_index) % player_list_len for x in range(player_list_len)]

    @classmethod
    def order_player_id_list_for_trick(cls) -> List[PlayerID]:
        """
        Generate a list of players from GameState.player_list starting with the current
        GameState.round_bid_trick_winner.

        :return: Re-ordered list of player ids.
        :rtype: List[PlayerID]
        """
        mylog.error("In GameState.order_player_id_list_for_trick.")

        return [
            cls.player_list[idx] for idx in cls._order_player_index_list_for_trick()
        ]

    @classmethod
    def order_player_name_list_for_trick(cls) -> List[str]:
        """
        Generate a list of player names from GameState.player_list starting with the
        current GameState.round_bid_trick_winner.

        :return: Re-ordered list of player names.
        :rtype: List[str]
        """
        mylog.error("In GameState.order_player_name_list_for_trick.")

        return [
            cls.other_players_name(p_id)
            for p_id in cls.order_player_id_list_for_trick()
        ]

    @classmethod
    def advance_mode(cls, event=None):  # pylint: disable=unused-argument
        """
        Routine to advance the UI game mode state. It can be called directly
        or via callback from an event.

        :param event: The event object passed in during callback, defaults to None
        :type event: [type], optional
        """
        mylog.error("In GameState.advance_mode.")
        mylog.warning(
            "GameState.advance_mode: Calling API (current mode=%s)",
            GAME_MODES[cls.game_mode],
        )

        if cls.game_id != GameID() and cls.player_id != PlayerID():
            AjaxRequests.put(
                f"/game/{cls.game_id.value}?state=true",
                AjaxCallbacks().advance_mode_callback,
                False,
            )
        else:
            display_game_options()


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

    bid_dialog: Dialog
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
        AjaxRequests.put(
            f"/play/{GameState.round_id.value}/submit_bid?player_id={GameState.player_id.value}&bid={bid}"
        )

    def display_bid_dialog(self, data: Dict):
        """
        Display the meld hand submitted by a player in a pop-up.

        :param bid_data: Data from the event as a JSON string.
        :type bid_data: str
        """
        mylog.error("In display_bid_dialog.")
        t_player_id: PlayerID = PlayerID(data["player_id"])
        self.last_bid = int(data["bid"])
        player_name = GameState.other_players_name(t_player_id)

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

    trump_dialog: Dialog
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
        mylog.warning(
            "TrumpSelectDialog.on_click_trump_dialog: You buried these cards: %r",
            cards_buried,
        )
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
        AjaxRequests.put(
            f"/play/{GameState.round_id.value}/set_trump?player_id={GameState.player_id.value}&trump={trump}"
        )
        # Transfer cards into the team's collection and out of the player's hand.
        buried_trump = 0
        for card in cards_buried:
            AjaxRequests.put(
                f"/round/{GameState.round_id.value}/{GameState.team_id.value}?card={card}"
            )
            AjaxRequests.delete(f"/player/{GameState.player_id.value}/hand/{card}")
            GameState.players_hand.remove(card)
            GameState.players_meld_deck.remove(card)
            if trump in card:
                buried_trump += 1
        if buried_trump > 0:
            g_websocket.send_websocket_message(
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
                    mylog.warning(
                        "TrumpSelectDialog.display_trump_dialog: Item: %r", item
                    )
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

    meld_final_dialog: Dialog

    def on_click_meld_dialog(self, event=None):  # pylint: disable=unused-argument
        """
        Handle the click event for the OK button. Ignore the cancel button.

        :param event: [description], defaults to None
        :type event: [type], optional
        """
        mylog.error("In MeldFinalDialog.on_click_meld_dialog")

        # Notify the server of my meld is final.
        AjaxRequests.put(
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

    trick_won_dialog: Dialog

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
        AjaxRequests.put(
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
        AjaxRequests.put(
            f"/game/{GameState.game_id.value}?state=true",
            AjaxCallbacks().advance_mode_callback,
            False,
        )
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


class AjaxRequestTracker:
    """
    Class to keep track outstanding requests made to the server.
    """

    _outstanding_requests: int = 0

    @classmethod
    def outstanding_requests(cls) -> int:
        """
        Return the number of outstanding AJAX requests.

        :return: The number of outstanding AJAX requests.
        :rtype: int
        """
        return cls._outstanding_requests

    @classmethod
    def update(cls, direction: int = 0):
        """
        Keep a tally of the currently outstanding AJAX requests.

        :param direction: Whether to increase or decrease the counter,
        defaults to 0 which does not affect the counter.
        :type direction: int, optional
        """
        mylog.error("In AjaxRequestTracker.update.")

        if direction > 0:
            cls._outstanding_requests += 1
        elif direction < 0:
            cls._outstanding_requests -= 1


class AjaxRequests:
    """
    Container for outgoing AJAX requests
    """

    AJAX_URL_ENCODING = "application/x-www-form-urlencoded"

    @classmethod
    def get(cls, url: str, callback=None, async_call=True):
        """
        Wrapper for the AJAX GET call.

        :param url: The part of the URL that is being requested.
        :type url: str
        :param callback: Function to be called when the AJAX request is complete.
        :type callback: function, optional
        :param async_call: Whether to make this call asynchronously, defaults to True
        :type async_call: bool, optional
        """
        mylog.error("In AjaxRequests.get.")

        req = ajax.Ajax()
        if callback is not None:
            AjaxRequestTracker.update(1)
            req.bind("complete", callback)
        mylog.warning("Calling GET /api%s", url)
        req.open("GET", "/api" + url, async_call)
        req.set_header("content-type", cls.AJAX_URL_ENCODING)

        req.send()

    @classmethod
    def put(cls, url: str, callback=None, async_call=True):
        """
        Wrapper for the AJAX PUT call.

        :param url: The part of the URL that is being requested.
        :type url: str
        :param callback: Function to be called when the AJAX request is complete.
        :type callback: function, optional
        :param async_call: Whether to make this call asynchronously, defaults to True
        :type async_call: bool, optional
        """
        mylog.error("In AjaxRequests.put.")

        req = ajax.Ajax()
        if callback is not None:
            AjaxRequestTracker.update(1)
            req.bind("complete", callback)
        # mylog.warning("Calling PUT /api%s with data: %r", url, data)
        mylog.warning("Calling PUT /api%s", url)
        req.open("PUT", "/api" + url, async_call)
        req.set_header("content-type", cls.AJAX_URL_ENCODING)
        # req.send({"a": a, "b":b})
        # req.send(data)
        req.send({})

    @classmethod
    def post(cls, url: str, callback=None, async_call=True):
        """
        Wrapper for the AJAX POST call.

        :param url: The part of the URL that is being requested.
        :type url: str
        :param callback: Function to be called when the AJAX request is complete.
        :type callback: function, optional
        :param async_call: Whether to make this call asynchronously, defaults to True
        :type async_call: bool, optional
        """
        mylog.error("In AjaxRequests.post.")

        req = ajax.Ajax()
        if callback is not None:
            AjaxRequestTracker.update(1)
            req.bind("complete", callback)
        # mylog.warning("Calling POST /api%s with data: %r", url, data)
        mylog.warning("Calling POST /api%s", url)
        req.open("POST", "/api" + url, async_call)
        req.set_header("content-type", cls.AJAX_URL_ENCODING)
        # req.send(data)
        req.send({})

    @classmethod
    def delete(cls, url: str, callback=None, async_call=True):
        """
        Wrapper for the AJAX Data call.

        :param url: The part of the URL that is being requested.
        :type url: str
        :param callback: Function to be called when the AJAX request is complete.
        :type callback: function, optional
        :param async_call: Whether to make this call asynchronously, defaults to True
        :type async_call: bool, optional
        """
        mylog.error("In AjaxRequests.delete.")

        req = ajax.Ajax()
        if callback is not None:
            AjaxRequestTracker.update(1)
            req.bind("complete", callback)
        # pass the arguments in the query string
        req.open("DELETE", "/api" + url, async_call)
        req.set_header("content-type", cls.AJAX_URL_ENCODING)
        req.send()


class AjaxCallbacks:
    """
    Container for incoming AJAX responses
    """

    def on_complete_games(self, req: ajax.Ajax):
        """
        Callback for AJAX request for the list of games.

        :param req: Request object from callback.
        :type req: ajax.Ajax
        """
        mylog.error("In AjaxCallbacks.on_complete_games.")

        AjaxRequestTracker.update(-1)
        temp = self._on_complete_common(req)
        if temp is None:
            return

        # Set the global game list.
        GameState.game_dict.clear()
        for item in temp:
            mylog.warning("AjaxCallbacks.on_complete_games: item=%s", item)
            GameState.game_dict[GameID(item["game_id"])] = item

        display_game_options()

    def on_complete_rounds(self, req: ajax.Ajax):
        """
        Callback for AJAX request for the list of rounds.

        :param req: Request object from callback.
        :type req: ajax.Ajax
        """
        mylog.error("In AjaxCallbacks.on_complete_rounds.")

        AjaxRequestTracker.update(-1)
        GameState.team_list.clear()

        temp = self._on_complete_common(req)
        if temp is None:
            return

        # Set the round ID.
        GameState.round_id = RoundID(temp["round_id"])
        mylog.warning(
            "AjaxCallbacks.on_complete_rounds: round_id=%s", GameState.round_id
        )

        display_game_options()

    def on_complete_teams(self, req: ajax.Ajax):
        """
        Callback for AJAX request for the information on the teams associated with the round.

        :param req: Request object from callback.
        :type req: ajax.Ajax
        """
        mylog.error("In AjaxCallbacks.on_complete_teams.")

        AjaxRequestTracker.update(-1)
        temp = self._on_complete_common(req)
        if temp is None:
            return

        # Set the global list of teams for this round.
        GameState.team_list.clear()
        GameState.team_list = [TeamID(x) for x in temp["team_ids"]]
        mylog.warning(
            "AjaxCallbacks.on_complete_teams: team_list=%r", GameState.team_list
        )

        # Clear the team dict here because of the multiple callbacks.
        GameState.team_dict.clear()
        for item in GameState.team_list:
            AjaxRequests.get(f"/team/{item}", self.on_complete_team_names)

    def on_complete_team_names(self, req: ajax.Ajax):
        """
        Callback for AJAX request for team information.

        :param req: Request object from callback.
        :type req: ajax.Ajax
        """
        mylog.error("In AjaxCallbacks.on_complete_team_names.")

        AjaxRequestTracker.update(-1)
        temp = self._on_complete_common(req)
        if temp is None:
            return

        # Set the global dict of team names for this round.
        mylog.warning(
            "AjaxCallbacks.on_complete_team_names: Setting team_dict[%s]=%r",
            temp["team_id"],
            temp,
        )
        GameState.team_dict[TeamID(temp["team_id"])] = temp
        mylog.warning(
            "AjaxCallbacks.on_complete_team_names: team_dict=%s", GameState.team_dict
        )

        # Only call API once per team, per player.
        for item in GameState.team_dict[TeamID(temp["team_id"])]["player_ids"]:
            mylog.warning(
                "AjaxCallbacks.on_complete_team_names: calling get/player/%s", item
            )
            AjaxRequests.get(f"/player/{item}", self.on_complete_players)

    def on_complete_players(self, req: ajax.Ajax):
        """
        Callback for AJAX request for player information.

        :param req: Request object from callback.
        :type req: ajax.Ajax
        """
        mylog.error("In AjaxCallbacks.on_complete_players.")

        AjaxRequestTracker.update(-1)
        temp = self._on_complete_common(req)
        if temp is None:
            return

        # Set the global dict of players for reference later.
        GameState.player_dict[PlayerID(temp["player_id"])] = temp
        mylog.warning(
            "AjaxCallbacks.on_complete_players: player_dict=%s", GameState.player_dict
        )
        display_game_options()

    def on_complete_set_gamecookie(self, req: ajax.Ajax):
        """
        Callback for AJAX request for setcookie information.

        :param req: Request object from callback.
        :type req: ajax.Ajax
        """
        mylog.error("In AjaxCallbacks.on_complete_set_gamecookie.")

        AjaxRequestTracker.update(-1)
        if req.status in [200, 0]:
            AjaxRequests.get("/getcookie/game_id", self.on_complete_getcookie)

    def on_complete_set_playercookie(self, req: ajax.Ajax):
        """
        Callback for AJAX request for setcookie information.

        :param req: Request object from callback.
        :type req: ajax.Ajax
        """
        mylog.error("In AjaxCallbacks.on_complete_set_playercookie.")

        AjaxRequestTracker.update(-1)
        if req.status in [200, 0]:
            AjaxRequests.get("/getcookie/player_id", self.on_complete_getcookie)

    def on_complete_getcookie(self, req: ajax.Ajax):
        """
        Callback for AJAX request for setcookie information.

        :param req: Request object from callback.
        :type req: ajax.Ajax
        """
        mylog.error("In AjaxCallbacks.on_complete_getcookie.")

        AjaxRequestTracker.update(-1)
        if req.status != 200:
            return
        if req.text is None or req.text == "":
            mylog.warning(
                "AjaxCallbacks.on_complete_getcookie: cookie response is None."
            )
            return
        mylog.warning("AjaxCallbacks.on_complete_getcookie: req.text=%s", req.text)
        response_data = json.loads(req.text)

        # Set the global deck of cards for the player's hand.
        mylog.warning(
            "AjaxCallbacks.on_complete_getcookie: response_data=%s", response_data
        )
        if "game_id" in response_data["kind"]:
            GameState.game_id = GameID(response_data["ident"])
            mylog.warning(
                "AjaxCallbacks.on_complete_getcookie: Setting GAME_ID=%s",
                response_data["ident"],
            )
            # put({}, f"/game/{GameState.game_id}?state=false", advance_mode_initial_callback, False)

            GameState.set_game_parameters()

        elif "player_id" in response_data["kind"]:
            GameState.player_id = PlayerID(response_data["ident"])
            mylog.warning(
                "AjaxCallbacks.on_complete_getcookie: Setting PLAYER_ID=%s",
                response_data["ident"],
            )
            AjaxRequests.get(
                f"/player/{GameState.player_id.value}/hand",
                self.on_complete_player_cards,
            )

        display_game_options()

    def on_complete_kitty(self, req: ajax.Ajax):
        """
        Callback for AJAX request for the round's kitty cards, if any.

        :param req: Request object from callback.
        :type req: ajax.Ajax
        """
        mylog.error("In AjaxCallbacks.on_complete_kitty.")

        AjaxRequestTracker.update(-1)
        mylog.warning("AjaxCallbacks.on_complete_kitty: req.text=%r", req.text)
        temp = self._on_complete_common(req)
        if temp is None:
            return

        # Set the global deck of cards for the kitty.
        GameState.kitty_deck.clear()
        GameState.kitty_deck = temp["cards"]
        mylog.warning(
            "AjaxCallbacks.on_complete_kitty: kitty_deck=%s", GameState.kitty_deck
        )
        if GameState.player_id == GameState.round_bid_trick_winner:
            # Add the kitty cards to the bid winner's deck
            for card in GameState.kitty_deck:
                GameState.players_hand.append(card)
                GameState.players_meld_deck.append(card)
            GameState.advance_mode()

    def on_complete_player_cards(self, req: ajax.Ajax):
        """
        Callback for AJAX request for the player's cards.

        :param req: Request object from callback.
        :type req: ajax.Ajax
        """
        mylog.error("In AjaxCallbacks.on_complete_player_cards.")

        AjaxRequestTracker.update(-1)
        temp = self._on_complete_common(req)
        if temp is None:
            return

        # Set the global deck of cards for the player's hand.
        GameState.players_hand.clear()
        GameState.players_meld_deck.clear()
        GameState.players_hand = [x["card"] for x in temp]
        mylog.warning(
            "AjaxCallbacks.on_complete_player_cards: players_hand=%s",
            GameState.players_hand,
        )
        GameState.players_meld_deck = copy.deepcopy(GameState.players_hand)  # Deep copy

        display_game_options()

    def on_complete_get_meld_score(self, req: ajax.Ajax):
        """
        Callback for AJAX request for the player's meld.

        :param req: Request object from callback.
        :type req: ajax.Ajax
        """
        mylog.error("In AjaxCallbacks.on_complete_get_meld_score.")

        AjaxRequestTracker.update(-1)
        temp = self._on_complete_common(req)
        if temp is None:
            return

        if req.status in [200, 0]:
            mylog.warning(
                "AjaxCallbacks.on_complete_get_meld_score: req.text: %s", req.text
            )
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

        mylog.warning("AjaxCallbacks.on_complete_get_meld_score: score: %r", req)

    def advance_mode_callback(self, req: ajax.Ajax):
        """
        Routine to capture the response of the server when advancing the game mode.

        :param req: Request object from callback.
        :type req: ajax.Ajax
        """
        mylog.error("In AjaxCallbacks.advance_mode_callback.")
        mylog.warning(
            "AjaxCallbacks.advance_mode_callback: (current mode=%s)",
            GAME_MODES[GameState.game_mode],
        )

        AjaxRequestTracker.update(-1)
        if req.status not in [200, 0]:
            return

        if "Round" in req.text and "started" in req.text:
            mylog.warning("AjaxCallbacks.advance_mode_callback: Starting new round.")
            GameState.game_mode = 0
            GameState.prepare_for_round_change()

            display_game_options()
            return

        mylog.warning("AjaxCallbacks.advance_mode_callback: req.text=%s", req.text)
        data = json.loads(req.text)
        mylog.warning("AjaxCallbacks.advance_mode_callback: data=%r", data)
        GameState.game_mode = data["state"]

        mylog.warning(
            "Leaving AjaxCallbacks.advance_mode_callback (current mode=%s)",
            GAME_MODES[GameState.game_mode],
        )

        remove_dialogs()

        display_game_options()

    def game_mode_query_callback(self, req: ajax.Ajax):
        """
        Routine to capture the response of the server when advancing the game mode.

        :param req: Request object from callback.
        :type req: ajax.Ajax
        """
        mylog.error("In AjaxCallbacks.game_mode_query_callback.")

        if GameState.game_mode is not None:
            mylog.warning(
                "In AjaxCallbacks.game_mode_query_callback (current mode=%s)",
                GAME_MODES[GameState.game_mode],
            )

        AjaxRequestTracker.update(-1)
        # TODO: Handle a semi-corner case where in the middle of a round, a player loses /
        # destroys a cookie and reloads the page.
        if req.status not in [200, 0]:
            mylog.warning(
                "AjaxCallbacks.game_mode_query_callback: Not setting game_mode - possibly because GameState.player_id is empty (%s).",
                GameState.player_id,
            )
            return

        mylog.warning("AjaxCallbacks.game_mode_query_callback: req.text=%s", req.text)
        data = json.loads(req.text)
        mylog.warning("AjaxCallbacks.game_mode_query_callback: data=%r", data)
        GameState.game_mode = data["state"]

        mylog.warning(
            "Leaving AjaxCallbacks.game_mode_query_callback (current mode=%s)",
            GAME_MODES[GameState.game_mode],
        )
        if GameState.game_mode == 0:
            GameState.prepare_for_round_change()

        display_game_options()

    def _on_complete_common(self, req: ajax.Ajax) -> Optional[Dict]:
        """
        Common function for AJAX callbacks.

        :param req: Request object from callback.
        :type req: ajax.Ajax
        :return: Dictionary returned in the request as decoded from JSON.
        :rtype: dict
        """
        mylog.error("In AjaxCallbacks._on_complete_common.")

        AjaxRequestTracker.update(-1)
        if req.status in [200, 0]:
            return json.loads(req.text)

        mylog.warning("AjaxCallbacks._on_complete_common: req=%s", req)
        return None


class WSocketContainer:
    """
    Container for websocket communications.
    """

    websock: websocket.WebSocket = None
    PROTOCOL: str
    SERVER: str
    registered_with_server = False

    def __init__(self) -> None:
        """
        WSocketContainer initializer
        """
        if not websocket.supported:
            InfoDialog("websocket", "WebSocket is not supported by your browser")
            return
        if self.websock:
            return

        self.find_protocol_server()
        self.ws_open()

    def find_protocol_server(self) -> None:
        """
        Gather information from the environment about the protocol and server name
        from where we're being served.
        """
        mylog.error("In WSocketContainer.find_protocol_server.")

        start = os.environ["HOME"].find("//") + 2
        end = os.environ["HOME"].find("/", start) + 1
        self.PROTOCOL = os.environ["HOME"][: start - 3]
        if end <= start:
            self.SERVER = os.environ["HOME"][start:]
        else:
            self.SERVER = os.environ["HOME"][start:end]

    def ws_open(self):
        """
        Open a websocket connection back to the originating server.
        """
        mylog.error("In WSocketContainer.ws_open.")

        # open a web socket
        proto = self.PROTOCOL.replace("http", "ws")
        self.websock = websocket.WebSocket(f"{proto}://{self.SERVER}/stream")
        # bind functions to web socket events
        self.websock.bind("open", self.on_ws_open)
        self.websock.bind("message", self.on_ws_event)
        self.websock.bind("close", self.on_ws_close)

    def on_ws_open(self, event=None):  # pylint: disable=unused-argument
        """
        Callback for Websocket open event.

        :param event: Event object from ws event.
        :type event: dict
        """
        mylog.error("In WSocketContainer.on_ws_open: Connection is open")

    def on_ws_close(self, event=None):  # pylint: disable=unused-argument
        """
        Callback for Websocket close event.
        """
        mylog.error("WSocketContainer.on_ws_close: Connection has closed")

        self.websock = None
        self.registered_with_server = False
        # set_timeout(ws_open, 1000)

    def on_ws_error(self, event=None):
        """
        Callback for Websocket error event.

        :param event: Event object from ws event.
        :type event: dict
        """
        mylog.error(
            "In WSocketContainer.on_ws_error: Connection has experienced an error"
        )
        mylog.warning("WSocketContainer.on_ws_error: event=%r", event)

    def on_ws_event(self, event=None):
        """
        Callback for Websocket event from server. This method handles much of the state
        change in the user interface.

        :param event: Event object from ws event as a JSON-encoded string.
        :type event: str
        """
        mylog.error("In WSocketContainer.on_ws_event.")

        t_data = json.loads(event.data)
        mylog.warning("WSocketContainer.on_ws_event: %s", event.data)

        if "action" not in t_data:
            return

        actions = {
            "game_start": self.start_game_and_clear_round_globals,
            "notification_player_list": self.update_player_names,
            "game_state": self.set_game_state_from_server,
            "bid_prompt": BidDialog().display_bid_dialog,
            "bid_winner": self.display_bid_winner,
            "reveal_kitty": self.reveal_kitty_card,
            "trump_selected": self.record_trump_selection,
            "trump_buried": self.notify_trump_buried,
            "meld_update": self.display_player_meld,
            "team_score": self.update_team_scores,
            "trick_card": self.update_trick_card,
            "trick_won": self.update_trick_winner,
            "trick_next": clear_globals_for_trick_change,
            "score_round": self.update_round_final_score,
        }

        # Dispatch action
        actions[t_data["action"]](t_data)

    def update_round_final_score(self, data: Dict):
        """
        Notify players that the final trick has been won.

        :param data: Data from the event.
        :type data: Dict
        """
        mylog.error("In WSocketContainer.update_round_final_score.")

        mylog.warning("WSocketContainer.update_round_final_score: data=%s", data)
        assert isinstance(data, dict)
        t_player_id = PlayerID(data["player_id"])
        assert isinstance(data["team_trick_scores"], dict)
        mylog.warning(
            "WSocketContainer.update_round_final_score: data['team_trick_scores']: %r",
            data["team_trick_scores"],
        )
        t_team_trick_scores = {
            TeamID(x): y for (x, y) in data["team_trick_scores"].items()
        }
        assert isinstance(data["team_scores"], dict)
        mylog.warning(
            "WSocketContainer.update_round_final_score: data['team_scores']: %r",
            data["team_scores"],
        )
        t_team_scores = {TeamID(x): y for (x, y) in data["team_scores"].items()}
        mylog.warning(
            "WSocketContainer.update_round_final_score: t_player_id=%s", t_player_id
        )
        mylog.warning(
            "WSocketContainer.update_round_final_score: t_team_trick_scores=%r",
            t_team_trick_scores,
        )
        mylog.warning(
            "WSocketContainer.update_round_final_score: t_team_scores=%r", t_team_scores
        )

        # Record that information.
        GameState.round_bid_trick_winner = t_player_id

        # Obtain the other team's ID
        t_other_team_id = GameState.other_team_id()

        mylog.warning("WSocketContainer.update_round_final_score: Setting my team name")
        my_team = GameState.my_team_name()
        mylog.warning(
            "WSocketContainer.update_round_final_score: Setting other team's name"
        )
        other_team = GameState.other_team_name()
        mylog.warning(
            "WSocketContainer.update_round_final_score: Setting score variables"
        )
        my_scores, other_scores = (
            t_team_trick_scores[GameState.team_id],
            t_team_trick_scores[t_other_team_id],
        )

        # TODO: Handle case where bid winner's team doesn't make the bid.
        mylog.warning(
            "WSocketContainer.update_round_final_score: Setting global team scores."
        )
        GameState.my_team_score, GameState.other_team_score = (
            t_team_scores[GameState.team_id],
            t_team_scores[t_other_team_id],
        )

        mylog.warning(
            "GameState.player_id=%s / t_player_id=%s", GameState.player_id, t_player_id
        )
        if GameState.player_id == t_player_id:
            mylog.warning(
                "WSocketContainer.update_round_final_score: Displaying final trick dialog for this player."
            )
            TrickWonDialog().display_final_trick_dialog(
                my_team, my_scores, other_team, other_scores
            )
        else:
            mylog.warning(
                "WSocketContainer.update_round_final_score: Displaying generic final trick dialog for this player."
            )
            InfoDialog(
                "Last Trick Won",
                f"{GameState.other_players_name(t_player_id)} won the final trick. "
                + f"Trick Scores: {my_team}: {my_scores} points / {other_team}: {other_scores} points",
                top=25,
                left=25,
            )

    def update_trick_winner(self, data: Dict):
        """
        Notify players that the trick has been won.

        :param data: Data from the event.
        :type data: Dict
        """
        mylog.error("In WSocketContainer.update_trick_winner.")
        mylog.warning("WSocketContainer.update_trick_winner: data=%s", data)

        assert isinstance(data, dict)
        t_player_id = PlayerID(data["player_id"])
        t_card = data["winning_card"]
        mylog.warning(
            "WSocketContainer.update_trick_winner: t_player_id=%s", t_player_id
        )
        mylog.warning("WSocketContainer.update_trick_winner: t_card=%s", t_card)

        # Find the first instance of the winning card in the list.
        card_index = GameState.discard_deck.index(t_card)
        # Correlate that to the player_id who threw it.
        t_player_id = GameState.order_player_id_list_for_trick()[card_index]
        mylog.warning(
            "WSocketContainer.update_trick_winner: t_player_id=%s", t_player_id
        )
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

    def update_trick_card(self, data: Dict):
        """
        Place the thrown card in the player's slot for this trick.

        :param data: Data from the event.
        :type data: Dict
        """
        mylog.error("In WSocketContainer.update_trick_card.")
        mylog.warning("WSocketContainer.update_trick_card: data=%s", data)

        assert isinstance(data, dict)
        t_player_id: PlayerID = PlayerID(data["player_id"])
        t_card = data["card"]
        mylog.warning("WSocketContainer.update_trick_card: t_player_id=%s", t_player_id)
        mylog.warning("WSocketContainer.update_trick_card: t_card=%s", t_card)
        GameState.discard_deck[
            GameState.order_player_id_list_for_trick().index(t_player_id)
        ] = t_card

        # Set the player's hand to unmovable until the trick is over.
        rebuild_display()

    def update_team_scores(self, data: Dict):
        """
        Update the game state from the server with the team scores.

        :param data: Data from the event.
        :type data: Dict
        """
        mylog.error("In WSocketContainer.update_team_scores.")

        mylog.warning("WSocketContainer.update_team_scores: data=%r", data)
        assert isinstance(data, dict)
        if GameState.team_id == TeamID(data["team_id"]):
            GameState.my_team_score = data["score"]
            GameState.meld_score = data["meld_score"]
        else:  # Other team
            GameState.other_team_score = data["score"]

        update_status_line()

    def notify_trump_buried(self, data: Dict):
        """
        Notify players that trump has been buried.

        :param data: Data from the event.
        :type data: Dict
        """
        mylog.error("In WSocketContainer.notify_trump_buried.")
        mylog.warning("WSocketContainer.notify_trump_buried: data=%r", data)

        assert isinstance(data, dict)
        if "player_id" in data:
            mylog.warning(
                "WSocketContainer.notify_trump_buried: About to retrieve player_id from data"
            )
            t_player_id: PlayerID = PlayerID(data["player_id"])
        else:
            t_player_id = PlayerID()
        mylog.warning(
            "WSocketContainer.notify_trump_buried: t_player_id=%r", t_player_id
        )
        player_name = ""
        if t_player_id == GameState.player_id:
            player_name = "You have"
        else:
            player_name = "{} has".format(GameState.other_players_name(t_player_id))
        mylog.warning(
            "WSocketContainer.notify_trump_buried: player_name=%s", player_name
        )
        count = data["count"]
        mylog.warning("WSocketContainer.notify_trump_buried: count=%d", count)

        InfoDialog(
            "Trump Buried",
            html.P(f"{player_name} buried {count} trump cards."),
            left=25,
            top=25,
            ok=True,
            remove_after=15,
        )

    def display_player_meld(self, data: Dict):
        """
        Display the meld hand submitted by a player in a pop-up.

        :param data: Data from the event.
        :type data: Dict
        """
        mylog.error("In WSocketContainer.display_player_meld.")

        player_id = PlayerID(data["player_id"])
        player_name = GameState.other_players_name(player_id)
        card_list = data["card_list"]
        try:
            # If a dialog already exists, delete it.
            if existing_dialog := document.getElementById(f"dialog_{player_id.value}"):
                existing_dialog.parentNode.removeChild(existing_dialog)
        except Exception as e:  # pylint: disable=invalid-name,broad-except
            mylog.warning(
                "WSocketContainer.display_player_meld: Caught exception: %r", e
            )
        try:
            # Construct the new dialog to display the meld cards.
            xpos = 0.0
            d_canvas = SVG.CanvasObject("40vw", "20vh", "none", objid="dialog_canvas")
            for card in card_list:
                # pylint: disable=expression-not-assigned
                d_canvas <= SVG.UseObject(href=f"#{card}", origin=(xpos, 0))
                xpos += CARD_WIDTH / 2.0
        except Exception as e:  # pylint: disable=invalid-name,broad-except
            mylog.warning(
                "WSocketContainer.display_player_meld: Caught exception: %r", e
            )
            return
        InfoDialog(
            "Meld Cards",
            html.P(f"{player_name}'s meld cards are:") + d_canvas,
            left=25,
            top=25,
            ok=True,
        )
        mylog.warning(
            "WSocketContainer.display_player_meld: Items: %r",
            document.getElementsByClassName("brython-dialog-main"),
        )
        # Add an ID attribute so we can find it later if needed.
        for item in document.getElementsByClassName("brython-dialog-main"):
            mylog.warning("WSocketContainer.display_player_meld: Item: %r", item)
            if not item.id:
                # Assume this is the one we just created.
                item.id = f"dialog_{player_id.value}"

        d_canvas.fitContents()

    def record_trump_selection(self, data: Dict):
        """
        Convey the chosen trump to the user, as provided by the server.

        :param data: Data from the event.
        :type data: Dict
        """
        mylog.error("In WSocketContainer.record_trump_selection.")

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

    def reveal_kitty_card(self, data: Dict):
        """
        Reveal the provided card in the kitty.

        :param data: Data from the event.
        :type data: Dict
        """
        mylog.error("In WSocketContainer.reveal_kitty_card.")

        revealed_card = str(data["card"])

        if revealed_card not in GameState.kitty_deck:
            mylog.warning(
                "WSocketContainer.reveal_kitty_card: %s is not in %r",
                revealed_card,
                GameState.kitty_deck,
            )
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

    def display_bid_winner(self, data: Dict):
        """
        Display the round's bid winner.

        :param data: Data from the event.
        :type data: Dict
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

    def update_player_names(self, data: Dict):
        """
        Update the player names in the UI.

        :param data: Data from the event.
        :type data: Dict
        """
        mylog.error("In WSocketContainer.update_player_names.")

        GameState.player_list = [PlayerID(x) for x in data["player_order"]]
        my_player_list = [PlayerID(x) for x in data["player_ids"]]
        # Display the player's name in the UI
        if my_player_list != [] and GameState.player_id in my_player_list:
            mylog.warning(
                "WSocketContainer.update_player_names: Players: %r", my_player_list
            )

            mylog.error("WSocketContainer.update_player_names: Section 1")
            self.registered_with_server = True
            document.getElementById("player_name").clear()
            document.getElementById("player_name").attach(
                html.SPAN(GameState.my_name(), Class="player_name",)
            )

            mylog.error("WSocketContainer.update_player_names: Section 2")
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
            mylog.error("WSocketContainer.update_player_names: Section 3")
            if len(my_player_list) < len(GameState.player_dict):
                document.getElementById(
                    "please_wait"
                ).text = "Waiting for all players to join the game."
            else:
                mylog.error("WSocketContainer.update_player_names: Section 4")
                try:
                    document.getElementById("please_wait").remove()
                except AttributeError:
                    # Occurs when it's already been removed.
                    pass
        mylog.error("WSocketContainer.update_player_names: Exiting...")

    def set_game_state_from_server(self, data: Dict):
        """
        Set game state from webservice message.

        :param data: Data from the event.
        :type data: Dict
        """
        mylog.error("In WSocketContainer.set_game_state_from_server.")

        GameState.game_mode = data["state"]
        display_game_options()

    def start_game_and_clear_round_globals(self, data: Dict):
        """
        Start game and clear round globals.

        :param data: Data from the event.
        :type data: Dict
        """
        mylog.error("In WSocketContainer.start_game_and_clear_round_globals.")

        GameState.game_mode = data["state"]
        mylog.warning(
            "WSocketContainer.start_game_and_clear_round_globals: game_start: GameState.player_list=%r",
            GameState.player_list,
        )
        GameState.prepare_for_round_change()
        display_game_options()

    def send_websocket_message(self, message: dict):
        """
        Send message to server.

        :param message: Websocket message to be sent to the server.
        :type message: dict
        """
        global g_websocket
        mylog.error("In WSocketContainer.send_websocket_message.")

        if self.websock is None:
            mylog.warning("WSocketContainer.send_websocket_message: Opening WebSocket.")
            g_websocket = WSocketContainer()

        mylog.warning("WSocketContainer.send_websocket_message: Sending message.")
        self.websock.send(json.dumps(message))

    def send_registration(self):
        """
        Send registration structure to server.
        """
        mylog.error("In WSocketContainer.send_registration")

        if self.registered_with_server:
            return

        self.send_websocket_message(
            {
                "action": "register_client",
                "game_id": GameState.game_id.value,
                "player_id": GameState.player_id.value,
            }
        )


## END Class definitions.

## BEGIN Function definitions.


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


def locate_cards_below_hand() -> List[str]:
    """
    Identify cards that have been moved below the player's hand.

    :return: List of cards found below the player's hand.
    :rtype: List[str]
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


def clear_globals_for_trick_change(__: Any):
    """
    Prepare game state in preparation for a new trick.
    """
    mylog.error("In clear_globals_for_trick_change.")

    GameState.prepare_for_trick_change()
    display_game_options()


def populate_canvas(deck, target_canvas: SVG.CanvasObject, deck_type="player"):
    """
    Populate given canvas with the deck of cards but without specific placement.

    :param deck: card names in the format that svg-cards.svg wants.
    :type deck: list
    :param target_canvas: Canvas to populate
    :type target_canvas: SVG.CanvasObject
    :param deck_type: The "type" of deck populating the UI.
    :type deck_type: str
    """
    mylog.error("In populate_canvas.")

    if GAME_MODES[GameState.game_mode] in ["game"]:
        mylog.warning("Exiting populate_canvas. Still in 'game' mode.")
        return
    if GameState.game_mode < 0:
        mylog.warning("Invalid game mode. (%d)", GameState.game_mode)
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
            player_index_in_discard_deck = GameState.order_player_id_list_for_trick().index(
                GameState.player_id
            )
            movable = (
                GameState.discard_deck[player_index_in_discard_deck] == "card-base"
            )
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
            mylog.warning(
                "%s %s", counter, GameState.order_player_name_list_for_trick()[counter]
            )
            player_name = GameState.order_player_name_list_for_trick()[counter]
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

    :param canvas: Canvas to receive the box.
    :type canvas: SVG.CanvasObject
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
            onclick=lambda x: AjaxRequests.get(
                "/game", AjaxCallbacks().on_complete_games
            ),
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
        AjaxRequests.get(
            f"/setcookie/game_id/{one_game_id.value}",
            AjaxCallbacks().on_complete_set_gamecookie,
        )
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
        mylog.warning("remove_dialogs: Removing dialog item=%r", item)
        item.remove()


def sort_player_cards(event=None):  # pylint: disable=unused-argument
    """
    Callback for the button requesting to sort the player's cards.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    mylog.error("In sort_player_cards.")

    GameState.sort_player_hand()
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

    # TODO: Probably should be a PUT
    AjaxRequests.get(
        f"/round/{GameState.round_id.value}/score_meld?player_id={GameState.player_id.value}&cards={card_string}",
        AjaxCallbacks().on_complete_get_meld_score,
    )


def clear_game(event=None):  # pylint: disable=unused-argument
    """
    Request the game cookie be cleared.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    mylog.error("In clear_game.")

    AjaxRequests.get(
        "/setcookie/game_id/clear", AjaxCallbacks().on_complete_set_gamecookie
    )
    AjaxRequests.get(
        "/setcookie/player_id/clear", AjaxCallbacks().on_complete_set_playercookie
    )


def clear_player(event=None):  # pylint: disable=unused-argument
    """
    Request the player cookie be cleared.

    :param event: The event object passed in during callback, defaults to None
    :type event: Event(?), optional
    """
    mylog.error("In clear_player.")

    AjaxRequests.get(
        "/setcookie/player_id/clear", AjaxCallbacks().on_complete_set_playercookie
    )


def choose_game(event=None):
    """
    Callback for a button press of the choose game button.

    :param event: The event object passed in during callback, defaults to None
    :type event: [type], optional
    """
    mylog.error("In choose_game.")

    try:
        game_to_be = event.currentTarget.id
        AjaxRequests.get(
            f"/setcookie/game_id/{game_to_be}",
            AjaxCallbacks().on_complete_set_gamecookie,
        )
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
        AjaxRequests.get(
            f"/setcookie/player_id/{player_to_be}",
            AjaxCallbacks().on_complete_set_playercookie,
        )
        AjaxRequests.get(
            f"/player/{player_to_be}/hand", AjaxCallbacks().on_complete_player_cards
        )
        mylog.warning("choose_player: PLAYER_ID will be %s", player_to_be)
    except AttributeError:
        mylog.warning("choose_player: Caught AttributeError.")
        return


def display_game_options():
    """
    Conditional ladder for early game data selection. This needs to be done better and
    have new game/team/player capability.
    """
    global g_websocket
    mylog.error("In display_game_options.")

    xpos = 10
    ypos = 0

    # Grab the game_id, team_ids, and players. Display and allow player to choose.
    if GameState.game_id == GameID():
        mylog.warning("dgo: In GameState.game_id=''")
        create_game_select_buttons(xpos, ypos)
    elif GameState.game_mode is None:
        mylog.warning("dgo: In GameState.game_mode is None")
        AjaxRequests.get(
            f"/game/{GameState.game_id.value}?state=false",
            AjaxCallbacks().game_mode_query_callback,
        )
    elif GameState.round_id == RoundID():
        mylog.warning("dgo: In GameState.round_id=''")
        # Open the websocket if needed.
        if g_websocket is None:
            g_websocket = WSocketContainer()

        AjaxRequests.get(
            f"/game/{GameState.game_id.value}/round", AjaxCallbacks().on_complete_rounds
        )
    elif GameState.team_list == []:
        mylog.warning("dgo: In GameState.team_list=[]")
        AjaxRequests.get(
            f"/round/{GameState.round_id.value}/teams",
            AjaxCallbacks().on_complete_teams,
        )
    elif GameState.player_id == PlayerID():
        mylog.warning("dgo: In GameState.player_id=''")
        create_player_select_buttons(xpos, ypos)
    elif GameState.players_hand == []:
        mylog.warning("dgo: In GameState.players_hand=[]")
        AjaxRequests.get(
            f"/player/{GameState.player_id.value}/hand",
            AjaxCallbacks().on_complete_player_cards,
        )
    else:
        mylog.warning("dgo: In else clause")
        # Send the registration message.
        g_websocket.send_registration()

        if GameState.game_mode == 1:
            GameState.meld_score = 0
            GameState.round_bid = 0
            GameState.round_bid_trick_winner = PlayerID()
            GameState.trump = ""
            # update_status_line()

        if GameState.team_id == TeamID():
            # Set the GameState.team_id variable based on the player id chosen.
            for _temp, _value in GameState.team_dict.items():
                mylog.warning(
                    "dgo: Key: %s Value: %r", _temp, _value["player_ids"],
                )
                if GameState.player_id.value in _value["player_ids"]:
                    GameState.team_id = TeamID(_value["team_id"])
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
    mylog.error("In rebuild_display.")

    if GameState.game_mode is None and not GameState.game_dict:
        GameState.game_mode = 0

    if AjaxRequestTracker.outstanding_requests() > 0:
        mylog.warning(
            "rebuild_display: There are %d outstanding requests. Skipping clear.",
            AjaxRequestTracker.outstanding_requests(),
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
    mylog.error("In set_card_positions.")
    mylog.warning("set_card_positions: (mode=%s)", GAME_MODES[GameState.game_mode])

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
                AjaxRequests.get(
                    f"/round/{GameState.round_id.value}/kitty",
                    AjaxCallbacks().on_complete_kitty,
                )
        elif GAME_MODES[GameState.game_mode] in ["reveal"]:  # Reveal
            populate_canvas(GameState.kitty_deck, g_canvas, "kitty")
            populate_canvas(GameState.players_hand, g_canvas, "player")
        elif GAME_MODES[GameState.game_mode] in ["meld"]:  # Meld
            populate_canvas(
                GameState.meld_deck, g_canvas, GAME_MODES[GameState.game_mode]
            )
            populate_canvas(GameState.players_meld_deck, g_canvas, "player")
        elif GAME_MODES[GameState.game_mode] in ["trick"]:  # Trick
            populate_canvas(
                GameState.discard_deck, g_canvas, GAME_MODES[GameState.game_mode]
            )
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
            GameState.discard_deck,
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
    :type event: [type], optional
    """
    mylog.error("In resize_canvas")

    _height: float = 0.95 * window.innerHeight - document["game_header"].height
    g_canvas.style.height = f"{_height}px"
    g_canvas.fitContents()


## END Function definitions.

# Make the clear_display function easily available to plain javascript code.
window.bind("resize", resize_canvas)  # pylint: disable=no-member

# Fix the height of the space for player names by using dummy names
document["player_name"].height = document["player_name"].offsetHeight

# Attach the card graphics file
document["card_definitions"].attach(SVG.Definitions(filename=CARD_URL))

# Websocket holder
g_websocket: WSocketContainer = WSocketContainer()

# Create the base SVG object for the card table.
g_canvas = CardTable()
document["card_table"] <= g_canvas
resize_canvas()

document.getElementById("please_wait").text = ""

# Pre-populate some data. Each of these calls display_game_options.
AjaxRequests.get("/game", AjaxCallbacks().on_complete_games)
AjaxRequests.get("/getcookie/game_id", AjaxCallbacks().on_complete_getcookie)
AjaxRequests.get("/getcookie/player_id", AjaxCallbacks().on_complete_getcookie)
