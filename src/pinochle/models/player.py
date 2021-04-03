import uuid
from datetime import datetime

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from .core import db
from .GUID import GUID

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
    meld_score = db.Column(db.Integer, default=0)
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        output = "<Player: "
        output += "player_id=%r, " % self.player_id
        output += "name=%r, " % self.name
        output += "hand_id=%r, " % self.hand_id
        output += "meld_score=%r, " % self.meld_score
        output += ">"
        return output


class PlayerSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Player
        sqla_session = db.session
        include_fk = True
        include_relationships = True
        load_instance = True
