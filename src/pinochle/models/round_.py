import uuid
from datetime import datetime

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from .core import db, ma
from .GUID import GUID

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
        output = "<Round: "
        output += "round_id=%r, " % self.round_id
        output += "round_seq=%r, " % self.round_seq
        output += "hand_id=%r, " % self.hand_id
        output += "bid=%r, " % self.bid
        output += "bid_winner=%r, " % self.bid_winner
        output += "trump=%r" % self.trump
        output += ">"
        return output


class RoundSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Round
        sqla_session = db.session
        include_fk = True
        include_relationships = True
        load_instance = True
