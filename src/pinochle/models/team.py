import uuid
from datetime import datetime

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
        output = "<Team: "
        output += "team_id=%r, " % self.team_id
        output += "name=%r, " % self.name
        output += "score=%r, " % self.score
        output += ">"
        return output


class TeamSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Team
        sqla_session = db.session
        include_fk = True
        include_relationships = True
        load_instance = True
