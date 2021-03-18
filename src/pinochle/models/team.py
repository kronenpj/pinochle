import uuid
from datetime import datetime

from marshmallow import fields
from pinochle.models.GUID import GUID

from .core import db, ma

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


class Team(db.Model):
    __tablename__ = "team"
    team_id = db.Column(
        GUID,
        default=lambda: uuid.uuid4(),  # pragma pylint: disable=unnecessary-lambda
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
    )
    name = db.Column(db.String)
    score = db.Column(db.Integer, default=0)
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        output = "<Team %r, " % self.team_id
        output += "Name %r, " % self.name
        output += "Score %r, " % self.score
        output += ">"
        return output


class TeamSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = Team
        sqla_session = db.session

    # team_id = fields.UUID()
    team_id = fields.Str()
    name = fields.Str()
    score = fields.Int()
    timestamp = fields.DateTime()
