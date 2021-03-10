"""
This is the roundkitty module and supports all the REST actions roundkitty data
"""

import sqlalchemy
from flask import abort, make_response

from pinochle.config import db
from pinochle.models import Round, RoundTeam, RoundTeamSchema, Team

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read(round_id):
    """
    This function responds to a request for /api/round/{round_id}
    with one matching round from round

    :param game_id:   Id of round to find
    :return:            round matching id
    """
    # Build the initial query
    a_round = (
        RoundTeam.query.filter(RoundTeam.round_id == round_id)
        # .outerjoin(Hand)
        .all()
    )

    # Did we find a round?
    if a_round is not None:
        # Serialize the data for the response
        data = {"round_id": round_id}
        temp = list()
        for _, team in enumerate(a_round):
            temp.append(team.team_id)
        data["team_ids"] = temp
        return data

    # Otherwise, nope, didn't find any rounds
    abort(404, f"No rounds found ID {round_id}")


def delete(game_id):
    """
    This function deletes a round from the round structure

    :param game_id:   Id of the round to delete
    :return:            200 on successful delete, 404 if not found
    """
    # Get the round requested
    a_round = RoundTeam.query.filter(RoundTeam.game_id == game_id).one_or_none()

    # Did we find a round?
    if a_round is not None:
        db.session.delete(a_round)
        db.session.commit()
        return make_response(f"round {game_id} deleted", 200)

    # Otherwise, nope, didn't find that round
    abort(404, f"round not found for Id: {game_id}")


## Manage the team's collected cards
def read(round_id):
    """
    This function responds to a get request for /api/round/{round_id}/{team_id}
    and returns the team's collected cards.

    :param round_id:   Id of round to find
    :param round_id:   Id of team to find
    :return:            List of cards collected by the team.
    """
    # Build the initial query
    # a_round = (
    #     RoundTeam.query.filter(RoundTeam.round_id == round_id)
    #     # .outerjoin(Hand)
    #     .all()
    # )

    # Did we find a round?
    # if a_round is not None:
    #     # Serialize the data for the response
    #     data = {"round_id": round_id}
    #     temp = list()
    #     for _, team in enumerate(a_round):
    #         temp.append(team.team_id)
    #     data["team_ids"] = temp
    #     return data
    return {"cards": [None]}

    # Otherwise, nope, didn't find any rounds
    abort(404, f"No rounds or team found for IDs {round_id}/{team_id}")


def addcard(round_id, team_id, card):
    """
    This function responds to a put request for /api/round/{round_id}/{team_id}
    and returns the team's collected cards.

    :param round_id:   Id of round to find
    :param team_id:    Id of team to find
    :return:        201 on success, 406 on team exists
    """
    # name = team.get("name")
    # existing_team = Team.query.filter(Team.name == name).one_or_none()
    # existing_team = None

    # Can we insert this team?
    # if existing_team is None:

    #     # Create a team instance using the schema and the passed in team
    #     schema = TeamSchema()
    #     new_team = schema.load(team, session=db.session).data

    #     # Add the team to the database
    #     db.session.add(new_team)
    #     db.session.commit()

    #     # Serialize and return the newly created team in the response
    #     data = schema.dump(new_team).data

    #     return data, 201

    # Otherwise, nope, team exists already
    # abort(409, f"Team {existing_team} exists already")


def deletecard(round_id, team_id, card):
    """
    This function responds to a delete request for /api/round/{round_id}/{team_id}
    and deletes the specified card from the team's collected cards.

    :param round_id:   Id of round to find
    :param team_id:    Id of team to find
    :param card:       Name of card to delete (suit_value)
    :return:        201 on success, 406 on team exists
    """
    # name = team.get("name")
    # existing_team = Team.query.filter(Team.name == name).one_or_none()
    # existing_team = None

    # Can we insert this team?
    # if existing_team is None:

    #     # Create a team instance using the schema and the passed in team
    #     schema = TeamSchema()
    #     new_team = schema.load(team, session=db.session).data

    #     # Add the team to the database
    #     db.session.add(new_team)
    #     db.session.commit()

    #     # Serialize and return the newly created team in the response
    #     data = schema.dump(new_team).data

    #     return data, 201

    # Otherwise, nope, team exists already
    # abort(409, f"Team {existing_team} exists already")
