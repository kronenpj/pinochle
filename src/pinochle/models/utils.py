"""
Database utilities to consolidate db activity and simplify other parts of the application.

"""
from typing import List, Optional

from .core import db  # pragma: no cover
from .game import Game
from .gameround import GameRound
from .hand import Hand
from .player import Player
from .round_ import Round
from .roundteam import RoundTeam
from .team import Team
from .teamplayers import TeamPlayers
from .trick import Trick


# This is used for database debugging only. No test coverage needed.
def dump_db():  # pragma: no cover
    con = db.engine.raw_connection()
    for line in con.iterdump():
        if "INSERT" in line:
            print("%s\n" % line)


def query_game(game_id: str) -> Game:
    """
    Retrieve information about the specified game.

    :param game_id: [description]
    :type game_id: str
    :return: [description]
    :rtype: Dict
    """
    return Game.query.filter(Game.game_id == game_id).one_or_none()


def query_game_list() -> List[Game]:
    """
    Retrieve list of games in the database.

    :return: [description]
    :rtype: List[Dict]
    """
    return Game.query.order_by(Game.timestamp.desc()).all()


def query_hand_list(hand_id: str) -> List[Hand]:
    """
    Retrieve list of cards contained in the specified hand.

    :param hand_id: [description]
    :type hand_id: str
    :return: [description]
    :rtype: List[Dict]
    """
    return Hand.query.filter(Hand.hand_id == hand_id).order_by(Hand.seq).all()


def query_hand_card(hand_id: str, card: str) -> Optional[Hand]:
    """
    Query whether the specified hand contains the specified card.

    :param hand_id: [description]
    :type hand_id: str
    :param card: [description]
    :type card: str
    :return: [description]
    :rtype: Dict
    """
    retval = Hand.query.filter(Hand.hand_id == hand_id, Hand.card == card).all()
    if retval:
        return retval[0]
    return None


def query_player(player_id: str) -> Player:
    """
    Retrieve information about the specified player.

    :param player_id: [description]
    :type player_id: str
    :return: [description]
    :rtype: Dict
    """
    return Player.query.filter(Player.player_id == player_id).one_or_none()


def query_player_list() -> List[Player]:
    """
    Retrieve information about all the players.

    :return: [description]
    :rtype: List[Dict]
    """
    return Player.query.order_by(Player.name).all()


def query_round(round_id: str) -> Round:
    """
    Retrieve information about the specified round.

    :param round_id: [description]
    :type round_id: str
    :return: [description]
    :rtype: Dict
    """
    return Round.query.filter(Round.round_id == round_id).one_or_none()


def query_gameround(game_id: str, round_id: str) -> GameRound:
    """
    Retrieve information about the specified game/round.

    :param game_id: [description]
    :type game_id: str
    :param round_id: [description]
    :type round_id: str
    :return: [description]
    :rtype: Dict
    """
    return GameRound.query.filter(
        GameRound.game_id == game_id, GameRound.round_id == round_id
    ).one_or_none()


def query_gameround_for_game(game_id: str) -> GameRound:
    """
    Retrieve information about the active round for a given game.

    :param game_id: [description]
    :type game_id: str
    :return: [description]
    :rtype: GameRound
    """
    temp = GameRound.query.filter(
        GameRound.game_id == game_id, GameRound.active_flag is True
    ).one_or_none()

    # Sqlite stores active_flag as 1 but doesn't compare favorably with True.
    if temp is None:
        temp = GameRound.query.filter(
            GameRound.game_id == game_id, GameRound.active_flag == 1
        ).one_or_none()

    # print(f"gameround={temp}")
    return temp


def query_gameround_for_round(round_id: str) -> GameRound:
    """
    Retrieve information about the active round for a given game.

    :param game_id: [description]
    :type game_id: str
    :return: [description]
    :rtype: GameRound
    """
    temp = GameRound.query.filter(
        GameRound.round_id == round_id, GameRound.active_flag is True
    ).one_or_none()

    # Sqlite stores active_flag as 1 but doesn't compare favorably with True.
    if temp is None:
        temp = GameRound.query.filter(
            GameRound.round_id == round_id, GameRound.active_flag == 1
        ).one_or_none()

    # print(f"gameround={temp}")
    return temp


def query_gameround_list() -> List[GameRound]:
    """
    Retrieve information about all game/round.

    :return: [description]
    :rtype: List[Dict]
    """
    return GameRound.query.order_by(GameRound.timestamp).all()


def query_round_list() -> List[Round]:
    """
    Retrieve information about all rounds.

    :return: [description]
    :rtype: List[Dict]
    """
    return Round.query.order_by(Round.timestamp).all()


def query_roundteam(round_id: str, team_id: str) -> RoundTeam:
    """
    Retrieve information about a specified round/team pair.

    :param round_id: [description]
    :type round_id: str
    :param team_id: [description]
    :type team_id: str
    :return: [description]
    :rtype: List[Dict]
    """
    return RoundTeam.query.filter(
        RoundTeam.round_id == round_id, RoundTeam.team_id == team_id
    ).one_or_none()


def query_team(team_id: str) -> Team:
    """
    Retrieve information about a specified team pair.

    :param team_id: [description]
    :type team_id: str
    :return: [description]
    :rtype: Team
    """
    return Team.query.filter(Team.team_id == team_id).one_or_none()


def query_roundteam_list(round_id: str) -> List[RoundTeam]:
    """
    Retrieve information about the specified roundteam.

    :param round_id: [description]
    :type round_id: str
    :return: [description]
    :rtype: List[Dict]
    """
    return (
        RoundTeam.query.filter(RoundTeam.round_id == round_id)
        .order_by(RoundTeam.team_order)
        .all()
    )


def query_roundteam_with_hand(round_id: str, team_id: str) -> RoundTeam:
    """
    Retrieve information about the specified round/team pair.

    :param round_id: [description]
    :type round_id: str
    :param team_id: [description]
    :type team_id: str
    :return: [description]
    :rtype: Dict
    """
    return RoundTeam.query.filter(
        RoundTeam.round_id == round_id,
        RoundTeam.team_id == team_id,
        RoundTeam.hand_id is not None,
    ).one_or_none()


def query_teamplayer_list(team_id: str) -> List[TeamPlayers]:
    """
    Retrieve information about the specified teamplayers.

    :param team_id: [description]
    :type team_id: str
    :return: [description]
    :rtype: List[Dict]
    """
    return (
        TeamPlayers.query.filter(TeamPlayers.team_id == team_id)
        .order_by(TeamPlayers.player_order)
        .all()
    )


def query_player_ids_for_round(round_id: str) -> List[str]:
    """
    Query the database for the list of player IDs in this round.

    :param round_id: Round ID to query
    :type round_id: str
    :return: [description]
    :rtype: List[str]
    """
    # print(f"round_id={round_id}")
    # Get the round requested
    a_round: Round = query_round(round_id)

    # Did we find a round?
    if a_round is None or a_round == {}:
        return []

    # Retrieve the information for the round and teams.
    round_t = query_roundteam_list(round_id)

    player_ids = []
    # Collect the individual players from the round's teams.
    for t_team_id in [str(x.team_id) for x in round_t]:
        for team_info in query_teamplayer_list(t_team_id):
            # Add each player to the list
            player_ids.append(str(team_info.player_id))

    return player_ids


def query_trick(trick_id: str) -> Trick:
    """
    Retrieve information about the specified round.

    :param round_id: [description]
    :type round_id: str
    :return: [description]
    :rtype: Dict
    """
    return Trick.query.filter(Trick.trick_id == trick_id).one_or_none()


def query_trick_for_round_id(round_id: str) -> Trick:
    """
    Retrieve the specified trick.

    :param trick_id: [description]
    :type trick_id: str
    :return: [description]
    :rtype: Dict
    """
    trick_list = Trick.query.filter(Trick.round_id == round_id).order_by(Trick._id).all()
    # print(f"query_trick_for_round_id: {trick_list=}")
    if trick_list:
        return trick_list[len(trick_list) - 1]

    return None


def query_all_tricks_for_round_id(round_id: str) -> List[Trick]:
    """
    Retrieve the specified trick.

    :param trick_id: [description]
    :type trick_id: str
    :return: [description]
    :rtype: Dict
    """
    return Trick.query.filter(Trick.round_id == round_id).order_by(Trick._id).all()


def query_all_tricks() -> List[Trick]:
    """
    Retrieve the specified trick.

    :param trick_id: [description]
    :type trick_id: str
    :return: [description]
    :rtype: Dict
    """
    return Trick.query.filter().all()
