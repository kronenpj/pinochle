"""
This is the roundplayer module and supports all the REST actions roundplayer data
"""

from flask import abort, make_response

from .models import utils
from .models.core import db
from .models.gameround import GameRoundSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to a request for /api/gameround
    with the complete lists of game rounds

    :return:        json string of list of game rounds
    """
    # Create the list of game-rounds from our data
    games = utils.query_gameround_list()

    # Serialize the data for the response
    game_schema = GameRoundSchema(many=True)
    return game_schema.dump(games)


def read_rounds(game_id: str):
    """
    This function responds to a request for /api/game/{game_id} (GET)
    with one matching round from round

    :param game_id:     Id of round to find
    :return:            round matching id
    """
    # Build the initial query
    a_round_list = utils.query_gameround_for_game(game_id=game_id)

    # Did we find a round?
    if a_round_list is not None:
        # print(f"{a_round_list=}")
        # Serialize the data for the response
        game_schema = GameRoundSchema()
        return game_schema.dump(a_round_list)

    # Otherwise, nope, didn't find any rounds
    abort(404, f"No rounds found for game {game_id}")


def read_one(game_id: str, round_id: str):
    """
    This function responds to a request for /api/game/{game_id}/{round_id}
    with one matching round from round

    :param game_id:     Id of round to find
    :param round_id:    Id of round to find
    :return:            round matching id
    """
    # Build the initial query
    a_round = utils.query_gameround(game_id=game_id, round_id=round_id)

    # Did we find a round?
    if a_round is not None:
        # Serialize the data for the response
        game_schema = GameRoundSchema()
        return game_schema.dump(a_round)

    # Otherwise, nope, didn't find any rounds
    abort(404, f"No rounds found for game {game_id}")


def create(game_id: str, round_id: dict):
    """
    This function creates a new round in the round structure
    based on the passed in round data

    :param game_id:   game to add round to
    :param round_id: round to add to game
    :return:          201 on success, 406 on round doesn't exist
    """
    # Player_id comes as a dict, extract the value.
    r_id = round_id["round_id"]

    # print(f"game_id={game_id} round_id={r_id}")
    existing_game = utils.query_game(game_id=game_id)
    existing_round = utils.query_round(round_id=r_id)
    game_round = utils.query_gameround(game_id=game_id, round_id=r_id)

    # Can we insert this round?
    if existing_game is None:
        abort(409, f"round {game_id} doesn't already exist.")
    if existing_round is None:
        abort(409, f"Round {r_id} doesn't already exist.")
    if game_round is not None:
        abort(409, f"Round {r_id} is already associated with Game {game_id}.")

    # Create a round instance using the schema and the passed in round
    schema = GameRoundSchema()
    new_gameround = schema.load(
        {"game_id": game_id, "round_id": r_id}, session=db.session
    )

    # Add the round to the database
    db.session.add(new_gameround)
    db.session.commit()

    # Serialize and return the newly created round in the response
    data = schema.dump(new_gameround)

    return data, 201


def update(game_id: str, round_id: str, data: dict):
    """
    This function updates an existing game/round in the gameround structure

    :param game_id:     Id of the game to update
    :param round_id:    Id of the round to update
    :param data:        Dictionary containing the data to update.
    :return:            Updated record.
    """
    return _update_data(game_id, round_id, data)


def _update_data(game_id: str, round_id: str, data: dict):
    """
    This function updates an existing round in the round structure

    :param game_id:     Id of the game to update
    :param round_id:    Id of the round to update
    :param data:        Dictionary containing the data to update.
    :return:            Updated record.
    """
    # Get the round requested from the db into session
    update_round = utils.query_gameround(game_id=game_id, round_id=round_id)

    # Did we find an existing round?
    if update_round is None:
        # Otherwise, nope, didn't find that round
        abort(404, f"Round {round_id} not found for Id: {game_id}")

    # turn the passed in round into a db object
    db_session = db.session()
    local_object = db_session.merge(update_round)

    # Update any key present in a_round that isn't round_id or round_seq.
    for key in [x for x in data if x not in ["game_id", "round_id"]]:
        setattr(local_object, key, data[key])

    # Add the updated data to the transaction.
    db_session.add(local_object)
    db_session.commit()

    # return updated round in the response
    schema = GameRoundSchema()
    data = schema.dump(update_round)

    return data, 200


def delete(game_id: str, round_id: str):
    """
    This function deletes a round from the round structure

    :param game_id:   Id of the round to delete
    :return:            200 on successful delete, 404 if not found
    """
    # Get the round requested
    a_round = utils.query_gameround(game_id=game_id, round_id=round_id)

    # Did we find a round?
    if a_round is not None:
        db_session = db.session()
        local_object = db_session.merge(a_round)
        db_session.delete(local_object)
        db_session.commit()
        return make_response(f"round {game_id} deleted", 200)

    # Otherwise, nope, didn't find that round
    abort(404, f"round not found for Id: {game_id}")
