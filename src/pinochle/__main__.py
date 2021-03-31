#!/usr/bin/env python3

from . import wsgi  # pragma: no cover

GLOBAL_LOG_LEVEL = logging.WARNING

if __name__ == "__main__":
    wsgi.application.run(
        host="0.0.0.0", port=5000, use_reloader=True, use_debugger=True, threaded=True
    )
