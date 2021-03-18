from pinochle.models.core import db  # pragma: no cover

# This is used for database debugging only. No test coverage needed.
def dump_db():  # pragma: no cover
    con = db.engine.raw_connection()
    for line in con.iterdump():
        if "INSERT" in line:
            print("%s\n" % line)
