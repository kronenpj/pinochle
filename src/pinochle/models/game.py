import uuid
from datetime import datetime

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from .core import db
from .GUID import GUID

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


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
    dealer_id = db.Column(GUID, default=None)
    kitty_size = db.Column(db.Integer, default=0)
    state = db.Column(db.Integer, default=0)
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        output = "<Game: "
        output += "game_id=%r " % self.game_id
        output += "dealer_id=%r, " % self.dealer_id
        output += "kitty_size=%r, " % self.kitty_size
        output += "state=%r, " % self.state
        output += ">"
        return output


class GameSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Game
        sqla_session = db.session
        include_fk = True
        include_relationships = True
        load_instance = True
