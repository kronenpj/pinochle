"""
Tests for the various game classes.

License: GPLv3
"""
import unittest
from typing import List
from unittest import mock

import pytest
from pinochle.models import Game, Hand, Player, Team, TeamPlayers
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

    @pytest.mark.asyncio
    def test_create_players(self):
        """
        GIVEN a Flask application configured for testing
        WHEN the '/' page is requested (GET)
        THEN check that the response is valid
        """
        with mock.patch(
            "pinochle.config.sqlite_url", side_effect="/tmp/pinochle_test.db"
        ):
            flask_app = connex_app.create_app('flask_test.cfg')
                # Attempt to access the new prize page, which requires authentication.
            response = flask_app.fetch("/api/player")
            self.assertEqual(200, response.code)
            # Log.debug(RESPONSE_BODY_.format(str(response.body)))
            self.assertEqual(
                flask_app.USERNAME_PROMPT_HTML_.format(""), response.body.decode()
            )
