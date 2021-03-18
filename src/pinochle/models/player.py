import uuid
from datetime import datetime

from marshmallow import fields
from pinochle.models.GUID import GUID

from .core import db, ma

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


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
