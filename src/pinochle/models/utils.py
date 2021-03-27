"""
Database utilities to consolidate db activity and simplify other parts of the application.

"""
from typing import Dict, List

from .core import db  # pragma: no cover
from .game import Game
from .gameround import GameRound
from .hand import Hand
from .player import Player
from .round_ import Round
from .roundteam import RoundTeam
from .teamplayers import TeamPlayers


# This is used for database debugging only. No test coverage needed.
def dump_db():  # pragma: no cover
    con = db.engine.raw_connection()
    for line in con.iterdump():
        if "INSERT" in line:
            print("%s\n" % line)


def query_game(game_id: str) -> Dict:
    """
    Retrieve information about the specified game.

    :param game_id: [description]
    :type game_id: str
    :return: [description]
    :rtype: Dict
    """
    temp = Game.query.filter(Game.game_id == game_id).one_or_none()
    return temp


def query_game_list() -> List[Dict]:
    """
    Retrieve list of games in the database.

    :return: [description]
    :rtype: List[Dict]
    """
    temp = Game.query.order_by(Game.timestamp.desc()).all()
    return temp


def query_hand_list(hand_id: str) -> List[Dict]:
    """
    Retrieve list of cards contained in the specified hand.

    :param hand_id: [description]
    :type hand_id: str
    :return: [description]
    :rtype: List[Dict]
    """
    temp = Hand.query.filter(Hand.hand_id == hand_id).all()
    return temp


def query_hand_card(hand_id: str, card: str) -> Dict:
    """
    Query whether the specified hand contains the specified card.

    :param hand_id: [description]
    :type hand_id: str
    :param card: [description]
    :type card: str
    :return: [description]
    :rtype: Dict
    """
    temp = Hand.query.filter(Hand.hand_id == hand_id, Hand.card == card).one_or_none()
    return temp


def query_player(player_id: str) -> Dict:
    """
    Retrieve information about the specified player.

    :param player_id: [description]
    :type player_id: str
    :return: [description]
    :rtype: Dict
    """
    temp = Player.query.filter(Player.player_id == player_id).one_or_none()
    return temp


def query_player_list() -> List[Dict]:
    """
    Retrieve information about all the players.

    :return: [description]
    :rtype: List[Dict]
    """
    temp = Player.query.order_by(Player.name).all()
    return temp


def query_round(round_id: str) -> Dict:
    """
    Retrieve information about the specified round.

    :param round_id: [description]
    :type round_id: str
    :return: [description]
    :rtype: Dict
    """
    temp = Round.query.filter(Round.round_id == round_id).one_or_none()
    return temp


def query_gameround(game_id: str, round_id: str) -> Dict:
    """
    Retrieve information about the specified game/round.

    :param game_id: [description]
    :type game_id: str
    :param round_id: [description]
    :type round_id: str
    :return: [description]
    :rtype: Dict
    """
    temp = GameRound.query.filter(
        GameRound.game_id == game_id, GameRound.round_id == round_id
    ).one_or_none()
    return temp


def query_round_list_for_game(game_id: str) -> Dict:
    """
    Retrieve information about the active round for a given game.

    :param game_id: [description]
    :type game_id: str
    :return: [description]
    :rtype: List[Dict]
    """
    temp = GameRound.query.filter(
        GameRound.game_id == game_id, GameRound.active_flag is True
    ).one_or_none()

    # Sqlite stores active_flag as 1 but doesn't compare favorably with True.
    if temp is None:
        temp = GameRound.query.filter(
            GameRound.game_id == game_id, GameRound.active_flag == 1
        ).one_or_none()

    # print(f"round_list={temp}")
    return temp


def query_gameround_list() -> List[Dict]:
    """
    Retrieve information about all game/round.

    :return: [description]
    :rtype: List[Dict]
    """
    temp = GameRound.query.order_by(GameRound.timestamp).all()
    return temp


def query_round_list() -> List[Dict]:
    """
    Retrieve information about all rounds.

    :return: [description]
    :rtype: List[Dict]
    """
    temp = Round.query.order_by(Round.timestamp).all()
    return temp


def query_roundteam(round_id: str, team_id: str) -> Dict:
    """
    Retrieve information about a specified round/team pair.

    :param round_id: [description]
    :type round_id: str
    :param team_id: [description]
    :type team_id: str
    :return: [description]
    :rtype: List[Dict]
    """
    temp = RoundTeam.query.filter(
        RoundTeam.round_id == round_id, RoundTeam.team_id == team_id
    ).one_or_none()
    return temp


def query_roundteam_list(round_id: str) -> List[Dict]:
    """
    Retrieve information about the specified roundteam.

    :param round_id: [description]
    :type round_id: str
    :return: [description]
    :rtype: List[Dict]
    """
    temp = RoundTeam.query.filter(RoundTeam.round_id == round_id).all()
    return temp


def query_roundteam_with_hand(round_id: str, team_id: str) -> Dict:
    """
    Retrieve information about the specified round/team pair.

    :param round_id: [description]
    :type round_id: str
    :param team_id: [description]
    :type team_id: str
    :return: [description]
    :rtype: Dict
    """
    temp = RoundTeam.query.filter(
        RoundTeam.round_id == round_id,
        RoundTeam.team_id == team_id,
        RoundTeam.hand_id is not None,
    ).one_or_none()
    return temp


def query_teamplayer_list(team_id: str) -> List[Dict]:
    """
    Retrieve information about the specified teamplayers.

    :param team_id: [description]
    :type team_id: str
    :return: [description]
    :rtype: List[Dict]
    """
    temp = TeamPlayers.query.filter(TeamPlayers.team_id == team_id).all()
    return temp


def update_player_meld_score(player_id: str, meld_score: int) -> bool:
    """
    Update player's meld score in the database.

    :param player_id: [description]
    :type player_id: str
    :param meld_score: [description]
    :type meld_score: int
    :return: Update success or failure.
    :rtype: bool
    """
    temp = Player.query.filter(Player.player_id == player_id).one_or_none()

    if temp is None:
        return False

    db_session = db.session()
    local_object = db_session.merge(temp)
    # Set the updated meld score
    local_object.meld_score = meld_score

    # merge the new object into the old and commit it to the db
    db_session.merge(local_object)
    db_session.commit()

    return True
