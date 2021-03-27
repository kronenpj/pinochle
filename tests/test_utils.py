"""
Routines commonly used in tests

"""
import regex
from pinochle import (
    game,
    player,  # gameround,; roundkitty,; roundteams,
    round_,
    team,
    teamplayers,
)
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


def query_team_hand_id(round_id: str, team_id: str) -> str:
    # Build the query to extract the hand_id
    rt_data = RoundTeam.query.filter(
        RoundTeam.round_id == round_id,
        RoundTeam.team_id == team_id,
        RoundTeam.hand_id is not None,
    ).one_or_none()

    if rt_data is not None:
        # Extract the properly formatted UUID.
        hand_id = str(rt_data.hand_id)

        return hand_id

    return None


def query_player_hand_id(player_id: str) -> str:
    # Build the query to extract the hand_id
    rt_data = Player.query.filter(
        Player.player_id == player_id, Player.hand_id is not None,
    ).one_or_none()

    if rt_data is not None:
        # Extract the properly formatted UUID.
        hand_id = str(rt_data.hand_id)

        return hand_id

    return None
