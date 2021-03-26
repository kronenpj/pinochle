"""
This is the people module and supports all the REST actions for the
people data
"""

import sqlalchemy
from flask import abort, make_response

from pinochle import teamplayers
from pinochle.models.core import db
from pinochle.models.team import Team, TeamSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to a request for /api/team
    with the complete lists of teams

    :return:        json string of list of teams
    """
    # Create the list of team from our data
    teams = Team.query.order_by(Team.name).all()

    # Serialize the data for the response
    team_schema = TeamSchema(many=True)
    data = team_schema.dump(teams)
    return data


def read_one(team_id: str):
    """
    This function responds to a request for /api/team/{team_id}
    with one matching team from team

    :param team_id:   Id of team to find
    :return:            team matching id
    """
    # Build the initial query
    team = (
        Team.query.filter(Team.team_id == team_id)
        # .outerjoin(Hand)
        .one_or_none()
    )

    # Did we find a team?
    if team is not None:

        # Serialize the data for the response
        team_schema = TeamSchema()
        data = team_schema.dump(team)
        return data

    # Otherwise, nope, didn't find that team
    abort(404, f"Team not found for Id: {team_id}")


def create(team: str):
    """
    This function creates a new team in the team structure
    based on the passed in team data

    :param team:  team to create in team structure
    :return:        201 on success, 406 on team exists
    """
    # print(f"{team=}")
    name = team["name"]

    try:
        # Create a team instance using the schema and the passed in team
        schema = TeamSchema()
        new_team = schema.load({"name": name}, session=db.session)
        new_team.name = name

        # Add the team to the database
        db.session.add(new_team)
        db.session.commit()

        # Serialize and return the newly created team in the response
        data = schema.dump(new_team)

        return data, 201
    except sqlalchemy.exc.DataError:
        abort(409, f"Team {name} exists already")

    abort(400, f"Team {name} could not be added to the database.")


def update(team_id: str, team: dict):
    """
    This function updates an existing team in the team structure

    :param team_id:     Id of the team to update
    :param player_id:   Player to add
    :return:            updated team structure
    """
    # Get the team requested from the db into session
    update_team = Team.query.filter(Team.team_id == team_id).one_or_none()

    # Did we find an existing team?
    if update_team is not None:

        # turn the passed in team into a db object
        schema = TeamSchema()
        db_update = schema.load(team, session=db.session)

        # Set the id to the team we want to update
        db_update.team_id = update_team.team_id

        # merge the new object into the old and commit it to the db
        db.session.merge(db_update)
        db.session.commit()

        # return updated team in the response
        data = schema.dump(update_team)

        return data, 200

    # Otherwise, nope, didn't find that team
    abort(404, f"Team not found for Id: {team_id}")


def delete(team_id: str):
    """
    This function deletes a team from the team structure

    :param team_id:   Id of the team to delete
    :return:            200 on successful delete, 404 if not found
    """
    # Get the team requested
    team = Team.query.filter(Team.team_id == team_id).one_or_none()

    # Did we find a team?
    if team is not None:
        teamplayers.delete(team_id)
        db_session = db.session()
        local_object = db_session.merge(team)
        db_session.delete(local_object)
        db_session.commit()
        return make_response(f"Team {team_id} deleted", 200)

    # Otherwise, nope, didn't find that team
    abort(404, f"Team not found for Id: {team_id}")