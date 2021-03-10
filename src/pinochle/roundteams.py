"""
This is the roundplayer module and supports all the REST actions roundplayer data
"""

import sqlalchemy
from flask import abort, make_response

from pinochle.config import db
from pinochle.models import Round, RoundTeam, RoundTeamSchema, Team

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to a request for /api/RoundTeam
    with the complete lists of game rounds

    :return:        json string of list of game rounds
    """
    try:
        # Create the list of game-rounds from our data
        games = RoundTeam.query.order_by(RoundTeam.timestamp).all()
    except sqlalchemy.exc.NoForeignKeysError:
        # Otherwise, nope, didn't find any game rounds
        abort(404, "No Rounds defined in database for any game")

    # Serialize the data for the response
    game_schema = RoundTeamSchema(many=True)
    data = game_schema.dump(games).data
    return data


def read_one(round_id):
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


def create(round_id, teams):
    """
    This function creates a new round in the round-team structure
    based on the passed in team data

    :param round_id:  round to add
    :param teams:     teams to associate with round
    :return:          201 on success, 406 on round doesn't exist
    """
    # Teams should come as a list, loop over the values.
    for t_id in teams:

        existing_round = Round.query.filter(Round.round_id == round_id).one_or_none()
        # This needs to deal with multiple t_ids.
        existing_team = Team.query.filter(Team.team_id == t_id).one_or_none()
        player_on_round = RoundTeam.query.filter(
            RoundTeam.round_id == round_id, RoundTeam.team_id == t_id
        ).one_or_none()

        # Can we insert this round?
        if existing_round is None:
            abort(409, f"Round {round_id} doesn't already exist.")
        if existing_team is None:
            abort(409, f"Team {t_id} doesn't already exist.")
        if player_on_round is not None:
            abort(409, f"Team {t_id} is already associated with Round {round_id}.")

        # Create a round instance using the schema and the passed in round
        schema = RoundTeamSchema()
        new_roundteam = schema.load(
            {"round_id": round_id, "team_id": t_id}, session=db.session
        ).data

        # Add the round to the database
        db.session.add(new_roundteam)

    db.session.commit()

    # Serialize and return the newly created round in the response
    data = schema.dump(new_roundteam).data
    # NOTE: This only returns the last team supplied, not the entire list.

    return data, 201


def update(game_id, round_id):
    """
    This function updates an existing round in the round structure

    :param game_id:     Id of the round to update
    :param round_id:    Round to add
    :return:            updated round structure
    """
    # Get the round requested from the db into session
    update_round = RoundTeam.query.filter(
        RoundTeam.game_id == game_id, RoundTeam.round_id == round_id
    ).one_or_none()

    # Did we find an existing round?
    if update_round is not None:

        # turn the passed in round into a db object
        schema = RoundTeamSchema()
        db_update = schema.load(round_id, session=db.session).data

        # Set the id to the round we want to update
        db_update.game_id = update_round.game_id

        # merge the new object into the old and commit it to the db
        db.session.merge(db_update)
        db.session.commit()

        # return updated round in the response
        data = schema.dump(update_round).data

        return data, 200

    # Otherwise, nope, didn't find that round
    abort(404, f"Round {round_id} not found for Id: {game_id}")


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
