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


def update(trick_id: str, data: dict):
    """
    This function updates an existing round in the round structure

    :param trick_id:    Id of the round to update
    :param data:        String containing the data to update.
    :return:            Updated record.
    """
    return _update_data(trick_id, data)


def _update_data(trick_id: str, data: dict):
    """
    This function updates an existing round in the round structure

    :param round_id:    Id of the round to update in the round structure
    :param data:        Dictionary containing the data to update.
    :return:            Updated record.
    """
    # Get the trick requested from the db into session
    update_trick = utils.query_trick(trick_id=trick_id)

    # Did we find an existing round?
    if update_trick is None or update_trick == {}:
        # Otherwise, nope, didn't find that round
        abort(404, f"Trick not found for Id: {trick_id}")

    # turn the passed in round into a db object
    db_session = db.session()
    local_object = db_session.merge(update_trick)

    # Update any key present in data that isn't trick_id.
    for key in [x for x in data if x not in ["trick_id"]]:
        setattr(local_object, key, data[key])

    # Add the updated data to the transaction.
    db_session.add(local_object)
    db_session.commit()

    # return updated round in the response
    schema = TrickSchema()
    data = schema.dump(update_trick)

    return data, 200
