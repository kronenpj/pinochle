import os

from .server import ioloop, make_app

if __name__ == "__main__":  # pragma: no cover
    if not os.path.exists("server.py") and os.path.exists("pinochle/server.py"):
        print("Changing current directory to pinochle.")
        os.chdir("pinochle")

    APP = make_app()
    APP.listen(8888)
    ioloop.IOLoop.current().start()
