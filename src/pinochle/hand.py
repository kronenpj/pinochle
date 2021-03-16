"""
This is the hand module and supports common database queries for cards in a hand.
"""

import sqlalchemy

from pinochle.config import db
from pinochle.models import Hand, HandSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to internal (non-API) requests database access
    for reads of the hand table.

    :return:        json string of list of game rounds
    """
    try:
        # Create the list of game-rounds from our data
        hands = Hand.query.all()
    except sqlalchemy.exc.NoForeignKeysError:  # Don't think this can happen.
        # Otherwise, nope, didn't find any game rounds
        return None

    # Serialize the data for the response
    hand_schema = HandSchema(many=True)
    data = hand_schema.dump(hands).data
    return data


def read_one(hand_id):
    """
    This function responds to internal (non-API) requests database access
    for reads of the hand table matching a hand_id

    :param hand_id:     Id of round to find
    :return:            List of cards from specified hand or None
    """
    # Build the initial query
    a_hand = Hand.query.filter(Hand.hand_id == hand_id).all()

    # Did we find a hand?
    if a_hand is not None:
        # Serialize the data for the response
        temp = list()
        for _, card in enumerate(a_hand):
            temp.append(card.card)
        data = {"hand_id": hand_id, "cards": temp}
        return data

    # Otherwise, nope, didn't find any rounds
    return None


def addcard(hand_id, card):
    """
    This function responds to internal (non-API) requests database access
    by adding the specified card to the given hand_id.

    :param hand_id:    Id of the hand to receive the new card
    :param card:       String of the card to add to the collection.
    :return:           None.
    """
    if hand_id is not None and card is not None:
        # Create a hand instance using the schema and the passed in card
        schema = HandSchema()
        new_card = schema.load(
            {"hand_id": hand_id, "card": card}, session=db.session
        ).data

        # Add the round to the database
        db.session.add(new_card)
        db.session.commit()

        # Serialize and return the newly created card in the response
    # TODO: Stop lying. Actually retreive the data from the database instead of
    # recycling the data that may or may not have been inserted into the database.
    # data = schema.dump(new_card).data


def deletecard(hand_id, card):
    """
    This function responds to internal (non-API) requests database access
    by deleting the specified card from the given hand_id.

    :param hand_id:    Id of the hand to receive the new card
    :param card:       String of the card to add to the collection.
    :return:           None.
    """
    if hand_id is not None and card is not None:
        # Create a hand instance using the schema and the passed in card
        schema = HandSchema()
        a_card = schema.load(
            {"hand_id": hand_id, "card": card}, session=db.session
        ).data

        if a_card is not None:
            # Delete the card from the database
            db.session.delete(a_card)
            db.session.commit()


def deleteallcards(hand_id):
    """
    This function responds to internal (non-API) requests database access
    by deleting all the card from the given hand_id.

    :param hand_id:    Id of the hand to receive the new card
    :return:           None.
    """
    # Create a hand instance using the schema and the passed in card
    if hand_id is not None:
        a_card = Hand.query.filter(Hand.hand_id == hand_id).all()

        if a_card is not None:
            for item in a_card:
                # Delete the cards from the database
                db.session.delete(item)
            db.session.commit()
