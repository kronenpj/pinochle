"""
Custom exceptions for pinochle game.
"""


class AppNotInstantiatedError(Exception):
    pass


class PinochleError(Exception):
    pass


class InvalidDeckError(PinochleError):
    pass


class InvalidValueError(PinochleError):
    pass


class InvalidSuitError(PinochleError):
    pass
