import uuid
from datetime import datetime

from pinochle.models.GUID import GUID

from .core import db, ma

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
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        output = "<Game %r" % self.game_id
        output += ">"
        return output


class GameSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Game
        sqla_session = db.session
        include_fk = True
        include_relationships = True
        load_instance = True
