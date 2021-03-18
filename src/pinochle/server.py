#!/usr/bin/env python3

from flask import render_template # pragma: no cover

from pinochle import app_factory # pragma: no cover

application = app_factory.create_app() # pragma: no cover

# Create a URL route in our application for "/"
@application.route("/home2.html") # pragma: no cover
def home2():
    """
    This function just responds to the browser URL
    localhost:5000/
    :return:        the rendered template 'home.html'
    """
    return render_template("home2.html")


# Create a URL route in our application for "/"
@application.route("/") # pragma: no cover
def home():
    """
    This function just responds to the browser URL
    localhost:5000/
    :return:        the rendered template 'home.html'
    """
    return render_template("home.html")


if __name__ == "__main__":
    # If we're running in stand alone mode, run the application
    application.run(
        host="0.0.0.0", port=5000, use_reloader=True, use_debugger=True, threaded=True
    )
