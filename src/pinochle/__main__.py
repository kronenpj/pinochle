#!/usr/bin/env python3

from pinochle import app_factory  # pragma: no cover


# If we're running in stand alone mode, run the application
if __name__ == "__main__":
    application = app_factory.create_app()  # pragma: no cover

    application.run(
        host="0.0.0.0", port=5000, use_reloader=True, use_debugger=True, threaded=True
    )
