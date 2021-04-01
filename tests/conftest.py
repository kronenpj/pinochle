"""
Module to hold test fixtures.

License: GPLv3
"""
import pytest
from pinochle import wsgi
from pinochle.models.core import db

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
