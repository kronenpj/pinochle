"""
This is the round module and supports all the REST actions for the
round data
"""

import sqlalchemy
from flask import abort, make_response

from pinochle.config import db
from pinochle.models import Game, GameRound, GameRoundSchema, Round, RoundSchema

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
        rounds = Round.query.order_by(Round.timestamp).all()
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
    abort(404, f"Round not found for Id: {round_id}")


def create(game_id):
    """
    This function creates a new round in the round structure
    using the passed in game ID

    :param game_id:  Game ID to attach the new round
    :return:         201 on success, 406 on round exists
    """
    # Get the round requested from the db into session
    existing_game = Game.query.filter(Game.game_id == game_id).one_or_none()

    # Did we find an existing round?
    if existing_game is not None:
        # Create a round instance using the schema and the passed in round
        schema = RoundSchema()
        new_round = schema.load({}, session=db.session).data

        # Add the round to the database
        db.session.add(new_round)
        db.session.commit()

        # Serialize and return the newly created round in the response
        data = schema.dump(new_round).data

        # Also insert a record into the game_round table
        gr_schema = GameRoundSchema()
        gr_update = gr_schema.load(data, session=db.session).data

        # Set the id to the round we want to update
        gr_update.game_id = game_id

        # merge the new object into the old and commit it to the db
        db.session.merge(gr_update)
        db.session.commit()

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
        db_update = schema.load(a_round, session=db.session).data

        # Set the id to the round we want to update
        db_update.round_id = update_round.round_id

        # merge the new object into the old and commit it to the db
        db.session.merge(db_update)
        db.session.commit()

        # return updated round in the response
        data = schema.dump(update_round).data

        return data, 200

    # Otherwise, nope, didn't find that round
    abort(404, f"Round not found for Id: {round_id}")


def delete(game_id, round_id):
    """
    This function deletes a round from both the round structure and the game_round
    structure.

    :param game_id:    Id of the game where round belongs
    :param round_id:   Id of the round to delete
    :return:            200 on successful delete, 404 if not found
    """
    # Get the round requested
    a_round = Round.query.filter(Round.round_id == round_id).one_or_none()
    # Get the round requested
    g_round = GameRound.query.filter(
        GameRound.game_id == game_id, GameRound.round_id == round_id
    ).one_or_none()

    success = False

    # Did we find a game-round?
    if g_round is not None:
        db.session.delete(g_round)
        db.session.commit()
        success = True

    # Did we find a round?
    if a_round is not None:
        db.session.delete(a_round)
        db.session.commit()
        success = True

    if success:
        return make_response(f"Round {round_id} deleted", 200)

    # Otherwise, nope, didn't find that round
    abort(404, f"Round not found for Id: {round_id}")
