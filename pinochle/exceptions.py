"""
Custom exceptions for pinochle game.
"""


class PinochleError(Exception):
    pass


class InvalidDeckError(PinochleError):
    pass


class InvalidTrumpError(PinochleError):
    pass
