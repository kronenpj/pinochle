#!/usr/bin/env python3

# 3rd party moudles
import os

import connexion
from flask import Flask, render_template

# Local modules
from pinochle import config

# Get the application instance
connex_app = config.connex_app

# Read the swagger.yml file to configure the endpoints
connex_app.add_api("swagger.yml")

# Delete database file if it exists currently
if not os.path.exists(config.sqlite_url):
    # Create the database
    config.db.create_all()

# Create a URL route in our application for "/"
@connex_app.route("/home2.html")
def home2():
    """
    This function just responds to the browser URL
    localhost:5000/
    :return:        the rendered template 'home.html'
    """
    return render_template("home2.html")


# Create a URL route in our application for "/"
@connex_app.route("/home3.html")
def home3():
    """
    This function just responds to the browser URL
    localhost:5000/
    :return:        the rendered template 'home.html'
    """
    return render_template("home3.html")


# Create a URL route in our application for "/"
@connex_app.route("/")
def home():
    """
    This function just responds to the browser URL
    localhost:5000/
    :return:        the rendered template 'home.html'
    """
    return render_template("home.html")


# If we're running in stand alone mode, run the application
if __name__ == "__main__":
    connex_app.run(host="0.0.0.0", port=5000, debug=True)
