"""
This is the round module and supports all the REST actions for the
round data
"""

from typing import List

from flask import abort, make_response

from . import gameround
from .models import utils
from .models.core import db
from .models.round_ import Round, RoundSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to a request for /api/round
    with the complete lists of rounds

    :return:        json string of list of rounds
    """
    # Create the list of round from our data
    rounds: List[Round] = utils.query_round_list()

    if not rounds:
        # Otherwise, nope, didn't find any players
        abort(404, "No Rounds defined in database")

    # Serialize the data for the response
    round_schema = RoundSchema(many=True)
    return round_schema.dump(rounds)


def read_one(round_id: str):
    """
    This function responds to a request for /api/round/{round_id}
    with one matching round from round

    :param round_id:   Id of round to find
    :return:            round matching id
    """
    # Build the initial query
    a_round = utils.query_round(round_id)

    # Did we find a round?
    if a_round is None:
        # Otherwise, nope, didn't find that round
        abort(404, f"Round not found for Id: {round_id}")

    # Serialize the data for the response
    round_schema = RoundSchema()
    return round_schema.dump(a_round)


def create(game_id: str):
    """
    This function creates a new round in the round structure
    using the passed in game ID

    :param game_id:  Game ID to attach the new round
    :return:         201 on success, 406 on round exists
    """
    # Get the round requested from the db into session
    existing_game = utils.query_game(game_id)

    # Did we find an existing round?
    if existing_game is None:
        abort(400, f"Counld not create new round for game {game_id}.")

    # Create a round instance using the schema and the passed in round
    schema = RoundSchema()
    _round = schema.load({}, session=db.session)
    # TODO: Find more appropriate way to declare minimum bid.
    _round.bid = 20

    # Add the round to the database
    db.session.add(_round)
    db.session.commit()

    # Serialize and return the newly created round in the response
    data = schema.dump(_round)

    round_id = data["round_id"]

    # Also insert a record into the game_round table
    # print(f"game_id={game_id} round_id={round_id}")
    return gameround.create(game_id=game_id, round_id={"round_id": round_id})


def update(round_id: str, a_round: dict):
    """
    This function updates an existing round in the round structure

    :param game_id:     Id of the game to update - unused.
    :param round_id:    Id of the round to update
    :param data:        String containing the data to update.
    :return:            Updated record.
    """
    return _update_data(round_id, a_round)


def _update_data(round_id: str, data: dict):
    """
    This function updates an existing round in the round structure

    :param round_id:    Id of the round to update in the round structure
    :param data:        Dictionary containing the data to update.
    :return:            Updated record.
    """
    # Get the round requested from the db into session
    update_round = utils.query_round(round_id=round_id)

    # Did we find an existing round?
    if update_round is None or update_round == {}:
        # Otherwise, nope, didn't find that round
        abort(404, f"Round not found for Id: {round_id}")

    # turn the passed in round into a db object
    db_session = db.session()
    local_object = db_session.merge(update_round)

    # Update any key present in data that isn't round_id or round_seq.
    for key in [x for x in data if x not in ["round_id"]]:
        setattr(local_object, key, data[key])

    # Add the updated data to the transaction.
    db_session.add(local_object)
    db_session.commit()

    # return updated round in the response
    schema = RoundSchema()
    data = schema.dump(update_round)

    return data, 200


def delete(game_id: str, round_id: str):
    """
    This function deletes a round from both the round structure and the game_round
    structure.

    :param game_id:    Id of the game where round belongs
    :param round_id:   Id of the round to delete
    :return:            200 on successful delete, 404 if not found
    """
    # Get the round requested
    a_round = utils.query_round(round_id)
    g_round = gameround.read_one(game_id=game_id, round_id=round_id)

    # Did we find a game-round?
    if g_round is None or a_round is None:
        # Otherwise, nope, didn't find that round
        abort(404, f"Round not found for Id: {round_id}")

    gameround.delete(game_id=game_id, round_id=round_id)
    db_session = db.session()
    local_object = db_session.merge(a_round)
    db_session.delete(local_object)
    db_session.commit()
    return make_response(f"Round {round_id} deleted", 200)
