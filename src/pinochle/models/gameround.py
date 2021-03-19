from datetime import datetime

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


class GameRoundSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = GameRound
        sqla_session = db.session
        include_fk = True
        include_relationships = True
        load_instance = True
