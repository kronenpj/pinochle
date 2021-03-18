from datetime import datetime

from marshmallow import fields
from pinochle.models.GUID import GUID

from .core import db, ma

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
        output += "Team %r, " % self.team_id
        output += "Player %r, " % self.player_id
        output += ">"
        return output


class TeamPlayersSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = TeamPlayers
        sqla_session = db.session

    # team_id = fields.UUID()
    team_id = fields.Str()
    # player_id = fields.UUID()
    player_id = fields.Str()
    timestamp = fields.DateTime()
