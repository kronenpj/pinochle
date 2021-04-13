"""
Tests for the various round classes.

License: GPLv3
"""
import json
import uuid
from random import choice

import pytest
from pinochle import hand, round_, roundteams
from pinochle.models.core import db

# pragma: pylint: disable=wrong-import-order
from werkzeug import exceptions

from . import test_utils

# from pinochle.models.utils import dump_db


def test_roundteam_readall(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/{team_id}' page is requested (GET)
    THEN check that the response contains the expected information
    """
    # Clear out ALL previous test data.
    db.drop_all()
    db.create_all()

    # Create a new game
    game_id = test_utils.create_game(4)

    # Create a new round
    round_id = test_utils.create_round(game_id)

    # Create a new teams
    team_ids = []
    for __ in range(2):
        team_id = test_utils.create_team(choice(test_utils.TEAM_NAMES))
        team_ids.append(team_id)

    # Create the roundteam association for the teams.
    roundteams.create(round_id=round_id, teams=team_ids)

    # Verify the association was created in the database.
    db_response = roundteams.read(round_id=round_id, team_id=team_id)
    assert db_response is not None

    with app.test_client() as test_client:
        # Attempt to access the readall roundteam api
        response = test_client.get(f"/api/round/{round_id}/{team_id}")
        assert response.status == "200 OK"

    # Verify the database agrees.
    db_response = roundteams.read_all()
    team_hand = None
    assert db_response is not None
    for item in db_response:
        assert round_id == item["round_id"]
        assert item["team_id"] in team_ids
        if team_hand is None:
            team_hand = item["hand_id"]
        else:
            assert team_hand != item["hand_id"]


def test_roundteam_addcard(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/{team_id}' page is requested (PUT)
    THEN check that the response contains the expected information
    """
    # Create a new game
    game_id = test_utils.create_game(4)

    # Create a new round
    round_id = test_utils.create_round(game_id)

    # Create a new teams
    team_ids = []
    for __ in range(2):
        team_id = test_utils.create_team(choice(test_utils.TEAM_NAMES))
        team_ids.append(team_id)

    # Create the roundteam association for the teams.
    roundteams.create(round_id=round_id, teams=team_ids)

    # Choose a team to receive the new card
    team_id = choice(team_ids)

    with app.test_client() as test_client:
        # Attempt to access the addcard roundteam api
        put_data = {}

        response = test_client.put(
            f"/api/round/{round_id}/{team_id}?card={choice(test_utils.CARD_LIST)}",
            data=json.dumps(put_data),
            content_type="application/json",
        )
        assert response.status == "201 CREATED"
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        assert response_str is not None
        response_data = json.loads(response_str)
        hand_id = response_data.get("hand_id")
        assert hand_id != ""
        assert test_utils.UUID_REGEX.match(hand_id)

    # Verify the database agrees.
    db_response = roundteams.read(round_id, team_id)
    assert db_response is not None
    assert round_id == db_response.get("round_id")
    assert hand_id == str(db_response.get("team_cards")[0].hand_id)


def test_roundteam_delcard(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/{team_id}/{card}' page is requested (DELETE)
    THEN check that the response contains the expected information
    """
    # Create a new game
    game_id = test_utils.create_game(4)
    print(f"game_id={game_id}")

    # Create a new round
    round_id = test_utils.create_round(game_id)
    print(f"round_id={round_id}")

    # Create a new teams
    team_ids = []
    for __ in range(2):
        team_id = test_utils.create_team(choice(test_utils.TEAM_NAMES))
        team_ids.append(team_id)

    # Create the roundteam association for the teams.
    roundteams.create(round_id=round_id, teams=team_ids)

    # Choose a team to receive the new card
    team_id = choice(team_ids)

    # Add a card to the team's collection.
    chosen_card = choice(test_utils.CARD_LIST)
    roundteams.addcard(round_id, team_id, chosen_card)

    with app.test_client() as test_client:
        # Attempt to access the deletecard roundteam api
        response = test_client.delete(f"/api/round/{round_id}/{team_id}/{chosen_card}")
        assert response.status == "200 OK"

    hand_id = test_utils.query_team_hand_id(round_id=round_id, team_id=team_id)
    # Verify the database agrees.
    db_response = hand.read_one(hand_id)
    assert db_response is None


def test_roundteam_delete(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/{team_id}' page is requested (DELETE)
    THEN check that the response contains the expected information
    """
    # Create a new game
    game_id = test_utils.create_game(4)
    print(f"game_id={game_id}")

    # Create a new round
    round_id = test_utils.create_round(game_id)
    print(f"round_id={round_id}")

    # Create a new teams
    team_ids = []
    for __ in range(2):
        team_id = test_utils.create_team(choice(test_utils.TEAM_NAMES))
        team_ids.append(team_id)

    # Create the roundteam association for the teams.
    roundteams.create(round_id=round_id, teams=team_ids)

    # Verify the association was created in the database.
    db_response = roundteams.read(round_id=round_id, team_id=team_id)
    assert db_response is not None

    with app.test_client() as test_client:
        # Attempt to access the delete roundteam api
        response = test_client.delete(f"/api/round/{round_id}/{team_id}")
        assert response.status == "200 OK"

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        db_response = roundteams.read(round_id, team_id)
        assert db_response is not None


def test_roundteam_readall_empty(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/{team_id}' page is requested (GET)
    THEN check that the response contains the expected information
    """
    # Clear out ALL previous test data.
    db.drop_all()
    db.create_all()

    # Create a new round
    round_id = str(uuid.uuid4())

    # Create a new teams
    team_id = str(uuid.uuid4())

    # Create the roundteam association for the teams.
    with pytest.raises(exceptions.Conflict):
        roundteams.create(round_id=round_id, teams=[team_id])

    # Verify the association was created in the database.
    with pytest.raises(exceptions.NotFound):
        roundteams.read(round_id=round_id, team_id=team_id)

    with app.test_client() as test_client:
        # Attempt to access the readall roundteam api
        test_client.get(f"/api/round/{round_id}/{team_id}")

    # Verify the database agrees.
    db_response = roundteams.read_all()
    assert db_response == []


def test_roundteam_addcard_missing(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/{team_id}' page is requested (PUT)
    THEN check that the response contains the expected information
    """
    # Create a new round
    round_id = str(uuid.uuid4())

    # Create a new team
    team_id = str(uuid.uuid4())

    # Create the roundteam association for the teams.
    with pytest.raises(exceptions.Conflict):
        roundteams.create(round_id=round_id, teams=[team_id])

    with app.test_client() as test_client:
        # Attempt to access the addcard roundteam api
        put_data = {}

        response = test_client.put(
            f"/api/round/{round_id}/{team_id}?card={choice(test_utils.CARD_LIST)}",
            data=json.dumps(put_data),
            content_type="application/json",
        )
        assert response.status == "404 NOT FOUND"
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        assert response_str is not None
        response_data = json.loads(response_str)
        hand_id = response_data.get("hand_id")
        assert hand_id is None

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        round_.read_one(round_id)


def test_roundteam_delcard_missing(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/{team_id}/{card}' page is requested (DELETE)
    THEN check that the response contains the expected information
    """
    # Create a new round
    round_id = str(uuid.uuid4())

    # Create a new teams
    team_id = str(uuid.uuid4())

    # Create the roundteam association for the teams.
    with pytest.raises(exceptions.Conflict):
        roundteams.create(round_id=round_id, teams=[team_id])

    # Add a card to the team's collection.
    chosen_card = choice(test_utils.CARD_LIST)
    with pytest.raises(exceptions.NotFound):
        roundteams.addcard(round_id, team_id, {"card": chosen_card})

    with app.test_client() as test_client:
        # Attempt to access the deletecard roundteam api
        response = test_client.delete(f"/api/round/{round_id}/{team_id}/{chosen_card}")
        assert response.status == "404 NOT FOUND"

    hand_id = test_utils.query_team_hand_id(round_id=round_id, team_id=team_id)
    # Verify the database agrees.
    db_response = hand.read_one(hand_id)
    assert db_response is None


def test_roundteam_delete_missing(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/{team_id}' page is requested (DELETE)
    THEN check that the response contains the expected information
    """
    # Create a new round
    round_id = uuid.uuid4()

    # Create a new teams
    team_id = uuid.uuid4()

    # Create the roundteam association for the teams.
    with pytest.raises(exceptions.Conflict):
        roundteams.create(round_id=round_id, teams=[team_id])

    # Verify the association was created in the database.
    with pytest.raises(exceptions.NotFound):
        roundteams.read(round_id=round_id, team_id=team_id)

    with app.test_client() as test_client:
        # Attempt to access the delete roundteam api
        response = test_client.delete(f"/api/round/{round_id}/{team_id}")
        assert response.status == "404 NOT FOUND"

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        db_response = roundteams.read(round_id, team_id)
        assert db_response is not None
