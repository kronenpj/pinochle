"""
This is the player module and supports all the REST actions for the
player data
"""

import sqlalchemy
from flask import abort, make_response

from . import hand
from .models import utils
from .models.core import db
from .models.hand import HandSchema
from .models.player import PlayerSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to a request for /api/player
    with the complete lists of players

    :return:        json string of list of players
    """
    # Create the list of player from our data
    players = utils.query_player_list()

    # Serialize the data for the response
    player_schema = PlayerSchema(many=True)
    return player_schema.dump(players)


def read_one(player_id: str):
    """
    This function responds to a request for /api/player/{player_id}
    with one matching player from player

    :param player_id:   Id of player to find
    :return:            player matching id
    """
    if not player_id or player_id in {"", "hand"}:
        abort(404, "Player_id not supplied.")

    # Build the initial query
    player = utils.query_player(player_id)

    # Did we find a player?
    if player is not None:
        # Serialize the data for the response
        player_schema = PlayerSchema()
        return player_schema.dump(player)

    # Otherwise, nope, didn't find that player
    abort(404, f"Player not found for Id: {player_id}")


def read_hand(player_id: str):
    """
    This function responds to a request for /api/player/{player_id} (GET)
    with one matching player from player

    :param player_id:   Id of player to find
    :return:            player matching id
    """
    # Build the initial query
    player = utils.query_player(player_id)

    # Did we find a player?
    if player is not None:
        # print(f"read_hand: player={player}")
        hand_id = str(player.hand_id)
        # print(f"read_hand: hand_id={hand_id}")
        player_hand = utils.query_hand_list(hand_id=hand_id)
        # print(f"read_hand: player_hand={player_hand}")
        # Serialize the data for the response
        hand_schema = HandSchema(many=True)
        return hand_schema.dump(player_hand)

    # Otherwise, nope, didn't find that player
    abort(404, f"Player not found for Id: {player_id}")


def create(player: dict):
    """
    This function creates a new player in the player structure
    based on the passed in player data

    :param player:  player to create in player structure
    :return:        201 on success, 409 on player exists, 400 on other error
    """
    name = player["name"]

    try:
        # Create a player instance using the schema and the passed in player
        schema = PlayerSchema()
        new_player = schema.load({"name": name}, session=db.session)

        # Add the player to the database
        db.session.add(new_player)
        db.session.commit()

        # Serialize and return the newly created player in the response
        data = schema.dump(new_player)

        return data, 201
    except sqlalchemy.exc.DataError:
        abort(409, f"Player {name} exists already")

    abort(400, f"Player {name} could not be added to the database.")


def addcard(player_id: str, card: dict):
    """
    This function responds to internal (non-API) database access requests
    by adding the specified card to the given hand_id.

    :param hand_id:    Id of the hand to receive the new card
    :param card:       String of the card to add to the collection.
    :return:           None.
    """
    # Build the initial query
    player = utils.query_player(player_id=player_id)

    # Did we find a player?
    if player is None:
        abort(404, "Player is invalid.")

    hand_id = str(player.hand_id)

    # Card is a dict.
    s_card = card["card"]

    return hand.addcard(hand_id, s_card)


def deletecard(player_id: str, card: str):
    """
    This function responds to internal (non-API) database access requests
    by deleting the specified card from the given hand_id.

    :param player_id:  Id of the hand to receive the new card
    :param card:       String of the card to delete to the collection.
    :return:           None.
    """
    # Build the initial query
    player = utils.query_player(player_id=player_id)

    # Did we find a player?
    if player is None or player.hand_id is None and card is None:
        return

    hand_id = str(player.hand_id)

    # Delete the card from the selected hand in the database.
    return hand.deletecard(hand_id, card)


def update(player_id: str, data: dict):
    """
    This function updates an existing player in the player structure

    :param player_id:   Id of the player to update
    :param data:        Dictionary containing the data to update.
    :return:            Updated record.
    """
    return _update_data(player_id, data)


def _update_data(player_id: str, data: dict):
    """
    This function updates an existing player in the player structure

    :param player_id:   Id of the player to update in the player structure
    :param data:        Dictionary containing the data to update.
    :return:            Updated record.
    """
    # Get the player requested from the db into session
    update_player = utils.query_player(player_id=player_id)

    # Did we find an existing player?
    if update_player is None or update_player == {}:
        # Otherwise, nope, didn't find that player
        abort(404, f"Player not found for Id: {player_id}")

    # turn the passed in round into a db object
    db_session = db.session()
    local_object = db_session.merge(update_player)

    # Update any key present in a_round that isn't round_id or round_seq.
    for key in [x for x in data if x not in ["player_id"]]:
        setattr(local_object, key, data[key])

    # Add the updated data to the transaction.
    db_session.add(local_object)
    db_session.commit()

    # return updated player in the response
    schema = PlayerSchema()
    data = schema.dump(update_player)

    return data, 200


def delete(player_id: str):
    """
    This function deletes a player from the player structure

    :param player_id:   Id of the player to delete
    :return:            200 on successful delete, 404 if not found
    """
    # Get the player requested
    player = utils.query_player(player_id=player_id)

    # Did we find a player?
    if player is not None:
        db_session = db.session()
        local_object = db_session.merge(player)
        db_session.delete(local_object)
        db_session.commit()
        return make_response(f"Player {player_id} deleted", 200)

    # Otherwise, nope, didn't find that player
    abort(404, f"Player not found for Id: {player_id}")
