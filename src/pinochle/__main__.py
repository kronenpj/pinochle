from pinochle.app_factory import create_app

# If we're running in stand alone mode, run the application
if __name__ == "__main__":

    # app.run(host="0.0.0.0", port=5000, debug=True)
    create_app().run(host="0.0.0.0", port=5000, debug=True)
