"""
This is the hand module and supports all the REST actions for the
hand data
"""

import sqlalchemy
from flask import abort, make_response

from pinochle.config import db
from pinochle.models import Hand, HandSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to a request for /api/hand
    with the complete lists of hands

    :return:        json string of list of hands
    """
    try:
        # Create the list of hand from our data
        hands = Hand.query.order_by(Hand.name).all()
    except sqlalchemy.exc.NoForeignKeysError:
        # Otherwise, nope, didn't find any players
        abort(404, "No Hands defined in database")

    # Serialize the data for the response
    hand_schema = HandSchema(many=True)
    data = hand_schema.dump(hands).data
    return data


def read_one(hand_id):
    """
    This function responds to a request for /api/hand/{hand_id}
    with one matching hand from hand

    :param hand_id:   Id of hand to find
    :return:            hand matching id
    """
    # Build the initial query
    hand = (
        Hand.query.filter(Hand.hand_id == hand_id)
        # .outerjoin(Hand)
        .one_or_none()
    )

    # Did we find a hand?
    if hand is not None:

        # Serialize the data for the response
        hand_schema = HandSchema()
        data = hand_schema.dump(hand).data
        return data

    # Otherwise, nope, didn't find that hand
    else:
        abort(404, f"Hand not found for Id: {hand_id}")


def create(hand):
    """
    This function creates a new hand in the hand structure
    based on the passed in hand data

    :param hand:  hand to create in hand structure
    :return:        201 on success, 406 on hand exists
    """
    name = hand.get("name")

    existing_hand = Hand.query.filter(Hand.name == name).one_or_none()

    # Can we insert this hand?
    if existing_hand is None:

        # Create a hand instance using the schema and the passed in hand
        schema = HandSchema()
        new_hand = schema.load(hand, session=db.session).data

        # Add the hand to the database
        db.session.add(new_hand)
        db.session.commit()

        # Serialize and return the newly created hand in the response
        data = schema.dump(new_hand).data

        return data, 201

    # Otherwise, nope, hand exists already
    else:
        abort(409, f"Hand {name} exists already")


def update(hand_id, hand):
    """
    This function updates an existing hand in the hand structure

    :param hand_id:   Id of the hand to update in the hand structure
    :param hand:      hand to update
    :return:            updated hand structure
    """
    # Get the hand requested from the db into session
    update_hand = Hand.query.filter(Hand.hand_id == hand_id).one_or_none()

    # Did we find an existing hand?
    if update_hand is not None:

        # turn the passed in hand into a db object
        schema = HandSchema()
        update = schema.load(hand, session=db.session).data

        # Set the id to the hand we want to update
        update.hand_id = update_hand.hand_id

        # merge the new object into the old and commit it to the db
        db.session.merge(update)
        db.session.commit()

        # return updated hand in the response
        data = schema.dump(update_hand).data

        return data, 200

    # Otherwise, nope, didn't find that hand
    else:
        abort(404, f"Hand not found for Id: {hand_id}")


def delete(hand_id):
    """
    This function deletes a hand from the hand structure

    :param hand_id:   Id of the hand to delete
    :return:            200 on successful delete, 404 if not found
    """
    # Get the hand requested
    hand = Hand.query.filter(Hand.hand_id == hand_id).one_or_none()

    # Did we find a hand?
    if hand is not None:
        db.session.delete(hand)
        db.session.commit()
        return make_response(f"Hand {hand_id} deleted", 200)

    # Otherwise, nope, didn't find that hand
    else:
        abort(404, f"Hand not found for Id: {hand_id}")
