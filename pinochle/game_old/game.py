"""
This encapsulates data and aspects of a game.

License: GPLv3
"""

import libuuid as uuid
from typing import List
from datetime import datetime

import pinochle.config


class Game(db.Model):
    __tablename__ = "game"
    _id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String)
    hand = db.Column(db.String)
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
