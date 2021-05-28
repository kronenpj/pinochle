"""
Routines commonly used in tests

"""
from random import choice
from typing import List

import regex
from pinochle import game, gameround, player, round_, roundteams, team, teamplayers
from pinochle.models import utils
from pinochle.models.game import Game
from pinochle.models.player import Player
from pinochle.models.roundteam import RoundTeam

UUID_REGEX_TEXT = r"^([a-f\d]{8}(-[a-f\d]{4}){3}-[a-f\d]{12}?)$"
UUID_REGEX = regex.compile(UUID_REGEX_TEXT)

TEAM_NAMES = ["Us", "Them"]
PLAYER_NAMES = ["Thing1", "Thing2", "Red", "Blue"]

CARD_LIST = ["club_9", "diamond_ace", "heart_jack", "spade_10"]


def create_game(kitty_size=0) -> str:
    """
    Create a game in the database.

    :param kitty_size: Number of cards to allocate to the kitty.
    :type kitty_size: int
    :return: UUID of the created game (game_id)
    :rtype: str
    """
    # Create a new game
    db_response, status = game.create(kitty_size)
    assert status == 201
    assert db_response is not None
    game_id = str(db_response.get("game_id"))
    assert UUID_REGEX.match(game_id)

    return game_id


def set_game_state(game_id: str, state=0):
    """
    Set the state of a game in the database.

    :param game_id:   Id of the game to update.
    :type game_id:    str
    :param state:     Number of cards to allocate to the kitty.
    :type state:      int
    :return:          UUID of the created game (game_id)
    :rtype:           str
    """
    # Create a new game
    game._update_data(game_id, {"state": state})  # pylint: disable=protected-access
    game_: Game = query_game_data(game_id)
    assert game_.state == state


def create_round(game_id: str) -> str:
    """
    Create a round in the database.

    :param game_id: UUID of the game to which the round belongs
    :type game_id: str
    :return: UUID of the created round (round_id)
    :rtype: str
    """
    # Create a new round
    db_response, status = round_.create(game_id)
    assert status == 201
    assert db_response is not None
    round_id = db_response.get("round_id")
    assert UUID_REGEX.match(round_id)

    return round_id


def create_team(team_name: str) -> str:
    """
    Create a team in the database.

    :param team_name: Name of the team to create
    :type team_name: str
    :return: UUID of the created team (team_id)
    :rtype: str
    """
    # Create a new team
    db_response, status = team.create({"name": team_name})
    assert status == 201
    assert db_response is not None
    team_id = db_response.get("team_id")
    assert UUID_REGEX.match(team_id)

    return team_id


def create_player(player_name: str) -> str:
    """
    Create a player in the database.

    :param player_name: Name of the player to be created
    :type player_name: str
    :return: UUID of the created player (player_id)
    :rtype: str
    """
    # Create a new player
    db_response, status = player.create({"name": player_name})
    assert status == 201
    assert db_response is not None
    player_id = db_response.get("player_id")
    assert UUID_REGEX.match(player_id)

    return player_id


def create_teamplayer(team_id: str, player_id: str) -> None:
    # Create a new teamplayer
    db_response, status = teamplayers.create(team_id, {"player_id": player_id})
    assert status == 201
    assert db_response is not None


def create_roundteam(round_id: str, team_ids: List[str]) -> None:
    # Create new round-teams associations
    db_response, status = roundteams.create(round_id, team_ids)
    assert status == 201
    assert db_response is not None


def query_team_hand_id(round_id: str, team_id: str) -> str:
    # Build the query to extract the hand_id
    rt_data = RoundTeam.query.filter(
        RoundTeam.round_id == round_id,
        RoundTeam.team_id == team_id,
        RoundTeam.hand_id is not None,
    ).one_or_none()

    if rt_data is None:
        return ""

    # Extract the properly formatted UUID.
    hand_id = str(rt_data.hand_id)

    return hand_id


def query_player_hand_id(player_id: str) -> str:
    # Build the query to extract the hand_id
    rt_data = Player.query.filter(
        Player.player_id == player_id, Player.hand_id is not None,
    ).one_or_none()

    if rt_data is None:
        return ""

    # Extract the properly formatted UUID.
    hand_id = str(rt_data.hand_id)

    return hand_id


def query_game_data(game_id: str) -> Game:
    # Build the query to extract the hand_id
    rt_data = Game.query.filter(Game.game_id == game_id).one_or_none()

    return rt_data


def setup_complete_game(kitty_s: int):
    # Create a new game
    game_id = str(create_game(kitty_s))

    # Create a new round
    round_id = str(create_round(game_id))

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    assert db_response is not None

    db_response = gameround.read_one(game_id, round_id)
    assert db_response is not None

    # Create players
    player_ids = []
    for player_name in PLAYER_NAMES:
        player_id = create_player(player_name)
        assert UUID_REGEX.match(player_id)
        player_ids.append(player_id)

    # Create a new teams
    team_ids = []
    for item in range(2):
        team_id = create_team(choice(TEAM_NAMES))
        team_ids.append(team_id)
        teamplayers.create(team_id=team_id, player_id={"player_id": player_ids[item]})
        teamplayers.create(
            team_id=team_id, player_id={"player_id": player_ids[item + 2]}
        )

    # Create the roundteam association for the teams.
    roundteams.create(round_id=round_id, teams=team_ids)

    # The order expected by the tests is to be the same as the game, which is not the
    # order from the original list.
    return game_id, round_id, team_ids, utils.query_player_ids_for_round(round_id)
