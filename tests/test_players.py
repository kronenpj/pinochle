"""
Tests for the various game classes.

License: GPLv3
"""
import unittest
from typing import List

from pinochle import card, deck, object_helpers, score_meld, utils
from pinochle.game import game, hand, player, team


class TestGameClasses(unittest.TestCase):
    team_names = ["Us", "Them"]
    player_names = ["Thing1", "Thing2", "Red", "Blue"]
    n_teams = len(team_names)
    n_players = len(player_names)
    n_kitty = 4
    teams: List[team.Team]

    def setUp(self):
        self.teams = []
        c_players = 0
        for i_team in range(len(self.team_names)):
            players = []
            for __ in range(int(len(self.player_names) / len(self.team_names))):
                players.append(player.Player(name=self.player_names[c_players]))
                c_players += 1
            self.teams.append(team.Team(name=self.team_names[i_team], players=players))

    def test_scenario_1(self):

        first_hand = hand.Hand(teams=self.teams)
        new_game = game.Game(hands=[first_hand])

        assert len(new_game.hands) == 1
        assert len(new_game.hands[0].teams) == self.n_teams
        assert len(new_game.hands[0].teams[0].players) == int(
            self.n_players / self.n_teams
        )

    def test_scenario_2(self):
        new_game = object_helpers.create_new_game(self.teams)

        # Add a new hand to the game.
        object_helpers.append_new_hand_to_game(game=new_game)

        assert len(new_game.hands) == 2
        for i_hand in new_game.hands:
            assert len(i_hand.teams) == self.n_teams
            for i_team in range(self.n_teams):
                assert i_hand.teams[i_team].team_id == self.teams[i_team].team_id
                assert len(i_hand.teams[i_team].players) == int(
                    self.n_players / self.n_teams
                )

    def test_scenario_3(self):
        new_game = object_helpers.create_new_game(self.teams)

        # Add a new hand to the game.
        object_helpers.append_new_hand_to_game(game=new_game, teams=self.teams)

        assert len(new_game.hands) == 2
        for i_hand in new_game.hands:
            assert len(i_hand.teams) == self.n_teams
            for i_team in range(self.n_teams):
                assert i_hand.teams[i_team].team_id == self.teams[i_team].team_id
                assert len(i_hand.teams[i_team].players) == int(
                    self.n_players / self.n_teams
                )
