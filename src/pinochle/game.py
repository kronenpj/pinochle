"""
This is the game module and supports all the REST actions for the
game data
"""
import json

from flask import abort, make_response

from pinochle.models.core import db
from pinochle.models.game import Game, GameSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to a request for /api/game
    with the complete lists of games

    :return:        json string of list of games
    """
    # Create the list of game from our data
    games = Game.query.order_by(Game.timestamp).all()

    # Serialize the data for the response
    game_schema = GameSchema(many=True)
    data = game_schema.dump(games)
    return data


def read_one(game_id):
    """
    This function responds to a request for /api/game/{game_id}
    with one matching game from game

    :param game_id:   Id of game to find
    :return:            game matching id
    """
    # Build the initial query
    game = Game.query.filter(Game.game_id == game_id).one_or_none()

    # Did we find a game?
    if game is not None:
        # Serialize the data for the response
        game_schema = GameSchema()
        data = game_schema.dump(game)
        return data

    # Otherwise, nope, didn't find that game
    abort(404, f"Game not found for Id: {game_id}")


def create():
    """
    This function creates a new game in the game structure

    :return:        201 on success, 406 on game exists
    """

    # Create a game instance using the schema and the passed in game
    schema: GameSchema = GameSchema()
    new_game = schema.load({}, session=db.session)

    # Add the game to the database
    db.session.add(new_game)
    db.session.commit()

    # Serialize and return the newly created game in the response
    data = schema.dump(new_game)

    return data, 201


def update(game_id, game):
    """
    This function updates an existing game in the game structure

    :param game_id:   Id of the game to update in the game structure
    :param game:      game to update
    :return:            updated game structure
    """
    # Get the game requested from the db into session
    update_game = Game.query.filter(Game.game_id == game_id).one_or_none()

    # Did we find an existing game?
    if update_game is not None:

        # turn the passed in game into a db object
        schema = GameSchema(many=True)
        db_update = schema.load(game, session=db.session)

        # Set the id to the game we want to update
        db_update.game_id = update_game.game_id

        # merge the new object into the old and commit it to the db
        db.session.merge(db_update)
        db.session.commit()

        # return updated game in the response
        data = schema.dump(update_game)

        return data, 200

    # Otherwise, nope, didn't find that game
    abort(404, f"Game not found for Id: {game_id}")


def delete(game_id):
    """
    This function deletes a game from the game structure

    :param game_id:   Id of the game to delete
    :return:            200 on successful delete, 404 if not found
    """
    # Get the game requested
    game = Game.query.filter(Game.game_id == game_id).one_or_none()

    # Did we find a game?
    if game is not None:
        db.session.delete(game)
        db.session.commit()
        return make_response(f"Game {game_id} deleted", 200)

    # Otherwise, nope, didn't find that game
    abort(404, f"Game not found for Id: {game_id}")
