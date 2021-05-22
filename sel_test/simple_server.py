# Currently just used for the temporary hack to quit the phantomjs process
# see below in quit_driver.
import signal
import threading
import wsgiref.simple_server

import flask
import pytest
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains


@pytest.mark.usefixtures("app")
class ServerThread(threading.Thread):
    def setup(self, app):
        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["TEST_SERVER_PORT"] = 5001
        self.port = app.config["TEST_SERVER_PORT"]

    def run(self):
        self.httpd = wsgiref.simple_server.make_server("0.0.0.0", self.port, self.app)
        print("Starting ServerThread:run:httpd.serve_forever")
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()


@pytest.mark.usefixtures("app")
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
            self.driver=driver_class()
        print("BrowserClient.init: driver instantiated")
        self.driver.set_window_size(1200, 760)
        print("BrowserClient.init: window size set")

    def finalise(self):
        self.driver.close()
        # A bit of hack this but currently there is some bug I believe in
        # the phantomjs code rather than selenium, but in any case it means that
        # the phantomjs process is not being killed so we do so explicitly here
        # for the time being. Obviously we can remove this when that bug is
        # fixed. See: https://github.com/SeleniumHQ/selenium/issues/767
        self.driver.service.process.send_signal(signal.SIGTERM)
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


@pytest.mark.usefixtures("app")
def make_url(app, endpoint, **kwargs):
    with app.app_context():
        return flask.url_for(endpoint, **kwargs)


# TODO: Ultimately we'll need a fixture so that we can have multiple
# test functions that all use the same server thread and possibly the same
# browser client.
@pytest.mark.usefixtures("app")
def test_server(app):
    # Start server
    server_thread = ServerThread()
    server_thread.setup(app)
    print("Starting server...")
    server_thread.start()
    print("Server started...")

    firefox_options = webdriver.FirefoxOptions()
    print("Firefox options set...")
    # driver = webdriver.Remote(
    #     command_executor="http://localhost:4444", options=firefox_options
    # )
    client = BrowserClient(browser="remote", hub_host="http://172.16.42.10:4444", options=firefox_options)
    print("Remote browser set...")
    driver = client.driver
    print("Local variable assigned...")

    print("Browser started...")

    try:
        port = app.config["TEST_SERVER_PORT"]
        app.config["SERVER_NAME"] = "172.16.42.10:{}".format(port)

        driver.get(make_url(app, "/"))
        assert "Pinochle" in driver.page_source

    finally:
        server_thread.stop()
        server_thread.join()
        client.finalise()
