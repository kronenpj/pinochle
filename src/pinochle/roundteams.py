"""
This is the roundplayer module and supports all the REST actions roundplayer data
"""

import sqlalchemy
from flask import abort, make_response

from pinochle.models import utils
from pinochle.models.core import db
from pinochle.models.hand import Hand, HandSchema
from pinochle.models.round_ import Round
from pinochle.models.roundteam import RoundTeam, RoundTeamSchema
from pinochle.models.team import Team

# pylint: disable=unused-import
# from pinochle.models.utils import dump_db

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


def read_all():
    """
    This function responds to a request for /api/RoundTeam
    with the complete lists of game rounds

    :return:        json string of list of game rounds
    """
    # Create the list of round-teams from our data
    round_teams = RoundTeam.query.order_by(RoundTeam.timestamp).all()

    # Serialize the data for the response
    rt_schema = RoundTeamSchema(many=True)
    data = rt_schema.dump(round_teams)
    return data


def read_one(round_id: str):
    """
    This function responds to a request for /api/round/{round_id}/teams
    with one matching round from round

    :param round_id:    Id of round to find
    :return:            list of team IDs playing in the specified round
    """
    # Build the initial query
    a_round = RoundTeam.query.filter(RoundTeam.round_id == round_id).all()

    # Did we find a round?
    if a_round is not None:
        # Serialize the data for the response
        data = {"round_id": round_id}
        temp = list()
        for _, team in enumerate(a_round):
            temp.append(str(team.team_id))
        data["team_ids"] = temp
        return data, 200

    # Otherwise, nope, didn't find any rounds
    abort(404, f"No rounds found ID {round_id}")


def read(round_id: str, team_id: str):
    """
    This function responds to a request for /api/round/{round_id}/{team_id}
    with selected team in that round.

    :param round_id:   Id of round to find
    :param team_id:    Id of the team to report
    :return:           list of cards collected by that team for the round.
    """
    # Build the query
    try:
        team_hand_id = utils.query_roundteam(round_id=round_id, team_id=team_id)
        hand_id = str(team_hand_id.hand_id)

        # Retrieve the list of cards the team has collected.
        team_cards = utils.query_hand_list(hand_id=hand_id)

        # Did we find any cards?
        if team_cards is not None:
            # Serialize the data for the response
            data = {"round_id": round_id, "team_id": team_id}
            temp = list()
            for _, team_cards in enumerate(team_cards):
                temp.append(team_cards)
            data["team_cards"] = temp
            return data
    except sqlalchemy.orm.exc.NoResultFound:
        pass
    except sqlalchemy.exc.StatementError:
        pass
    except AttributeError:  # If hand_id is None
        pass

    # Otherwise, nope, didn't find any cards for this round/team
    abort(404, f"No cards found for {round_id}/{team_id}")


def addcard(round_id: str, team_id: str, card: dict):
    """
    This function responds to a PUT for /api/round/{round_id}/{team_id}
    by adding the specified card to the team's collection.

    :param round_id:   Id of round to find
    :param team_id:    Id of the team to report
    :param card:       String of the card to add to the collection.
    :return:           None.
    """
    if round_id is not None and team_id is not None and card is not None:
        # Build the query to extract the hand_id
        rt_data = utils.query_roundteam_with_hand(round_id=round_id, team_id=team_id)

        if rt_data is not None:
            hand_id = str(rt_data.hand_id)

            # Create a hand instance using the schema and the passed in card
            schema = HandSchema()
            new_card = schema.load(
                {"hand_id": hand_id, "card": card["card"]}, session=db.session
            )

            # Add the round to the database
            db.session.add(new_card)
            db.session.commit()

            # Serialize and return the newly created card in the response
            data = schema.dump(new_card)

            return data, 201

    # Otherwise, something happened.
    abort(404, f"Couldn't add {card} to collection for {round_id}/{team_id}")


def deletecard(round_id: str, team_id: str, card: str):
    """
    This function responds to a DELETE for /api/round/{round_id}/{team_id}
    by deleting the specified card to the team's collection.

    :param round_id:   Id of round to find
    :param team_id:    Id of the team to report
    :param card:       String of the card to add to the collection.
    :return:           None.
    """
    if round_id is not None and team_id is not None and card is not None:
        # Build the query to extract the hand_id
        rt_data = RoundTeam.query.filter(
            RoundTeam.round_id == round_id,
            RoundTeam.team_id == team_id,
            RoundTeam.hand_id is not None,
        ).one_or_none()

        if rt_data is not None:
            # Extract the properly formatted UUID.
            hand_id = str(rt_data.hand_id)

            # Locate the entry in Hand that corresponds to the hand_id and card
            rt_data = Hand.query.filter(
                Hand.hand_id == hand_id, Hand.card == card
            ).one_or_none()

            # Delete the card from the database
            db_session = db.session()
            local_object = db_session.merge(rt_data)
            db_session.delete(local_object)
            db_session.commit()

            return 200

    # Otherwise, something happened.
    abort(404, f"Couldn't delete {card} from collection for {round_id}/{team_id}")


def create(round_id: str, teams: list):
    """
    This function creates a new round in the round-team structure
    based on the passed in team data

    :param round_id:  round to add
    :param teams:     teams to associate with round
    :return:          201 on success, 406 on round doesn't exist
    """
    if round_id is None or teams is None:
        abort(409, "Invalid data provided.")

    # Teams should come as a list, loop over the values.
    for t_id in teams:
        existing_round = Round.query.filter(Round.round_id == round_id).one_or_none()
        existing_team = Team.query.filter(Team.team_id == t_id).one_or_none()
        team_on_round = RoundTeam.query.filter(
            RoundTeam.round_id == round_id, RoundTeam.team_id == t_id
        ).one_or_none()

        # Can we insert this round?
        if existing_round is None:
            abort(409, f"Round {round_id} doesn't already exist.")
        if existing_team is None:
            abort(409, f"Team {t_id} doesn't already exist.")
        if team_on_round is not None:
            abort(409, f"Team {t_id} is already associated with Round {round_id}.")

        # Create a round instance using the schema and the passed in round
        schema = RoundTeamSchema()
        new_roundteam = schema.load(
            {"round_id": round_id, "team_id": t_id}, session=db.session
        )

        # Add the round to the database
        db.session.add(new_roundteam)

    db.session.commit()

    # Serialize and return the newly created round in the response
    data = schema.dump(new_roundteam)
    # NOTE: This only returns the last team supplied, not the entire list.

    return data, 201


def update(round_id: str, teams: dict):
    """
    This function updates an existing round/team in the roundteam structure

    :param round_id:    Id of the round to update.
    :param teams:       Dictionary containing the data to update.
    :return:            Updated record.
    """
    return _update_data(round_id, teams)


def _update_data(round_id: str, data: dict):
    """
    This function updates an existing round/team in the roundteam structure

    :param round_id:    Id of the round to update.
    :param team_id:     Id of the team to update.
    :param data:        Dictionary containing the data to update.
    :return:            Updated record.
    """
    # Get the round requested from the db into session
    update_round = RoundTeam.query.filter(
        RoundTeam.round_id == round_id
    ).one_or_none()

    # Did we find an existing roundteam record?
    if update_round is not None or update_round == {}:
        # Otherwise, nope, didn't find one
        abort(404, f"Round Id {round_id} not found.")

    # turn the passed in game/round into a db object
    db_session = db.session()
    local_object = db_session.merge(update_round)

    # Update any key present in data that isn't round_id.
    for key in [x for x in data if x not in ["round_id"]]:
        setattr(local_object, key, data[key])

    # Add the updated data to the transaction.
    db_session.add(local_object)
    db_session.commit()

    # return updated round in the response
    schema = RoundTeamSchema()
    data = schema.dump(update_round)

    return data, 200


def delete(round_id: str, team_id: str):
    """
    This function deletes a round from the round structure

    :param round_id:    Id of the round to delete
    :param team_id:     Id of the team to delete
    :return:            200 on successful delete, 404 if not found
    """
    # Get the round requested
    a_round = RoundTeam.query.filter(
        RoundTeam.round_id == round_id, RoundTeam.team_id == team_id
    ).one_or_none()

    # Did we find a round?
    if a_round is not None:
        db_session = db.session()
        local_object = db_session.merge(a_round)
        db_session.delete(local_object)
        db_session.commit()
        return make_response(f"team {team_id} deleted from round {round_id}", 200)

    # Otherwise, nope, didn't find that round
    abort(404, f"Team {team_id} not found for round: {round_id}")
