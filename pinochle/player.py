"""
This is the player module and supports all the REST actions for the
player data
"""

import sqlalchemy
from flask import abort, make_response

from pinochle.config import db
from pinochle.models import Player, PlayerSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to a request for /api/player
    with the complete lists of players

    :return:        json string of list of players
    """
    try:
        # Create the list of player from our data
        players = Player.query.order_by(Player.name).all()
    except sqlalchemy.exc.NoForeignKeysError:
        # Otherwise, nope, didn't find any players
        abort(404, "No Players defined in database")

    # Serialize the data for the response
    player_schema = PlayerSchema(many=True)
    data = player_schema.dump(players).data
    return data


def read_one(player_id):
    """
    This function responds to a request for /api/player/{player_id}
    with one matching player from player

    :param player_id:   Id of player to find
    :return:            player matching id
    """
    # Build the initial query
    player = (
        Player.query.filter(Player.player_id == player_id)
        # .outerjoin(Hand)
        .one_or_none()
    )

    # Did we find a player?
    if player is not None:
        # Serialize the data for the response
        player_schema = PlayerSchema()
        data = player_schema.dump(player).data
        return data

    # Otherwise, nope, didn't find that player
    else:
        abort(404, f"Player not found for Id: {player_id}")


def create(player):
    """
    This function creates a new player in the player structure
    based on the passed in player data

    :param player:  player to create in player structure
    :return:        201 on success, 406 on player exists
    """
    name = player.get("name")

    existing_player = Player.query.filter(Player.name == name).one_or_none()

    # Can we insert this player?
    if existing_player is None:

        # Create a player instance using the schema and the passed in player
        schema = PlayerSchema()
        new_player = schema.load(player, session=db.session).data
        # new_player = schema.load(player).data

        # Add the player to the database
        db.session.add(new_player)
        db.session.commit()

        # Serialize and return the newly created player in the response
        data = schema.dump(new_player).data

        return data, 201

    # Otherwise, nope, player exists already
    else:
        abort(409, f"Player {name} exists already")


def update(player_id, player):
    """
    This function updates an existing player in the player structure

    :param player_id:   Id of the player to update in the player structure
    :param player:      player to update
    :return:            updated player structure
    """
    # Get the player requested from the db into session
    update_player = Player.query.filter(Player.player_id == player_id).one_or_none()

    # Did we find an existing player?
    if update_player is not None:

        # turn the passed in player into a db object
        schema = PlayerSchema()
        update = schema.load(player, session=db.session).data

        # Set the id to the player we want to update
        update.player_id = update_player.player_id

        # merge the new object into the old and commit it to the db
        db.session.merge(update)
        db.session.commit()

        # return updated player in the response
        data = schema.dump(update_player).data

        return data, 200

    # Otherwise, nope, didn't find that player
    else:
        abort(404, f"Player not found for Id: {player_id}")


def delete(player_id):
    """
    This function deletes a player from the player structure

    :param player_id:   Id of the player to delete
    :return:            200 on successful delete, 404 if not found
    """
    # Get the player requested
    player = Player.query.filter(Player.player_id == player_id).one_or_none()

    # Did we find a player?
    if player is not None:
        db.session.delete(player)
        db.session.commit()
        return make_response(f"Player {player_id} deleted", 200)

    # Otherwise, nope, didn't find that player
    else:
        abort(404, f"Player not found for Id: {player_id}")
