from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from .core import db
from .GUID import GUID

# Suppress invalid no-member messages from pylint.
# pylint: disable=no-member


class Hand(db.Model):
    __tablename__ = "hand"
    _id = db.Column(
        db.Integer, primary_key=True, nullable=False, index=True, unique=True,
    )
    # This is also a foreign key, but to more than one table:
    # - player.hand_id
    # - round.hand_id
    # - roundteam.hand_id
    hand_id = db.Column(GUID, index=True, nullable=False)
    card = db.Column(db.String, nullable=False)
    seq = db.Column(db.Integer, nullable=False, unique=False, default=-1)

    def __repr__(self):
        output = "<Hand: "
        output += "hand_id=%r, " % self.hand_id
        output += "card=%r, " % self.card
        output += "seq=%r, " % self.seq
        output += ">"
        return output


class HandSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Hand
        sqla_session = db.session
        include_fk = True
        include_relationships = True
        load_instance = True
