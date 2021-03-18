from marshmallow import fields
from pinochle.models.GUID import GUID

from .core import db, ma

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

    def __repr__(self):
        output = "<Hand %r, " % self.hand_id
        output += "Card %r, " % self.card
        output += ">"
        return output


class HandSchema(ma.ModelSchema):
    def __init__(self, **kwargs):
        super().__init__(strict=True, **kwargs)

    class Meta:
        model = Hand
        sqla_session = db.session

    hand_id = fields.Str()
    card = fields.Str()
