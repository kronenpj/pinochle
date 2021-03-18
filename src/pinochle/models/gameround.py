from datetime import datetime

from marshmallow import fields
from pinochle.models.GUID import GUID

from .core import db, ma

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


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
