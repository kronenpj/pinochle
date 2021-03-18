"""
This is the roundkitty module which supports the REST actions relating to roundkitty data
"""

from pinochle import hand
from pinochle.models.core import db
from pinochle.models.hand import Hand
from pinochle.models.round_ import Round, RoundSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read(round_id):
    """
    This function responds to a request for /api/round/{round_id}/kitty
    with the deck of cards in the kitty for the specified round

    :param round_id:    Id of round to find
    :return:            list of cards in the kitty or None
    """
    # Build the initial query
    a_round = Round.query.filter(Round.round_id == round_id).one_or_none()

    # Did we find a round?
    if a_round is not None:
        # Retrieve the hand_id from the returned data.
        round_schema = RoundSchema()
        temp_hand_data = round_schema.dump(a_round).data
        hand_id = temp_hand_data["hand_id"]

        cards = Hand.query.filter(Hand.hand_id == hand_id).all()

        # Serialize the data for the response
        data = dict()
        temp = list()
        for _, card in enumerate(cards):
            temp.append(card.card)
        data["cards"] = temp
        return data

    # Otherwise, nope, didn't find any rounds
    return None


def delete(round_id):
    """
    This function deletes the kitty cards for the round from the hand table

    :param round_id:   Id of the round to delete
    :return:           None
    """
    # Get the round requested
    if round_id is not None:
        # Retrieve the hand_id from the returned data.
        round_schema = RoundSchema()
        a_round = Round.query.filter(Round.round_id == round_id).one_or_none()
        temp_hand_data = round_schema.dump(a_round).data
        if len(temp_hand_data) == 0:
            return
        hand_id = temp_hand_data["hand_id"]
        

        hand.deleteallcards(hand_id)

        a_round.hand_id = None
        # merge the new object into the old and commit it to the db
        db.session.merge(a_round)
        db.session.commit()
