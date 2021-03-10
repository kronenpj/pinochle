"""
Tests for the various game classes.

License: GPLv3
"""
import unittest
from typing import List
from unittest import mock

import pytest
from pinochle.models import Game, Player, Team, TeamPlayers #, Hand
from pinochle.server import connex_app


@pytest.fixture
def app():
    app = connex_app.create_app()
    return app


class TestAPI(unittest.TestCase):
    team_names = ["Us", "Them"]
    player_names = ["Thing1", "Thing2", "Red", "Blue"]
    n_teams = len(team_names)
    n_players = len(player_names)
    n_kitty = 4

    # @pytest.mark.asyncio # Unknown annotation...
    def test_create_players(self):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/api/player' page is requested (GET)
        THEN check that the response is valid
        """
        # with mock.patch(
        #     "pinochle.config.sqlite_url", side_effect="/tmp/pinochle_test.db"
        # ):
        # TODO: Implement this test...
        pass
