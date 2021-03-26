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
        output = "<Hand: "
        output += "hand_id=%r, " % self.hand_id
        output += "card=%r, " % self.card
        output += ">"
        return output


class HandSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Hand
        sqla_session = db.session
        include_fk = True
        include_relationships = True
        load_instance = True
