"""
Custom exceptions for pinochle game.
"""


class PinochleError(Exception):
    pass


class InvalidDeckError(PinochleError):
    pass


class InvalidValueError(PinochleError):
    pass


class InvalidSuitError(PinochleError):
    pass
