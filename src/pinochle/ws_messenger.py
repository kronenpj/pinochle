"""
Encapsulates websocket message routines and tracks attached clients.
"""
import json
from typing import Optional

import geventwebsocket

from . import GLOBAL_LOG_LEVEL, custom_log, play_pinochle, roundteams
from .models import utils


class WebSocketMessenger:
    """
    Encapsulates websocket message routines and tracks attached clients.
    """

    __instance = None
    client_sockets = {}

    @staticmethod
    def get_instance():
        """ Static access method. """
        if WebSocketMessenger.__instance is None:
            WebSocketMessenger()
        return WebSocketMessenger.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if WebSocketMessenger.__instance is not None:
            raise Exception("This class is a singleton!")

        WebSocketMessenger.__instance = self

        self.mylog = custom_log.get_logger()
        self.mylog.setLevel(GLOBAL_LOG_LEVEL)
        self.mylog.info("Log level: %d", self.mylog.getEffectiveLevel())

    @property
    def game_update(self):
        """ Return stored function pointing to game.update """
        return self._game_update

    @game_update.setter
    def game_update(self, ext_game_update):
        assert callable(ext_game_update)
        self._game_update = ext_game_update

    def register_new_player(
        self, game_id: str, player_id: str, ws: geventwebsocket.websocket.WebSocket
    ) -> None:
        """
        Handle new player registrations.

        :param game_id: Game ID where the player wants to register.
        :type game_id: str
        :param player_id: Player ID of the registrant.
        :type player_id: str
        :param ws: Websocket corresponding to the registered player.
        :type ws: websocket.WebSocket
        """
        new_data = {"player_id": player_id, "ws": ws}

        try:
            # Try to replace existing WS for same player.
            self.client_sockets[game_id] = [
                x for x in self.client_sockets[game_id] if x["player_id"] != player_id
            ]
            self.mylog.info("Appending new_data.")
            self.client_sockets[game_id].append(new_data)
        except KeyError:
            self.client_sockets[game_id] = [new_data]

        # Gather information about the number of players and the game state.
        self.distribute_registered_players(game_id)

        self.update_refreshed_player_page(game_id, player_id, ws)

    def update_refreshed_player_page(self, game_id, player_id, ws):
        # Send this player information about the game, as appropriate, in case they've
        # just refreshed the page.
        # TODO: Replace this nonsense with a straightforward entire game/round/team/
        # player status message.
        game_mode = utils.query_game(game_id).state
        round_id = str(utils.query_gameround_for_game(game_id).round_id)
        self.update_refreshed_page_team_scores(round_id, ws)
        if "bid" in play_pinochle.GAME_MODES[game_mode]:
            self.update_refreshed_page_bid(round_id, player_id, ws)
        elif "reveal" in play_pinochle.GAME_MODES[game_mode]:
            self.update_refreshed_page_reveal(round_id, ws)
        elif "meld" in play_pinochle.GAME_MODES[game_mode]:
            try:
                self.update_refreshed_page_bid(round_id, player_id, ws)
            except IndexError:
                pass
            self.update_refreshed_page_trump(round_id, ws)

    @staticmethod
    def update_refreshed_page_team_scores(round_id, ws):
        a_roundteams = utils.query_roundteam_list(round_id)
        for a_roundteam in a_roundteams:
            a_team = utils.query_team(str(a_roundteam.team_id))
            ws.send(
                json.dumps(
                    {
                        "action": "team_score",
                        "team_id": str(a_roundteam.team_id),
                        "score": a_team.score,
                        "meld_score": 0,
                    }
                )
            )

    @staticmethod
    def update_refreshed_page_trump(round_id, ws):
        a_round = utils.query_round(round_id)
        ws.send(json.dumps({"action": "trump_selected", "trump": str(a_round.trump),}))

    @staticmethod
    def update_refreshed_page_reveal(round_id, ws):
        a_round = utils.query_round(round_id)
        ws.send(
            json.dumps(
                {
                    "action": "bid_winner",
                    "player_id": str(a_round.bid_winner),
                    "bid": a_round.bid,
                }
            )
        )

    @staticmethod
    def update_refreshed_page_bid(round_id, player_id, ws):
        # Try to figure out who is responsible for the next bid...
        ordered_player_list = play_pinochle.players_still_bidding(round_id)
        a_round = utils.query_round(round_id)

        current_bid = a_round.bid
        if current_bid > 20:
            next_bid_player_idx = play_pinochle.determine_next_bidder_player_id(
                player_id, ordered_player_list
            )
            player_bidding = ordered_player_list[next_bid_player_idx]
        else:
            player_bidding = ordered_player_list[
                a_round.round_seq % len(ordered_player_list)
            ]
            ws.send(
                json.dumps(
                    {
                        "action": "bid_prompt",
                        "player_id": player_bidding,
                        "bid": current_bid,
                    }
                )
            )

    def distribute_registered_players(self, game_id):
        """
        Send registrant list for the supplied game to all currently registered players. Also
        start the game within the server and send the game start message when the appropriate
        number of players have registered.

        :param game_id: Game ID to distribute player list.
        :type game_id: [type]
        """
        # Send a message to each client registered to this game.
        joined_players = [x["player_id"] for x in self.client_sockets[game_id]]
        if not joined_players:
            return

        round_id = str(utils.query_gameround_for_game(game_id).round_id)
        ordered_player_list = roundteams.create_ordered_player_list(round_id)
        self.websocket_broadcast(
            game_id,
            {
                "action": "notification_player_list",
                "game_id": game_id,
                "player_ids": joined_players,
                "player_order": ordered_player_list,
            },
        )

        # Gather information about the number of players and the game state.
        temp_round = str(utils.query_gameround_for_game(game_id).round_id)
        temp_team_list = utils.query_roundteam_list(temp_round)
        num_players = sum(
            len(utils.query_teamplayer_list(str(temp_team.team_id)))
            for temp_team in temp_team_list
        )
        game_mode = utils.query_game(game_id).state

        # In order to make the decision of whether the game should start.
        self.mylog.info("Players: %d - Game mode: %d", num_players, game_mode)
        if (
            len(joined_players) == num_players
            and "game" in play_pinochle.GAME_MODES[game_mode]
        ):
            self.mylog.info("Enough players have joined. Start the game!")
            try:
                self._game_update(game_id, state=True)
            except AttributeError:
                self.mylog.error(
                    "WebSocketMessenger: game_update was not set before use."
                )
            # TODO: This should be abstracted to be any kind of game.
            play_pinochle.start(temp_round)

    def websocket_broadcast(
        self, game_id: str, message: dict, exclude: Optional[str] = None
    ) -> None:
        """
        Send a websocket broadcast message to all players registered to a game,
        optionally excluding a player.

        :param game_id: ID of the game
        :type game_id:  str
        :param action:  Dictionary containing the structured message to send.
        :type action:   dict
        :param exclude: Player ID to exclude from broadcast.
        :type exclude:  str, optional
        """
        # If no registrations have occurred or none for the supplied game, continue.
        if not self.client_sockets or not self.client_sockets[game_id]:
            return

        for item in self.client_sockets[game_id]:
            cli_ws = item["ws"]
            if exclude and exclude in item["player_id"]:
                continue
            try:
                self.mylog.info("Sending message to client %r", cli_ws)
                cli_ws.send(json.dumps(message))
            except geventwebsocket.exceptions.WebSocketError:
                self.mylog.info(
                    "stream_socket: gevent WebSocketError: Client's websocket is closed."
                )
