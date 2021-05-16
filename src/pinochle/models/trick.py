import uuid
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from .core import db
from .GUID import GUID

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


class Trick(db.Model):
    __tablename__ = "trick"
    _id = db.Column(
        db.Integer, primary_key=True, nullable=False, index=True, unique=True,
    )
    trick_id = db.Column(
        GUID,
        default=lambda: uuid.uuid4(),  # pragma pylint: disable=unnecessary-lambda
        primary_key=False,
        nullable=False,
        index=True,
    )
    round_id = db.Column(GUID, db.ForeignKey("round.round_id"), index=False)
    trick_starter = db.Column(GUID, db.ForeignKey("player.player_id"), nullable=True)
    hand_id = db.Column(
        GUID,
        default=lambda: uuid.uuid4(),  # pragma pylint: disable=unnecessary-lambda
        primary_key=False,
        nullable=True,
        index=False,
    )

    def __repr__(self):
        output = "<Trick: "
        output += "trick_id=%r, " % self.trick_id
        output += "round_id=%r, " % self.round_id
        output += "trick_starter=%r, " % self.trick_starter
        output += "hand_id=%r, " % self.hand_id
        output += ">"
        return output


class TrickSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Trick
        sqla_session = db.session
        include_fk = True
        include_relationships = True
        load_instance = True
