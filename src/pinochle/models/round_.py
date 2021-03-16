import uuid
from datetime import datetime

from marshmallow import fields
from pinochle.config import db, ma
from pinochle.models.GUID import GUID
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import CHAR, TypeDecorator

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


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
