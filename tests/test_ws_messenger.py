"""
Tests for the ws_messenger module.

License: GPLv3
"""

from unittest.mock import MagicMock
import geventwebsocket
from pinochle import game, play_pinochle
from pinochle.models import utils
from pinochle.ws_messenger import WebSocketMessenger as WSM

import test_utils

# from pinochle.models.utils import dump_db


def test_register_new_player(
    app, patch_ws_messenger
):  # pylint: disable=unused-argument
    """
    GIVEN a Flask application configured for testing
    WHEN the register_new_player function is called
    THEN check that the response is successful
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    ws_mess = WSM.get_instance()
    ws_mess.client_sockets.clear()
    ws_mess.game_update = game.update
    dummy_ws = geventwebsocket.websocket.WebSocket(None, None, None)
    ws_mess.register_new_player(game_id, player_ids[0], dummy_ws)

    assert len(ws_mess.client_sockets) == 1
    assert len(ws_mess.client_sockets[game_id]) == 1
    assert isinstance(
        ws_mess.client_sockets[game_id][0]["ws"], geventwebsocket.websocket.WebSocket
    )
    assert ws_mess.client_sockets[game_id][0]["ws"] == dummy_ws


def test_register_four_players(
    app, patch_ws_messenger
):  # pylint: disable=unused-argument
    """
    GIVEN a Flask application configured for testing
    WHEN the register_new_player function is called
    THEN check that the response is successful
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    ws_mess = WSM.get_instance()
    ws_mess.client_sockets.clear()
    ws_mess.game_update = game.update
    dummy_ws = geventwebsocket.websocket.WebSocket(None, None, None)
    assert utils.query_game(game_id).state == 0

    for player_id in player_ids:
        ws_mess.register_new_player(game_id, player_id, dummy_ws)

    assert utils.query_game(game_id).state == 1


def test_register_new_players_game_0(
    app, patch_ws_messenger
):  # pylint: disable=unused-argument
    """
    GIVEN a Flask application configured for testing
    WHEN the register_new_player function is called
    THEN check that the response is successful
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    ws_mess = WSM.get_instance()
    ws_mess.client_sockets.clear()
    ws_mess.game_update = game.update
    ws_mess.distribute_registered_players = MagicMock()

    dummy_ws = geventwebsocket.websocket.WebSocket(None, None, None)
    ws_mess.register_new_player(game_id, player_ids[0], dummy_ws)
    ws_mess.register_new_player(game_id, player_ids[1], dummy_ws)

    assert len(ws_mess.client_sockets) == 1
    assert len(ws_mess.client_sockets[game_id]) == 2
    ws_mess.distribute_registered_players.assert_called()
    ws_mess.distribute_registered_players.assert_called_with(game_id)


def test_register_new_players_game_bid(
    app, patch_ws_messenger
):  # pylint: disable=unused-argument
    """
    GIVEN a Flask application configured for testing
    WHEN the register_new_player function is called
    THEN check that the response is successful
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    ws_mess = WSM.get_instance()
    ws_mess.client_sockets.clear()
    ws_mess.game_update = game.update
    ws_mess.update_refreshed_page_bid = MagicMock()
    ws_mess.update_refreshed_page_reveal = MagicMock()
    ws_mess.update_refreshed_page_trump = MagicMock()

    dummy_ws = geventwebsocket.websocket.WebSocket(None, None, None)
    play_pinochle.start(round_id)
    test_utils.set_game_state(game_id, 1)
    assert utils.query_game(game_id).state == 1
    ws_mess.register_new_player(game_id, player_ids[0], dummy_ws)
    ws_mess.register_new_player(game_id, player_ids[1], dummy_ws)

    ws_mess.update_refreshed_page_bid.assert_called_with(
        round_id, player_ids[1], dummy_ws
    )
    ws_mess.update_refreshed_page_reveal.assert_not_called()
    ws_mess.update_refreshed_page_trump.assert_not_called()


def test_register_new_players_game_reveal(
    app, patch_ws_messenger
):  # pylint: disable=unused-argument
    """
    GIVEN a Flask application configured for testing
    WHEN the register_new_player function is called
    THEN check that the response is successful
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    ws_mess = WSM.get_instance()
    ws_mess.client_sockets.clear()
    ws_mess.game_update = game.update
    ws_mess.update_refreshed_page_bid = MagicMock()
    ws_mess.update_refreshed_page_reveal = MagicMock()
    ws_mess.update_refreshed_page_trump = MagicMock()

    dummy_ws = geventwebsocket.websocket.WebSocket(None, None, None)
    play_pinochle.start(round_id)
    test_utils.set_game_state(game_id, 3)
    assert utils.query_game(game_id).state == 3
    ws_mess.register_new_player(game_id, player_ids[0], dummy_ws)
    ws_mess.register_new_player(game_id, player_ids[1], dummy_ws)

    ws_mess.update_refreshed_page_bid.assert_not_called()
    ws_mess.update_refreshed_page_reveal.assert_called_with(round_id, dummy_ws)
    ws_mess.update_refreshed_page_trump.assert_not_called()


def test_register_new_players_game_trump(
    app, patch_ws_messenger
):  # pylint: disable=unused-argument
    """
    GIVEN a Flask application configured for testing
    WHEN the register_new_player function is called
    THEN check that the response is successful
    """
    game_id, round_id, team_ids, player_ids = test_utils.setup_complete_game(4)

    ws_mess = WSM.get_instance()
    ws_mess.client_sockets.clear()
    ws_mess.game_update = game.update
    ws_mess.update_refreshed_page_bid = MagicMock()
    ws_mess.update_refreshed_page_reveal = MagicMock()
    ws_mess.update_refreshed_page_trump = MagicMock()

    dummy_ws = geventwebsocket.websocket.WebSocket(None, None, None)
    play_pinochle.start(round_id)
    test_utils.set_game_state(game_id, 4)
    assert utils.query_game(game_id).state == 4
    ws_mess.register_new_player(game_id, player_ids[0], dummy_ws)
    ws_mess.register_new_player(game_id, player_ids[1], dummy_ws)

    ws_mess.update_refreshed_page_bid.assert_called_with(
        round_id, player_ids[1], dummy_ws
    )
    ws_mess.update_refreshed_page_reveal.assert_not_called()
    ws_mess.update_refreshed_page_trump.assert_called_with(round_id, dummy_ws)
