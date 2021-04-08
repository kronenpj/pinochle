"""
Module to hold test fixtures.

License: GPLv3
"""
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


@pytest.fixture
def patch_ws_messenger(monkeypatch):
    """
    Fixture to replace methods of WebSocketMessenger implementation.
    """
    monkeypatch.setattr(WSM, "register_new_player", do_nothing)
    monkeypatch.setattr(WSM, "distribute_registered_players", do_nothing)
    monkeypatch.setattr(WSM, "websocket_broadcast", do_nothing)
