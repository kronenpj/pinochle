import uuid
from datetime import datetime

from pinochle.models.GUID import GUID

from .core import db, ma

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
        output += "Hand_id %r, " % self.hand_id
        output += "Bid %r, " % self.bid
        output += "Winner %r, " % self.bid_winner
        output += "Trump %r" % self.trump
        output += ">"
        return output


class RoundSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Round
        sqla_session = db.session
        include_fk = True
        include_relationships = True
        load_instance = True
