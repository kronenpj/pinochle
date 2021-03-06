"""
This is the roundkitty module which supports the REST actions relating to roundkitty data
"""

from . import hand
from .models import utils
from .models.core import db
from .models.round_ import RoundSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read(round_id: str):
    """
    This function responds to a request for /api/round/{round_id}/kitty
    with the deck of cards in the kitty for the specified round

    :param round_id:    Id of round to find
    :return:            list of cards in the kitty or None
    """
    # Did we find a round?
    if round_id is None or round_id == "":
        return None

    # Build the initial query
    a_round = utils.query_round(str(round_id))

    # Did we find a round?
    if a_round is None:
        return None

    # Retrieve the hand_id from the returned data.
    round_schema = RoundSchema()
    temp_hand_data = round_schema.dump(a_round)
    hand_id = temp_hand_data["hand_id"]

    cards = utils.query_hand_list(hand_id)

    # Serialize the data for the response
    data = {}
    temp = [card.card for _, card in enumerate(cards)]
    data["cards"] = temp
    return data


def delete(round_id: str):
    """
    This function deletes the kitty cards for the round from the hand table

    :param round_id:   Id of the round to delete
    :return:           None
    """
    # print(f"{round_id=}")
    # Get the round requested
    if round_id is not None:
        # Retrieve the hand_id from the returned data.
        round_schema = RoundSchema()
        a_round = utils.query_round(str(round_id))
        temp_hand_data = round_schema.dump(a_round)
        if len(temp_hand_data) == 0:
            return
        hand_id = temp_hand_data["hand_id"]
        # print(f"{hand_id=}")

        hand.deleteallcards(hand_id)

        a_round.hand_id = None
        # merge the new object into the old and commit it to the db
        db.session.merge(a_round)
        db.session.commit()
