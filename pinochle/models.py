import os
import uuid
from datetime import datetime

import connexion
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import CHAR, TypeDecorator

from pinochle.config import db, ma

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    From: https://docs.sqlalchemy.org/en/14/core/custom_types.html#backend-agnostic-guid-type
    """

    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


class Game(db.Model):
    __tablename__ = "game"
    _id = db.Column(db.Integer, primary_key=True)
    # NOTE: Without lambda: the uuid.uuid4() function is invoked once, upon class instantiation.
    game_id = db.Column(GUID, default=lambda: uuid.uuid4())
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class GameSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = Game
        sqla_session = db.session

    _id = fields.Int()
    game_id = fields.Str()
    timestamp = fields.DateTime()


class Hand(db.Model):
    __tablename__ = "hand"
    _id = db.Column(db.Integer, primary_key=True)
    hand_id = db.Column(GUID, default=lambda: uuid.uuid4())
    hand_seq = db.Column(db.Integer, autoincrement=True)
    bid = db.Column(db.Integer, default=20, nullable=False)
    bid_winner = db.Column(GUID, db.ForeignKey("player.player_id"))

    # This is a serialized list.
    # content = db.Column(db.String, nullable=False)

    trump = db.Column(db.String, default="")
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class HandSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = Hand
        sqla_session = db.session

    _id = fields.Int()
    # hand_id = fields.UUID()
    hand_id = fields.Str()
    hand_seq = fields.Int()
    bid = fields.Int()
    # bid_winner = fields.UUID()
    bid_winner = fields.Str()
    trump = fields.Str()
    timestamp = fields.DateTime()


class HandTeam(db.Model):
    __tablename__ = "hand_team"
    _id = db.Column(db.Integer, primary_key=True)
    hand_id = db.Column(GUID, db.ForeignKey("hand.hand_id"))
    team_id = db.Column(GUID, db.ForeignKey("team.team_id"))
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class HandTeamSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = HandTeam
        sqla_session = db.session

    _id = fields.Int()
    hand_id = fields.Str()
    team_id = fields.Str()
    timestamp = fields.DateTime()


class Team(db.Model):
    __tablename__ = "team"
    _id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(GUID, default=lambda: uuid.uuid4())
    name = db.Column(db.String(32))

    # These are serialized list.
    # hands = db.Column(db.String)
    # players = db.Column(db.String)

    score = db.Column(db.Integer, default=0)
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class TeamSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = Team
        sqla_session = db.session

    _id = fields.Int()
    team_id = fields.Str()
    name = fields.Str()
    score = fields.Int()
    timestamp = fields.DateTime()


class TeamPlayers(db.Model):
    __tablename__ = "team_players"
    _id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(GUID, db.ForeignKey("team.team_id"))
    player_id = db.Column(GUID, db.ForeignKey("player.player_id"))
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class TeamPlayersSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = TeamPlayers
        sqla_session = db.session

    _id = fields.Int()
    team_id = fields.Str()
    player_id = fields.Str()
    timestamp = fields.DateTime()


class Player(db.Model):
    __tablename__ = "player"
    _id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(GUID, default=lambda: uuid.uuid4())
    name = db.Column(db.String(32))
    hand = db.Column(db.String(32))
    score = db.Column(db.Integer, default=0)
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class PlayerSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = Player
        sqla_session = db.session

    _id = fields.Int()
    name = fields.Str()
    player_id = fields.UUID()
    hand = fields.Str()
    score = fields.Int()
    timestamp = fields.DateTime()
