"""
Tests for the various round classes.

License: GPLv3
"""
import json
import uuid
from random import choice

import pytest
from pinochle import gameround, play_pinochle, round_, roundteams, teamplayers
from pinochle.cards.const import SUITS
from pinochle.models import utils
from pinochle.models.core import db

# pylint: disable=wrong-import-order
from werkzeug import exceptions

import test_utils

# from pinochle.models.utils import dump_db


def test_game_round_start(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/start' page is requested (POST)
    THEN check that the response is successful
    """
    # Create a new game
    game_id = str(test_utils.create_game(4))

    # Create a new round
    round_id = str(test_utils.create_round(game_id))

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    assert db_response is not None

    db_response = gameround.read_one(game_id, round_id)
    assert db_response is not None

    # Create players
    player_ids = []
    for player_name in test_utils.PLAYER_NAMES:
        player_id = test_utils.create_player(player_name)
        assert test_utils.UUID_REGEX.match(player_id)
        player_ids.append(player_id)

    # Create a new teams
    team_ids = []
    for item in range(2):
        team_id = test_utils.create_team(choice(test_utils.TEAM_NAMES))
        team_ids.append(team_id)
        teamplayers.create(team_id=team_id, player_id={"player_id": player_ids[item]})
        teamplayers.create(
            team_id=team_id, player_id={"player_id": player_ids[item + 2]}
        )

    # Create the roundteam association for the teams.
    roundteams.create(round_id=round_id, teams=team_ids)

    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.post(f"/api/round/{round_id}/start")
        assert response.status == "200 OK"
        response_str = response.get_data(as_text=True)
        assert "started" in response_str

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    # print(f"db_response={db_response}")

    db_response = gameround.read_one(game_id, round_id)
    # print(f"db_response={db_response}")


def test_round_score_meld_hand_no_trump(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/score_hand_meld' page is requested (POST)
    THEN check that the response is successful
    """
    # Create a new game
    game_id = str(test_utils.create_game(4))

    # Create a new round
    round_id = str(test_utils.create_round(game_id))

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    assert db_response is not None

    db_response = gameround.read_one(game_id, round_id)
    assert db_response is not None

    # Create players
    player_ids = []
    for player_name in test_utils.PLAYER_NAMES:
        player_id = test_utils.create_player(player_name)
        assert test_utils.UUID_REGEX.match(player_id)
        player_ids.append(player_id)

    # Create a new teams
    team_ids = []
    for item in range(2):
        team_id = test_utils.create_team(choice(test_utils.TEAM_NAMES))
        team_ids.append(team_id)
        teamplayers.create(team_id=team_id, player_id={"player_id": player_ids[item]})
        teamplayers.create(
            team_id=team_id, player_id={"player_id": player_ids[item + 2]}
        )

    # Create the roundteam association for the teams.
    roundteams.create(round_id=round_id, teams=team_ids)

    round_.start(round_id=round_id)
    player_id = choice(player_ids)
    hand_id = test_utils.query_player_hand_id(player_id=player_id)
    temp_cards = []
    for item in utils.query_hand_list(hand_id):
        temp_cards.append(item.card)

    print(f"round_id={round_id}, player_id={player_id}")
    print(f"player_cards={temp_cards}")
    print(f"temp_cards= {','.join(temp_cards)}")
    cards_str = ",".join(temp_cards)
    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.get(
            f"/api/round/{round_id}/score_meld?player_id={player_id}&cards={cards_str}"
        )
        assert response.status == "200 OK"
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        score = response_data.get("score")
        assert "score" in response_str
        assert isinstance(score, int)
        print(f"score={score}")

    # Verify database agrees.
    updated_player = utils.query_player(player_id=player_id)
    print(f"updated_player={updated_player}")
    assert updated_player.meld_score == score


def test_round_score_meld_hand_with_trump(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/score_hand_meld' page is requested (POST)
    THEN check that the response is successful
    """
    # Create a new game
    game_id = str(test_utils.create_game(4))

    # Create a new round
    round_id = str(test_utils.create_round(game_id))

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    assert db_response is not None

    db_response = gameround.read_one(game_id, round_id)
    assert db_response is not None

    # Create players
    player_ids = []
    for player_name in test_utils.PLAYER_NAMES:
        player_id = test_utils.create_player(player_name)
        assert test_utils.UUID_REGEX.match(player_id)
        player_ids.append(player_id)

    # Create a new teams
    team_ids = []
    for item in range(2):
        team_id = test_utils.create_team(choice(test_utils.TEAM_NAMES))
        team_ids.append(team_id)
        teamplayers.create(team_id=team_id, player_id={"player_id": player_ids[item]})
        teamplayers.create(
            team_id=team_id, player_id={"player_id": player_ids[item + 2]}
        )

    # Create the roundteam association for the teams.
    roundteams.create(round_id=round_id, teams=team_ids)

    round_.start(round_id=round_id)
    player_id = choice(player_ids)
    round_.update(round_id, {"bid_winner": player_id})
    hand_id = test_utils.query_player_hand_id(player_id=player_id)
    temp_cards = []
    for item in utils.query_hand_list(hand_id):
        temp_cards.append(item.card)

    print(f"round_id={round_id}, player_id={player_id}")
    print(f"player_cards={temp_cards}")
    print(f"temp_cards= {','.join(temp_cards)}")
    cards_str = ",".join(temp_cards)
    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.get(
            f"/api/round/{round_id}/score_meld?player_id={player_id}&cards={cards_str}"
        )
        assert response.status == "200 OK"
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        score = response_data.get("score")
        assert "score" in response_str
        assert isinstance(score, int)
        print(f"score={score}")

    trump = choice(SUITS)
    play_pinochle.set_trump(round_id, player_id, trump)

    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.get(
            f"/api/round/{round_id}/score_meld?player_id={player_id}&cards={cards_str}"
        )
        assert response.status == "200 OK"
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        t_score = response_data.get("score")
        assert "score" in response_str
        assert isinstance(t_score, int)
        assert t_score >= score
        print(f"t_score={t_score}")


def test_game_round_start_no_teams(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/start' page is requested (POST)
    THEN check that the response is successful
    """
    # Create a new game
    game_id = str(test_utils.create_game(4))

    # Create a new round
    round_id = str(test_utils.create_round(game_id))

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    assert db_response is not None

    db_response = gameround.read_one(game_id, round_id)
    assert db_response is not None

    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.post(f"/api/round/{round_id}/start")
        assert response.status == "409 CONFLICT"
        # response_str = response.get_data(as_text=True)
        # assert f"Round {round_id} not found." in response_str


def test_game_round_start_invalid(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/start' page is requested (POST)
    THEN check that the response is successful
    """
    # Create a new, invalidround
    round_id = str(uuid.uuid4())

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        round_.read_one(round_id)
        # print(f"db_response={db_response}")
    # assert db_response is not None

    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.post(f"/api/round/{round_id}/start")
        assert response.status == "404 NOT FOUND"
        response_str = response.get_data(as_text=True)
        assert f"Round {round_id} not found." in response_str


def test_round_create(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round' page is requested (POST)
    THEN check that the response is a UUID and contains the expected information
    """
    # Create a new game
    game_id = test_utils.create_game(4)

    with app.test_client() as test_client:
        # Attempt to access the create round api
        response = test_client.post(f"/api/game/{game_id}/round")
        assert response.status == "201 CREATED"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        round_id = response_data.get("round_id")
        assert round_id != ""
        assert test_utils.UUID_REGEX.match(round_id)

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    assert db_response is not None
    assert round_id == db_response.get("round_id")
    assert db_response.get("trump") == "NONE"
    assert db_response.get("bid_winner") is None
    assert isinstance(db_response.get("round_seq"), int)
    assert db_response.get("bid") == 20


def test_game_round_delete(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}/{round_id}' page is requested (DELETE)
    THEN check that the response is successful
    """
    # Create a new game
    game_id = test_utils.create_game(4)

    # Create a new round
    round_id = test_utils.create_round(game_id)

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    assert db_response is not None

    db_response = gameround.read_one(game_id, round_id)
    assert db_response is not None

    with app.test_client() as test_client:
        # Attempt to access the delete round api
        response = test_client.delete(f"/api/game/{game_id}/{round_id}")
        assert response.status == "200 OK"

        # Attempt to retrieve the now-deleted round id
        response = test_client.get(f"/api/game/{game_id}/{round_id}")
        assert "404 NOT FOUND" in response.status

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        db_response = round_.read_one(round_id)
    with pytest.raises(exceptions.NotFound):
        db_response = gameround.read_one(game_id, round_id)


def test_game_round_list(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}/round' page is requested (GET)
    THEN check that the response is successful
    """
    # Create a new game
    game_id = str(test_utils.create_game(4))

    # Create a new round
    round_id = test_utils.create_round(game_id)

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    assert db_response is not None

    db_response = gameround.read_one(game_id, round_id)
    assert db_response is not None

    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.get(f"/api/game/{game_id}/round")
        assert response.status == "200 OK"
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        # print(f"response_data={response_data}")

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    # print(f"db_response={db_response}")

    db_response = gameround.read_one(game_id, round_id)
    # print(f"db_response={db_response}")
    assert response_data == db_response


def test_round_read_all(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round' page is requested (GET)
    THEN check that the response is a list of UUID and contains the expected information
    """
    create_games = 2

    # Clear out ALL previous test data.
    db.drop_all()
    db.create_all()

    game_ids = []
    round_ids = []
    for __ in range(create_games):
        # Create a new game
        game_id = test_utils.create_game(4)
        game_ids.append(game_id)

        for __ in range(create_games):
            # Create a new round
            round_id = test_utils.create_round(game_id)
            round_ids.append(round_id)
    assert len(game_ids) == create_games
    assert len(round_ids) == create_games * 2

    with app.test_client() as test_client:
        # Attempt to access the GET game api
        response = test_client.get("/api/round")
        assert response.status == "200 OK"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        r_round_id = response_data  # List of dicts
        assert len(r_round_id) >= create_games
        for item in r_round_id:
            assert item["round_id"] != ""
            assert item["round_id"] in round_ids
            assert test_utils.UUID_REGEX.match(item.get("round_id"))

    # Verify the database agrees.
    db_response = round_.read_all()  # List of dicts
    assert db_response is not None
    for item in db_response:
        assert item["round_id"] in round_ids


def test_round_read_one(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}' page is requested (GET)
    THEN check that the response is a UUID and contains the expected information
    """
    # Create a new game
    game_id = test_utils.create_game(4)

    # Create a new round
    round_id = test_utils.create_round(game_id)

    with app.test_client() as test_client:
        # Attempt to access the create round api
        response = test_client.get(f"/api/round/{round_id}")
        assert response.status == "200 OK"
        assert response.get_data(as_text=True) is not None
        # This is a JSON formatted STRING
        response_str = response.get_data(as_text=True)
        response_data = json.loads(response_str)
        r_round_id = response_data.get("round_id")
        assert r_round_id != ""
        assert r_round_id == round_id
        assert test_utils.UUID_REGEX.match(r_round_id)

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    assert db_response is not None
    assert round_id == db_response.get("round_id")


def test_game_round_delete_missing(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}/{round_id}' page is requested (DELETE)
    THEN check that the response is successful
    """
    # Create a new game
    game_id = str(uuid.uuid4())

    # Create a new round
    round_id = str(uuid.uuid4())

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        round_.read_one(round_id)

    with pytest.raises(exceptions.NotFound):
        gameround.read_one(game_id, round_id)

    with app.test_client() as test_client:
        # Attempt to access the delete round api
        response = test_client.delete(f"/api/game/{game_id}/{round_id}")
        assert response.status == "404 NOT FOUND"

        # Attempt to retrieve the now-deleted round id
        response = test_client.get(f"/api/game/{game_id}/{round_id}")
        assert "404 NOT FOUND" in response.status

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        round_.read_one(round_id)

    with pytest.raises(exceptions.NotFound):
        gameround.read_one(game_id, round_id)


def test_round_read_all_empty(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round' page is requested (GET)
    THEN check that the response is a list of UUID and contains the expected information
    """
    # Clear out ALL previous test data.
    db.drop_all()
    db.create_all()

    with app.test_client() as test_client:
        # Attempt to access the GET game api
        response = test_client.get("/api/round")
        assert response.status == "404 NOT FOUND"

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        round_.read_all()  # List of dicts


def test_round_read_one_missing(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}' page is requested (GET)
    THEN check that the response is a UUID and contains the expected information
    """
    # Create a new round
    round_id = uuid.uuid4()

    with app.test_client() as test_client:
        # Attempt to access the create round api
        response = test_client.get(f"/api/round/{round_id}")
        assert response.status == "404 NOT FOUND"

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        round_.read_one(round_id)


def test_game_round_delete_missing2(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}/{round_id}' page is requested (DELETE)
    THEN check that the response is successful
    """
    # Create a new game
    game_id = str(uuid.uuid4())

    # Create a new round
    round_id = str(uuid.uuid4())

    # Verify the database agrees.
    with pytest.raises(exceptions.NotFound):
        gameround.delete(game_id, round_id)


def test_game_round_create_invalid(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/game/{game_id}/{round_id}' page is requested (POST)
    THEN check that the response is successful
    """
    # Create a new game
    game_id = str(uuid.uuid4())

    with pytest.raises(exceptions.Conflict):
        gameround.create(game_id, {"round_id": game_id})

    game_id = test_utils.create_game(4)

    # Create a new round
    round_id = str(uuid.uuid4())

    with pytest.raises(exceptions.Conflict):
        gameround.create(game_id, {"round_id": round_id})

    round_id = test_utils.create_round(game_id)

    with pytest.raises(exceptions.Conflict):
        gameround.create(game_id, {"round_id": round_id})


def test_round_score_meld_bad_hand(app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/round/{round_id}/score_hand_meld' page is requested (POST)
    THEN check that the response is successful
    """
    # Create a new game
    game_id = str(test_utils.create_game(4))

    # Create a new round
    round_id = str(test_utils.create_round(game_id))

    # Verify the database agrees.
    db_response = round_.read_one(round_id)
    assert db_response is not None

    db_response = gameround.read_one(game_id, round_id)
    assert db_response is not None

    # Create players
    player_ids = []
    for player_name in test_utils.PLAYER_NAMES:
        player_id = test_utils.create_player(player_name)
        assert test_utils.UUID_REGEX.match(player_id)
        player_ids.append(player_id)

    # Create a new teams
    team_ids = []
    for item in range(2):
        team_id = test_utils.create_team(choice(test_utils.TEAM_NAMES))
        team_ids.append(team_id)
        teamplayers.create(team_id=team_id, player_id={"player_id": player_ids[item]})
        teamplayers.create(
            team_id=team_id, player_id={"player_id": player_ids[item + 2]}
        )

    # Create the roundteam association for the teams.
    roundteams.create(round_id=round_id, teams=team_ids)

    round_.start(round_id=round_id)
    player_id = choice(player_ids)
    # Choose another player so that the cards don't match exactly.
    temp_player_id = choice([x for x in player_ids if x != player_id])
    hand_id = test_utils.query_player_hand_id(player_id=temp_player_id)
    temp_cards = []
    for item in utils.query_hand_list(hand_id):
        temp_cards.append(item.card)

    print(f"round_id={round_id}, player_id={player_id}")
    print(f"player_cards={temp_cards}")
    print(f"temp_cards= {','.join(temp_cards)}")
    cards_str = ",".join(temp_cards)
    with app.test_client() as test_client:
        # Attempt to access the get round api
        response = test_client.get(
            f"/api/round/{round_id}/score_meld?player_id={player_id}&cards={cards_str}"
        )
        assert response.status == "409 CONFLICT"
