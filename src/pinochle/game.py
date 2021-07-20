"""
This is the game module and supports all the REST actions for the
game data
"""
from flask import abort, make_response

from pinochle import play_pinochle

from .models import utils
from .models.core import db
from .models.game import GameSchema
from .play_pinochle import GAME_MODES
from .ws_messenger import WebSocketMessenger as WSM

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to a request for /api/game
    with the complete lists of games

    :return:        json string of list of games
    """
    # Create the list of game from our data
    # games = Game.query.order_by(Game.timestamp).all()
    games = utils.query_game_list()

    # Serialize the data for the response
    game_schema = GameSchema(many=True)
    return game_schema.dump(games)


def read_one(game_id: str):
    """
    This function responds to a request for /api/game/{game_id}
    with one matching game from game

    :param game_id:    Id of game to find
    :return:           game matching id
    """
    # Build the initial query
    game = utils.query_game(game_id=game_id)

    # Did we find a game?
    if game is None:
        # Otherwise, nope, didn't find that game
        abort(404, f"Game not found for Id: {game_id}")

    # Serialize the data for the response
    game_schema = GameSchema()
    return game_schema.dump(game)


def create(kitty_size=0):
    """
    This function creates a new game in the game structure

    :param kitty_size:  Number of cards to allocate to the kitty, optional
    :type kitty_size:   int
    :return:            201 on success, 406 on game exists
    """

    # print(f"game.create: kitty_size={kitty_size}")
    # Create a game instance using the schema and the passed in game
    schema: GameSchema = GameSchema()
    new_game = schema.load({"kitty_size": kitty_size}, session=db.session)
    # print(f"game.create: new_game={new_game}")

    # Add the game to the database
    db.session.add(new_game)
    db.session.commit()

    # Serialize and return the newly created game in the response
    data = schema.dump(new_game)

    return data, 201


def update(game_id: str, kitty_size=None, state=None, dealer_id=None):
    """
    This function updates an existing game in the game structure

    :param game_id:     Id of the game to update in the game structure
    :param kitty_size:  Size of the new kitty.
    :type kitty_size:   int
    :param state:       Updated state.
    :type state:        boolean
    :param dealer_id:   Identifier of new dealer.
    :type dealer_id:    str
    :return:            Updated / new record.
    """
    if dealer_id:
        return _update_data(game_id, {"dealer_id": dealer_id})
    if kitty_size:
        return _update_data(game_id, {"kitty_size": kitty_size})
    if state:
        game = utils.query_game(game_id=game_id)
        if game is None:
            abort(409)
        current_state = game.state
        if current_state == 2 and game.kitty_size == 0:
            current_state += 1  # advance past kitty reveal.
        new_state = current_state + 1
        # print(f"game.update: mode: {new_state}, array length: {len(GAME_MODES)}")
        if new_state < len(GAME_MODES):
            # print(f"game.update: Returning game state(true): {new_state}")
            send_game_state_message(game_id, new_state)
            return _update_data(game_id, {"state": new_state})

        new_state = 1
        # Reset the game state
        _update_data(game_id, {"state": new_state})

        # Create and start a new round
        current_round = utils.query_gameround_for_game(game.game_id)
        # print(f"current_round is: {type(current_round)}")
        # print("game.update: Returning new round state(true).")
        return play_pinochle.new_round(game_id, str(current_round.round_id))

    # Send the current game state rather than advancing it.
    game = utils.query_game(game_id=game_id)
    # print(f"game.update: Returning game state(false): {game.state}")
    send_game_state_message(game_id, game.state)
    return {"state": game.state}, 200

def _update_data(game_id: str, data: dict):
    """
    This function updates an existing game in the game structure

    :param game_id:     Id of the game to update in the game structure
    :param data:        Dictionary containing the data to update.
    :return:            Updated record.
    """
    # Get the game requested from the db into session
    update_game = utils.query_game(game_id=game_id)

    # Did we find an existing game?
    if update_game is None or update_game == {}:
        # Otherwise, nope, didn't find that game
        abort(404, f"Game not found for Id: {game_id}")

    # turn the passed in game into a db object
    db_session = db.session()
    local_object = db_session.merge(update_game)

    # Update any key present in game that isn't game_id or game_seq.
    for key in [x for x in data if x not in ["game_id", "game_seq"]]:
        setattr(local_object, key, data[key])

    # Add the updated data to the transaction.
    db_session.add(local_object)
    db_session.commit()

    # return updated game in the response
    schema = GameSchema()
    data = schema.dump(update_game)

    return data, 200


def send_game_state_message(game_id, new_state):
    # print(f"game.send_game_state_message: Sending game state message: {new_state}")
    message = {"action": "game_state", "game_id": game_id, "state": new_state}
    ws_mess = WSM()
    ws_mess.game_update = update
    ws_mess.websocket_broadcast(game_id, message)


def delete(game_id: str):
    """
    This function deletes a game from the game structure

    :param game_id:   Id of the game to delete
    :return:            200 on successful delete, 404 if not found
    """
    # Get the game requested
    game = utils.query_game(game_id=game_id)

    # Did we find a game?
    if game is None or game == {}:
        # Otherwise, nope, didn't find that game
        abort(404, f"Game not found for Id: {game_id}")

    db.session.delete(game)
    db.session.commit()
    return make_response(f"Game {game_id} deleted", 200)
