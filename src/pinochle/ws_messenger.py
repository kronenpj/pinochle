"""
Encapsulates websocket message routines and tracks attached clients.
"""
import json
from typing import Optional

import geventwebsocket

from . import GLOBAL_LOG_LEVEL, custom_log
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

        self.websocket_broadcast(
            game_id,
            {
                "action": "notification_player_list",
                "game_id": game_id,
                "player_ids": joined_players,
            },
        )

        # Gather information about the number of players and the game state.
        temp_round = utils.query_gameround_for_game(game_id).round_id
        temp_team_list = utils.query_roundteam_list(temp_round)
        num_players = sum(
            len(utils.query_teamplayer_list(str(temp_team.team_id)))
            for temp_team in temp_team_list
        )
        game_mode = utils.query_game(game_id).state

        # In order to make the decision of whether the game should start.
        self.mylog.info("Players: %d - Game mode: %d", num_players, game_mode)
        if len(joined_players) == num_players and game_mode == 0:
            self.mylog.info("Enough players have joined. Start the game!")
            try:
                self._game_update(game_id, state=True)
            except AttributeError:
                self.mylog.error(
                    "WebSocketMessenger: game_update was not set before use."
                )
            self.websocket_broadcast(game_id, {"action": "game_start"})

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
