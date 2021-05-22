"""
Module to hold test fixtures.

License: GPLv3
"""

from unittest.mock import MagicMock

import geventwebsocket
import pytest
from pinochle import wsgi
from pinochle.models.core import db
from pinochle.ws_messenger import WebSocketMessenger as WSM

# Suppress invalid redefined-outer-name messages from pylint.
# pragma pylint: disable=redefined-outer-name

# Possible scopes:
# function, class, module, package, session
# Only package and sesion work with in-memory SQLite database.
@pytest.fixture(scope="package")
def app():
    """
        Fixture to create an in-memory database and make it available only for the set of
    import flask
        tests that call for this fixture. The database is re-created according to the scope.

        :yield: The application being tested with the temporary database.
        :rtype: FlaskApp
    """
    # print("Entering conftest.app...")
    app = wsgi.app

    # print("conftest.app, yielding app")
    yield app

    # print("conftest.app, removing db session")
    db.session.remove()


def do_nothing(*args, **kwargs):  # pylint: disable=unused-argument
    """
    Null function for mocking.
    """
    pass  # pylint: disable=unnecessary-pass


@pytest.fixture(scope="function")
def patch_geventws(monkeypatch):
    """
    Fixture to replace send method of WebSocket implementation with a no-op.
    """
    monkeypatch.setattr(geventwebsocket.websocket.WebSocket, "__init__", do_nothing)
    monkeypatch.setattr(geventwebsocket.websocket.WebSocket, "send", do_nothing)


@pytest.fixture(scope="function")
def patch_ws_messenger_to_MM():
    WSM.websocket_broadcast = MagicMock()
    WSM.websocket_broadcast.assert_has_calls
