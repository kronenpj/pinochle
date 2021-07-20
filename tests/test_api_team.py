"""
Tests for the various team classes.

License: GPLv3
"""
import json
import uuid
from random import choice

import pytest
from werkzeug import exceptions

from pinochle import team

from . import test_utils

# from pinochle.models.utils import dump_db


def test_team_create(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/team' page is requested (POST)
    THEN check that the response is a UUID and contains the expected information
    """
    with app.test_client() as test_client:
        # Create a new team
        team_name = choice(test_utils.TEAM_NAMES)

        # Attempt to access the create team api
        post_data = {
            "name": team_name,
        }
        response = test_client.post(
            "/api/team", data=json.dumps(post_data), content_type="application/json",
        )
        assert response.status == "201 CREATED"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        team_id = response_data.get("team_id")
        assert team_id != ""
        assert test_utils.UUID_REGEX.match(team_id)

        # Verify the database agrees.
        db_response = team.read_one(team_id)
        assert db_response is not None
        assert team_id == db_response.get("team_id")
        assert db_response.get("score") == 0
        # print(f"{db_response}")
        assert team_name == db_response.get("name")


def test_team_read_one(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/team/{team_id}' page is requested (GET)
    THEN check that the response is a UUID and contains the expected information
    """
    # Create a new team and player
    player_name = choice(test_utils.PLAYER_NAMES)
    team_name = choice(test_utils.TEAM_NAMES)

    # Create a new player
    player_id = test_utils.create_player(player_name)

    # Create a new team
    team_id = test_utils.create_team(team_name)

    # Join the player to the team.
    test_utils.create_teamplayer(team_id=team_id, player_id=player_id)

    with app.test_client() as test_client:
        # Attempt to access the create player api
        response = test_client.get(f"/api/team/{team_id}")
        assert response.status == "200 OK"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        team_id = response_data.get("team_id")
        assert team_id != ""
        assert test_utils.UUID_REGEX.match(team_id)

        # Verify the database agrees.
        db_response = team.read_one(team_id)
        assert db_response is not None
        assert team_id == db_response.get("team_id")
        assert db_response.get("score") == 0
        assert team_name == db_response.get("name")


def test_team_add_player(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/team/{team_id}' page is requested (POST)
    THEN check that the response is a UUID and contains the expected information
    """
    # Create a new team and player
    player_name = choice(test_utils.PLAYER_NAMES)
    team_name = choice(test_utils.TEAM_NAMES)

    # Create a new player
    player_id = test_utils.create_player(player_name)

    # Create a new team
    team_id = test_utils.create_team(team_name)

    with app.test_client() as test_client:
        # Attempt to access the create player api
        post_data = {
            "player_id": player_id,
        }
        response = test_client.post(
            f"/api/team/{team_id}",
            data=json.dumps(post_data),
            content_type="application/json",
        )
        assert response.status == "201 CREATED"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        team_id = response_data.get("team_id")
        assert team_id != ""
        assert test_utils.UUID_REGEX.match(team_id)

        # Verify the database agrees.
        db_response = team.read_one(team_id)
        assert db_response is not None
        assert team_id == db_response.get("team_id")
        assert db_response.get("score") == 0
        assert team_name == db_response.get("name")


def test_team_delete(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/team/{team_id}' page is requested (DELETE)
    THEN check that the response is successful
    """
    # Create a new player
    player_id = test_utils.create_player(choice(test_utils.PLAYER_NAMES))

    # Create a new team
    team_id = test_utils.create_team(choice(test_utils.TEAM_NAMES))

    # Create a new teamplayer
    test_utils.create_teamplayer(team_id, player_id)

    # Verify the database agrees.
    db_response = team.read_all()
    assert db_response is not None
    team_id_list = [response["team_id"] for response in db_response]
    assert team_id in team_id_list

    with app.test_client() as test_client:
        # Attempt to access the delete round api
        response = test_client.delete(f"/api/team/{team_id}")
        assert response.status == "200 OK"

        # Attempt to retrieve the now-deleted round id
        response = test_client.get(f"/api/team/{team_id}")
        assert response.status == "404 NOT FOUND"

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        team.read_one(team_id)


def test_team_add_player_missing(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/team' page is requested (POST)
    THEN check that the response is a UUID and contains the expected information
    """
    # Create a new player
    player_id = str(uuid.uuid4())

    # Create a new team
    team_id = str(uuid.uuid4())

    with app.test_client() as test_client:
        # Attempt to access the create player api
        post_data = {"player_id": player_id}
        response = test_client.post(
            f"/api/team/{team_id}",
            data=json.dumps(post_data),
            content_type="application/json",
        )
        assert response.status == "409 CONFLICT"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        team_id = response_data.get("team_id")
        assert team_id is None

        # Verify the database agrees.
        with pytest.raises(exceptions.NotFound):
            team.read_one(team_id)


def test_team_delete_missing(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/team/{team_id}' page is requested (DELETE)
    THEN check that the response is successful
    """
    # Create a new team
    team_id = str(uuid.uuid4())

    with app.test_client() as test_client:
        # Attempt to access the delete round api
        response = test_client.delete(f"/api/team/{team_id}")
        assert response.status == "404 NOT FOUND"

        # Attempt to retrieve the now-deleted round id
        response = test_client.get(f"/api/team/{team_id}")
        assert response.status == "404 NOT FOUND"

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        team.read_one(team_id)
