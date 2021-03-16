import uuid
from datetime import datetime

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

        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int

            # hexstring
            return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return value


class Game(db.Model):
    __tablename__ = "game"
    # NOTE: Without lambda: the uuid.uuid4() function is invoked once, upon class instantiation.
    game_id = db.Column(
        GUID,
        default=lambda: uuid.uuid4(),  # pragma pylint: disable=unnecessary-lambda
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
    )
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        output = "<Game %r" % self.game_id
        output += ">"
        return output


class GameSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = Game
        sqla_session = db.session

    # game_id = fields.UUID()
    game_id = fields.Str()
    timestamp = fields.DateTime()


class GameRound(db.Model):
    __tablename__ = "game_round"
    game_id = db.Column(
        GUID,
        db.ForeignKey("game.game_id"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    round_id = db.Column(
        GUID,
        db.ForeignKey("round.round_id"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        output = "<GameRound: "
        output += "Game %r, " % self.game_id
        output += "Round %r, " % self.round_id
        output += ">"
        return output


class GameRoundSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = GameRound
        sqla_session = db.session

    _id = fields.Int()
    # game_id = fields.UUID()
    game_id = fields.Str()
    # round_id = fields.UUID()
    round_id = fields.Str()
    timestamp = fields.DateTime()


class Round(db.Model):
    __tablename__ = "round"
    round_id = db.Column(
        GUID,
        default=lambda: uuid.uuid4(),  # pragma pylint: disable=unnecessary-lambda
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
    )
    round_seq = db.Column(db.Integer, default=0)
    hand_id = db.Column(
        GUID,
        default=lambda: uuid.uuid4(),  # pragma pylint: disable=unnecessary-lambda
        primary_key=False,
        nullable=True,
        index=False,
    )
    bid = db.Column(db.Integer, default=20, nullable=False)
    bid_winner = db.Column(GUID, db.ForeignKey("player.player_id"))
    trump = db.Column(db.String, default="NONE")
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        output = "<Round %r, " % self.round_id
        output += "Seq %r, " % self.round_seq
        output += "Bid %r, " % self.bid
        output += "Winner %r, " % self.bid_winner
        output += "Trump %r" % self.trump
        output += ">"
        return output


class RoundSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = Round
        sqla_session = db.session

    # round_id = fields.UUID()
    round_id = fields.Str()
    round_seq = fields.Int()
    # hand_id = fields.UUID()
    hand_id = fields.Str()
    bid = fields.Int()
    # bid_winner = fields.UUID()
    bid_winner = fields.Str()
    trump = fields.Str()
    timestamp = fields.DateTime()


class RoundTeam(db.Model):
    __tablename__ = "round_team"
    round_id = db.Column(
        GUID,
        db.ForeignKey("round.round_id"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    team_id = db.Column(
        GUID,
        db.ForeignKey("team.team_id"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    hand_id = db.Column(
        GUID,
        default=lambda: uuid.uuid4(),  # pragma pylint: disable=unnecessary-lambda
        primary_key=False,
        nullable=True,
        index=False,
    )
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        output = "<RoundTeam: "
        output += "Round %r, " % self.round_id
        output += "Team %r, " % self.team_id
        output += "Hand %r, " % self.hand_id
        output += ">"
        return output


class RoundTeamSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = RoundTeam
        sqla_session = db.session

    # round_id = fields.UUID()
    round_id = fields.Str()
    # team_id = fields.UUID()
    team_id = fields.Str()
    hand_id = fields.Str()
    timestamp = fields.DateTime()


class Team(db.Model):
    __tablename__ = "team"
    team_id = db.Column(
        GUID,
        default=lambda: uuid.uuid4(),  # pragma pylint: disable=unnecessary-lambda
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
    )
    name = db.Column(db.String)
    score = db.Column(db.Integer, default=0)
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        output = "<Team %r, " % self.team_id
        output += "Name %r, " % self.name
        output += "Score %r, " % self.score
        output += ">"
        return output


class TeamSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = Team
        sqla_session = db.session

    # team_id = fields.UUID()
    team_id = fields.Str()
    name = fields.Str()
    score = fields.Int()
    timestamp = fields.DateTime()


class TeamPlayers(db.Model):
    __tablename__ = "team_players"
    team_id = db.Column(
        GUID,
        db.ForeignKey("team.team_id"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    player_id = db.Column(
        GUID,
        db.ForeignKey("player.player_id"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        output = "<TeamPlayers: "
        output += "Team %r, " % self.team_id
        output += "Player %r, " % self.player_id
        output += ">"
        return output


class TeamPlayersSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = TeamPlayers
        sqla_session = db.session

    # team_id = fields.UUID()
    team_id = fields.Str()
    # player_id = fields.UUID()
    player_id = fields.Str()
    timestamp = fields.DateTime()


class Player(db.Model):
    __tablename__ = "player"
    player_id = db.Column(
        GUID,
        default=lambda: uuid.uuid4(),  # pragma pylint: disable=unnecessary-lambda
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
    )
    hand_id = db.Column(
        GUID,
        default=lambda: uuid.uuid4(),  # pragma pylint: disable=unnecessary-lambda
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
    )
    name = db.Column(db.String)
    score = db.Column(db.Integer, default=0)
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        output = "<Player %r, " % self.player_id
        output += "Name %r, " % self.name
        output += "Hand %r, " % self.hand_id
        output += "Score %r, " % self.score
        output += ">"
        return output


class PlayerSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = Player
        sqla_session = db.session

    name = fields.Str()
    # player_id = fields.UUID()
    player_id = fields.Str()
    # hand_id = fields.UUID()
    hand_id = fields.Str()
    score = fields.Int()
    timestamp = fields.DateTime()


class Hand(db.Model):
    __tablename__ = "hand"
    _id = db.Column(
        db.Integer, primary_key=True, nullable=False, index=True, unique=True,
    )
    # This is also a foreign key, but to more than one table:
    # - player.hand_id
    # - round.hand_id
    # - roundteam.hand_id
    hand_id = db.Column(GUID, index=True, nullable=False)
    card = db.Column(db.String, nullable=False)

    def __repr__(self):
        output = "<Hand %r, " % self.hand_id
        output += "Card %r, " % self.card
        output += ">"
        return output


class HandSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = Hand
        sqla_session = db.session

    hand_id = fields.Str()
    card = fields.Str()

