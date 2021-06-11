#!/usr/bin/env python3

from . import wsgi  # pragma: no cover
from .__init__ import setup_logging


if __name__ == "__main__":
    ROOT_LOGGER = setup_logging()

    # wsgi.application.run(
    #     host="0.0.0.0", port=5000, use_reloader=True, use_debugger=True, threaded=True
    # )

    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(
        ("", 5000),
        wsgi.application,
        handler_class=WebSocketHandler,
        log=ROOT_LOGGER,
        error_log=ROOT_LOGGER,
    )
    server.serve_forever()
