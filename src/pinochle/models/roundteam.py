import uuid
from datetime import datetime

from marshmallow import fields
from pinochle.models.GUID import GUID

from .core import db, ma

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


class RoundTeam(db.Model):
    __tablename__ = "round_team"
    round_id = db.Column(
        GUID,
        db.ForeignKey("round.round_id"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    team_id = db.Column(
        GUID,
        db.ForeignKey("team.team_id"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    hand_id = db.Column(
        GUID,
        default=lambda: uuid.uuid4(),  # pragma pylint: disable=unnecessary-lambda
        primary_key=False,
        nullable=True,
        index=False,
    )
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        output = "<RoundTeam: "
        output += "Round %r, " % self.round_id
        output += "Team %r, " % self.team_id
        output += "Hand %r, " % self.hand_id
        output += ">"
        return output


class RoundTeamSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = RoundTeam
        sqla_session = db.session

    # round_id = fields.UUID()
    round_id = fields.Str()
    # team_id = fields.UUID()
    team_id = fields.Str()
    hand_id = fields.Str()
    timestamp = fields.DateTime()
