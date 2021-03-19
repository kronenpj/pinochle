"""
This is the default configuration file imported by app_factory.
Nothing in this file is sensitive as it only provides defaults to
be overridden by items in src/pinochle/instance/application.cfg.py.

The instance file has the same format and will override and add to
constants specified here. These go into the app.config area of Flask
for its use.

To use a PostgreSQL database, for example, the application.cfg.py file
could contain this:

    SQLALCHEMY_DB_PREFIX = "postgresql+psycopg2"
    DB_USERNAME = 'dbadmin'
    DB_PASSWORD = 'dbadminpassword'
    DB_SERVER = 'pgservername.example.com'
    DB_NAME = 'pgdatabasename'

    SECRET_KEY = "MySuPeRsEcReTrAnDoMkEyGoEsHeRe"
    SECURITY_PASSWORD_SALT = "12345678-9abc-4def-0123-456789abcdef"

The default points to an in-memory SQLite database for convenience in development
and testing.
"""
SERVER_NAME = "localhost:5000"

DB_USERNAME = ""
DB_PASSWORD = ""
DB_SERVER = "localhost"
DB_NAME = ":memory:"
SQLALCHEMY_DB_PREFIX = "sqlite"
