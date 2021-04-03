from datetime import datetime

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from .core import db
from .GUID import GUID

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


class TeamPlayers(db.Model):
    __tablename__ = "team_players"
    team_id = db.Column(
        GUID,
        db.ForeignKey("team.team_id"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    player_id = db.Column(
        GUID,
        db.ForeignKey("player.player_id"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        output = "<TeamPlayers: "
        output += "team_id=%r, " % self.team_id
        output += "player_id=%r, " % self.player_id
        output += ">"
        return output


class TeamPlayersSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TeamPlayers
        sqla_session = db.session
        include_fk = True
        include_relationships = True
        load_instance = True
