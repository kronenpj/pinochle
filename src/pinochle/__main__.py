#!/usr/bin/env python3

import logging
import sys

from . import wsgi  # pragma: no cover
from .__init__ import GLOBAL_LOG_LEVEL

if __name__ == "__main__":
    ROOT_LOGGER = logging.getLogger()
    ROOT_LOGGER.setLevel(GLOBAL_LOG_LEVEL)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(ROOT_LOGGER.getEffectiveLevel())
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    ROOT_LOGGER.addHandler(handler)

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
