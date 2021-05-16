"""
This is the trick module and supports common database queries for cards in a trick.
"""

from flask import abort

from .models import utils
from .models.core import db
from .models.trick import TrickSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def create(round_id: str):
    """
    This function creates a new trick in the trick structure
    using the passed in round ID

    :param game_id:  Round ID to associate the new trick to
    :return:         201 on success, 400 on round not found
    """
    # Get the round requested from the db into session
    existing_round = utils.query_round(round_id)

    # Did we find an existing round?
    if existing_round is None:
        abort(400, f"Counld not create new trick for round {round_id}.")

    # Create a trick instance using the schema and the passed in round
    schema = TrickSchema()
    _trick = schema.load({}, session=db.session)
    _trick.round_id = round_id

    # Add the trick to the database
    db.session.add(_trick)
    db.session.commit()

    # Serialize and return the newly created trick in the response
    data = schema.dump(_trick)

    return data, 201


def read_one(trick_id: str):
    """
    This function responds to a request for /api/round/{round_id}
    with one matching round from round

    :param round_id:   Id of round to find
    :return:            round matching id
    """
    # Build the initial query
    a_trick = utils.query_trick(trick_id)

    # Did we find a trick?
    if a_trick is None:
        # Otherwise, nope, didn't find that round
        abort(404, f"Trick not found for Id: {trick_id}")

    # Serialize the data for the response
    trick_schema = TrickSchema()
    return trick_schema.dump(a_trick)
