"""
This is the teamplayer module and supports all the REST actions teamplayer data
"""

from flask import abort, make_response

from .models.core import db
from .models.player import Player
from .models.team import Team
from .models.teamplayers import TeamPlayers, TeamPlayersSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to a request for /api/team
    with the complete lists of teams

    :return:        json string of list of teams
    """
    # Create the list of team from our data
    teams = TeamPlayers.query.order_by(TeamPlayers.team_id).all()

    # Serialize the data for the response
    team_schema = TeamPlayersSchema(many=True)
    data = team_schema.dump(teams)
    return data


def read_one(team_id: str):
    """
    NOTE: This function says it responds to the same API request
    as team.read_one. Depending on the needs of the implementation
    this may be removed or enhanced.

    This function responds to a request for /api/team/{team_id}
    with one matching team from team

    :param team_id:   Id of team to find
    :return:            team matching id
    """
    # Build the initial query
    team = TeamPlayers.query.filter(TeamPlayers.team_id == team_id).all()
    team_info = Team.query.filter(Team.team_id == team_id).one_or_none()

    # Did we find a team?
    if team is not None and team != []:
        # Serialize the data for the response
        data = {"team_id": team_id}
        data["team_name"] = team_info.name
        temp = list()
        for _, one_team in enumerate(team):
            temp.append(one_team.player_id)
        data["player_ids"] = temp
        return data, 200

    # Otherwise, nope, didn't find that team
    abort(404, f"Team not found for Id: {team_id}")


def create(team_id: str, player_id: dict):
    """
    This function creates a new team in the team structure
    based on the passed in team data

    :param team_id:   team to add player to
    :param player_id: player to add to team
    :return:          201 on success, 406 on team doesn't exist
    """
    # Player_id comes as a dict, extract the value.
    p_id = player_id["player_id"]

    existing_team = Team.query.filter(Team.team_id == team_id).one_or_none()
    existing_player = Player.query.filter(Player.player_id == p_id).one_or_none()
    player_on_team = TeamPlayers.query.filter(
        TeamPlayers.team_id == team_id, TeamPlayers.player_id == p_id
    ).one_or_none()

    # Can we insert this team?
    if existing_team is None:
        abort(409, f"Team {team_id} doesn't already exist.")
    if existing_player is None:
        abort(409, f"Player {p_id} doesn't already exist.")
    if player_on_team is not None:
        abort(409, f"Player {p_id} is already on Team {team_id}.")

    # Create a team instance using the schema and the passed in team
    schema = TeamPlayersSchema()
    new_teamplayer = schema.load(
        {"team_id": team_id, "player_id": p_id}, session=db.session
    )

    # Add the team to the database
    db.session.add(new_teamplayer)
    db.session.commit()

    # Serialize and return the newly created team in the response
    data = schema.dump(new_teamplayer)

    return data, 201


def delete(team_id: str):
    """
    This function deletes a team from the team structure

    :param team_id:   Id of the team to delete
    :return:            200 on successful delete, 404 if not found
    """
    # Get the team requested
    team = TeamPlayers.query.filter(TeamPlayers.team_id == team_id).one_or_none()

    # Did we find a team?
    if team is not None:
        db_session = db.session()
        local_object = db_session.merge(team)
        db_session.delete(local_object)
        db_session.commit()
        return make_response(f"Team {team_id} deleted", 200)

    # Otherwise, nope, didn't find that team
    abort(404, f"Team not found for Id: {team_id}")
