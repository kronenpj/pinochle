"""
This is the hand module and supports common database queries for cards in a hand.
"""

from typing import List

from flask import abort, make_response

from pinochle.models import utils
from pinochle.models.core import db
from pinochle.models.hand import Hand, HandSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to internal (non-API) requests database access
    for reads of the hand table.

    :return:        json string of list of game rounds
    """
    # Create the list of game-rounds from our data
    hands = Hand.query.all()

    # Serialize the data for the response
    hand_schema = HandSchema(many=True)
    data = hand_schema.dump(hands)
    return data


def read_one(hand_id: str):
    """
    This function responds to internal (non-API) requests database access
    for reads of the hand table matching a hand_id

    :param hand_id:     Id of round to find
    :return:            List of cards from specified hand or None
    """
    # Build the initial query
    a_hand = utils.query_hand_list(hand_id=hand_id)

    # Did we find a hand?
    if hand_id is not None and a_hand is not None:
        # Serialize the data for the response
        temp = list()
        for _, card in enumerate(a_hand):
            temp.append(card.card)
        if len(temp) > 0:
            data = {"hand_id": hand_id, "cards": temp}
            return data

    # Otherwise, nope, didn't find any rounds with cards.
    return None


def addcard(hand_id: str, card: str):
    """
    This function responds to API requests database access
    by adding the specified card to the given hand_id.

    :param hand_id:    Id of the hand to receive the new card
    :param card:       String of the card to add to the collection.
    :return:           None.
    """
    if hand_id is not None and card is not None:
        # Create a hand instance using the schema and the passed in card
        schema = HandSchema()
        new_card = schema.load({"hand_id": hand_id, "card": card}, session=db.session)

        # Add the round to the database
        db.session.add(new_card)
        db.session.commit()
        return make_response(f"Card {card} added to player's hand", 201)

    # Otherwise, nope, didn't find that player
    abort(404, f"Could not add card to: {hand_id}/{card}")


def addcards(hand_id: str, cards: List[str]):
    """
    This function responds to API requests database access
    by adding the specified card to the given hand_id.

    :param hand_id:    Id of the hand to receive the new card
    :param card:       String of the card to add to the collection.
    :return:           None.
    """
    if hand_id is not None and cards is not None:
        # Create a hand instance using the schema and the passed in card
        schema = HandSchema(many=False)
        for item in cards:
            new_card = schema.load(
                {"hand_id": hand_id, "card": item}, session=db.session
            )

            # Add the round to the database
            db.session.add(new_card)
        db.session.commit()
        return make_response(f"Card {cards} added to player's hand", 201)

    # Otherwise, nope, didn't find that player
    abort(404, f"Could not add cards to: {hand_id}")


def deletecard(hand_id: str, card: str):
    """
    This function responds to API requests database access
    by deleting the specified card from the given hand_id.

    :param hand_id:    Id of the hand to receive the new card
    :param card:       String of the card to add to the collection.
    :return:           None.
    """
    if hand_id is not None and card is not None:
        # Create a hand instance using the schema and the passed in card
        a_card = utils.query_hand_card(hand_id=hand_id, card=card)

        if a_card is not None:
            # Delete the card from the database
            db_session = db.session()
            local_object = db_session.merge(a_card)
            db_session.delete(local_object)
            db_session.commit()
            return make_response(f"Player's card {card} deleted", 200)

    # Otherwise, nope, didn't find that player
    abort(404, f"Hand/card not found for: {hand_id}/{card}")


def deleteallcards(hand_id: str):
    """
    This function responds to API requests database access
    by deleting all the card from the given hand_id.

    :param hand_id:    Id of the hand to receive the new card
    :return:           None.
    """
    # Create a hand instance using the schema and the passed in card
    if hand_id is not None:
        a_card = utils.query_hand_list(hand_id)

        db_session = db.session()
        if a_card is not None:
            for item in a_card:
                # Delete the cards from the database
                local_object = db_session.merge(item)
                db_session.delete(local_object)
            db_session.commit()
            return make_response("All cards deleted", 200)

    # Otherwise, nope, didn't find that player
    abort(404, f"Error occurred deleting cards for: {hand_id}")
