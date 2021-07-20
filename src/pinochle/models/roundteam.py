import uuid
from datetime import datetime

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from .core import db
from .GUID import GUID

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
    team_order = db.Column(db.Integer)
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        output = "<RoundTeam: "
        output += "round_id=%r, " % self.round_id
        output += "team_id=%r, " % self.team_id
        output += "hand_id=%r, " % self.hand_id
        output += "team_order=%r, " % self.team_order
        output += ">"
        return output


class RoundTeamSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = RoundTeam
        sqla_session = db.session
        include_fk = True
        include_relationships = True
        load_instance = True
