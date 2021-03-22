"""
This is the round module and supports all the REST actions for the
round data
"""

from flask import abort, make_response

from pinochle import gameround, play_pinochle
from pinochle.models import utils
from pinochle.models.core import db
from pinochle.models.round_ import RoundSchema

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to a request for /api/round
    with the complete lists of rounds

    :return:        json string of list of rounds
    """
    # Create the list of round from our data
    rounds = utils.query_round_list()

    if len(rounds) == 0:
        # Otherwise, nope, didn't find any players
        abort(404, "No Rounds defined in database")

    # Serialize the data for the response
    round_schema = RoundSchema(many=True)
    data = round_schema.dump(rounds)
    return data


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
    if a_round is not None:
        # Serialize the data for the response
        round_schema = RoundSchema()
        data = round_schema.dump(a_round)
        return data

    # Otherwise, nope, didn't find that round
    abort(404, f"Round not found for Id: {round_id}")


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
    if existing_game is not None:
        # Create a round instance using the schema and the passed in round
        schema = RoundSchema()
        new_round = schema.load({}, session=db.session)

        # Add the round to the database
        db.session.add(new_round)
        db.session.commit()

        # Serialize and return the newly created round in the response
        data = schema.dump(new_round)

        round_id = data["round_id"]

        # Also insert a record into the game_round table
        # print(f"game_id={game_id} round_id={round_id}")
        return gameround.create(game_id=game_id, round_id={"round_id": round_id})

    abort(400, f"Counld not create new round for game {game_id}.")


def update(round_id: str, a_round: dict):
    """
    This function updates an existing round in the round structure

    :param round_id:   Id of the round to update in the round structure
    :param round:      round to update
    :return:            updated round structure
    """
    # Get the round requested from the db into session
    update_round = utils.query_round(round_id)

    # Did we find an existing round?
    if update_round is not None:

        # turn the passed in round into a db object
        schema = RoundSchema()
        db_update = schema.load(a_round, session=db.session)

        # Set the id to the round we want to update
        db_update.round_id = update_round.round_id

        # merge the new object into the old and commit it to the db
        db.session.merge(db_update)
        db.session.commit()

        # return updated round in the response
        data = schema.dump(update_round)

        return data, 200

    # Otherwise, nope, didn't find that round
    abort(404, f"Round not found for Id: {round_id}")


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
    if g_round is not None:
        gameround.delete(game_id=game_id, round_id=round_id)

    # Did we find a round?
    if a_round is not None:
        db_session = db.session()
        local_object = db_session.merge(a_round)
        db_session.delete(local_object)
        db_session.commit()
        return make_response(f"Round {round_id} deleted", 200)

    # Otherwise, nope, didn't find that round
    abort(404, f"Round not found for Id: {round_id}")


def start(round_id: str):
    """
    This function starts a game round if all the requirements are satisfied.

    :param game_id:    Id of the game where round belongs
    :param round_id:   Id of the round to delete
    :return:           200 on successful delete, 404 if not found,
                       409 if requirements are not satisfied.
    """
    # print(f"\nround_id={round_id}")
    # Get the round requested
    a_round: dict = utils.query_round(round_id)

    # Did we find a round?
    if a_round is None or a_round == {}:
        abort(404, f"Round {round_id} not found.")

    # Retrieve the information for the round and teams.
    round_t: list = utils.query_roundteam_list(round_id)

    # Did we find one or more round-team entries?
    if round_t is None or round_t == {}:
        abort(409, f"No teams found for round {round_id}.")

    # Retrieve the hand_id for the kitty.
    kitty = str(a_round.hand_id)

    # Gather a list of teams and associate the team with the correct hand_id.
    teams = []
    team_hand_id = {}
    for _id in round_t:
        temp_team = str(_id.team_id)
        teams.append(temp_team)
        team_hand_id[temp_team] = str(_id.hand_id)

    # Collect the individual players.
    player_hand_id = {}
    for team_id in teams:
        team_temp: dict = utils.query_teamplayer_list(team_id)
        for team_info in team_temp:
            player_hand_id[str(team_info.player_id)] = ""

    # Associate the player with that player's hand.
    for player_id in player_hand_id:
        player_temp: dict = utils.query_player(player_id=player_id)
        player_hand_id[player_id] = str(player_temp.hand_id)

    # print(f"kitty={kitty}")
    # print(f"team_hand_id={team_hand_id}")
    # print(f"player_hand_id={player_hand_id}\n")

    assert len(list(player_hand_id.keys())) == 4
    # print(f"player_hand_ids: {list(player_hand_id.keys())}")
    # Time to deal the cards.
    play_pinochle.deal_pinochle(
        player_ids=list(player_hand_id.keys()), kitty_len=4, kitty_id=kitty
    )

    return make_response(f"Round {round_id} started.", 200)
