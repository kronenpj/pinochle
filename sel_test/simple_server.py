# Currently just used for the temporary hack to quit the phantomjs process
# see below in quit_driver.
import signal
import threading
import wsgiref.simple_server

import flask
import selenium
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains


# @pytest.fixture()
class ServerThread(threading.Thread):
    def setup(self, app):
        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["TEST_SERVER_PORT"] = 5000
        self.port = app.config["TEST_SERVER_PORT"]

    def run(self):
        self.httpd = wsgiref.simple_server.make_server("0.0.0.0", self.port, self.app)
        print("Starting ServerThread:run:httpd.serve_forever")
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()


# @pytest.fixture()
class BrowserClient(object):
    """Interacts with a running instance of the application via animating a
    browser."""

    def __init__(self, browser="firefox", hub_host="", options=None):
        driver_class = {
            "chrome": webdriver.Chrome,
            "firefox": webdriver.Firefox,
            "remote": webdriver.Remote,
        }.get(browser)
        print("BrowserClient.init: driver_class set")
        if hub_host:
            print(f"Setting command_executor={hub_host}")
            self.driver = driver_class(command_executor=hub_host, options=options)
        else:
            self.driver = driver_class()
        print("BrowserClient.init: driver instantiated")
        # self.driver.set_window_size(1200, 760)
        # print("BrowserClient.init: window size set")

    def finalise(self):
        self.driver.close()
        self.driver.quit()

    def log_current_page(self, message=None, output_basename=None):
        content = self.driver.page_source
        # This is frequently what we really care about so I also output it
        # here as well to make it convenient to inspect (with highlighting).
        basename = output_basename or "log-current-page"
        file_name = basename + ".html"
        with open(file_name, "w") as outfile:
            if message:
                outfile.write("<!-- {} --> ".format(message))
            outfile.write(content)
        filename = basename + ".png"
        self.driver.save_screenshot(filename)


def make_url(app, endpoint, **kwargs):
    with app.app_context():
        return flask.url_for(endpoint, **kwargs)


# TODO: Ultimately we'll need a fixture so that we can have multiple
# test functions that all use the same server thread and possibly the same
# browser client.
def test_server(app):
    # Start server
    # server_thread = ServerThread()
    # server_thread.setup(app)
    # server_thread.start()
    # print("Server started...")

    firefox_options = webdriver.FirefoxOptions()
    print("Firefox options set...")

    client = BrowserClient(
        browser="remote", hub_host="http://172.16.42.10:4444", options=firefox_options
    )
    driver = client.driver
    print("Browser started...")

    try:
        port = app.config["TEST_SERVER_PORT"]
        app.config["SERVER_NAME"] = "172.16.42.10:{}".format(port)

        url = make_url(app, '/')
        print(f"{url=}")
        driver.get(url)
        assert "Pinochle" in driver.page_source

    finally:
        # server_thread.stop()
        # server_thread.join()
        try:
            client.finalise()
        except selenium.common.exceptions.InvalidSessionIdException:
            pass
