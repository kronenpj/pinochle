"""
This is the round module and supports all the REST actions for the
round data
"""

import sqlalchemy
from flask import abort, make_response

from pinochle.config import db
from pinochle.models import Round, RoundSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to a request for /api/round
    with the complete lists of rounds

    :return:        json string of list of rounds
    """
    try:
        # Create the list of round from our data
        rounds = Round.query.order_by(Round.name).all()
    except sqlalchemy.exc.NoForeignKeysError:
        # Otherwise, nope, didn't find any players
        abort(404, "No Rounds defined in database")

    # Serialize the data for the response
    round_schema = RoundSchema(many=True)
    data = round_schema.dump(rounds).data
    return data


def read_one(round_id):
    """
    This function responds to a request for /api/round/{round_id}
    with one matching round from round

    :param round_id:   Id of round to find
    :return:            round matching id
    """
    # Build the initial query
    a_round = (
        Round.query.filter(Round.round_id == round_id)
        # .outerjoin(Round)
        .one_or_none()
    )

    # Did we find a round?
    if round is not None:

        # Serialize the data for the response
        round_schema = RoundSchema()
        data = round_schema.dump(a_round).data
        return data

    # Otherwise, nope, didn't find that round
    else:
        abort(404, f"Round not found for Id: {round_id}")


def create(a_round):
    """
    This function creates a new round in the round structure
    based on the passed in round data

    :param round:  round to create in round structure
    :return:        201 on success, 406 on round exists
    """

    # Create a round instance using the schema and the passed in round
    schema = RoundSchema()
    new_round = schema.load(a_round, session=db.session).data

    # Add the round to the database
    db.session.add(new_round)
    db.session.commit()

    # Serialize and return the newly created round in the response
    data = schema.dump(new_round).data

    return data, 201


def update(round_id, a_round):
    """
    This function updates an existing round in the round structure

    :param round_id:   Id of the round to update in the round structure
    :param round:      round to update
    :return:            updated round structure
    """
    # Get the round requested from the db into session
    update_round = Round.query.filter(Round.round_id == round_id).one_or_none()

    # Did we find an existing round?
    if update_round is not None:

        # turn the passed in round into a db object
        schema = RoundSchema()
        update = schema.load(a_round, session=db.session).data

        # Set the id to the round we want to update
        update.round_id = update_round.round_id

        # merge the new object into the old and commit it to the db
        db.session.merge(update)
        db.session.commit()

        # return updated round in the response
        data = schema.dump(update_round).data

        return data, 200

    # Otherwise, nope, didn't find that round
    else:
        abort(404, f"Round not found for Id: {round_id}")


def delete(round_id):
    """
    This function deletes a round from the round structure

    :param round_id:   Id of the round to delete
    :return:            200 on successful delete, 404 if not found
    """
    # Get the round requested
    a_round = Round.query.filter(Round.round_id == round_id).one_or_none()

    # Did we find a round?
    if a_round is not None:
        db.session.delete(a_round)
        db.session.commit()
        return make_response(f"Round {round_id} deleted", 200)

    # Otherwise, nope, didn't find that round
    else:
        abort(404, f"Round not found for Id: {round_id}")
