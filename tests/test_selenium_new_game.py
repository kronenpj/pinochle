"""
Invoke selenium in four separate browsers and step through creating a game from
beginning to end.

Requires a Selenium Grid or four standalone selenium instances.
Configuration available in conftest.py's SeleniumConfig class.
"""
import json
import logging
import sys
import threading
import time
from random import choice
from typing import Dict, List

import pytest
import requests
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from pinochle import wsgi
from tests.conftest import SeleniumConfig
from tests.test_utils import PLAYER_NAMES, TEAM_NAMES

# pylint: disable=attribute-defined-outside-init

# Declare this entire module as being a 'slow' test.
pytestmark = pytest.mark.slow


def obtain_game_information() -> str:
    game_id = ""

    response = requests.get(
        f"{SeleniumConfig.BASE_URL}/api/game",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    r_data = json.loads(response.text)
    print("obtain_game_information: r_data(game): ", r_data)
    game_id = r_data[0]["game_id"]
    print("obtain_game_information: game_id=", game_id)
    assert game_id

    return game_id


def obtain_player_information() -> List[str]:
    _round_id = ""
    player_ids = []
    _team_ids = []

    response = requests.get(
        f"{SeleniumConfig.BASE_URL}/api/game/{TestNewGame.game_id}/round",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    r_data = json.loads(response.text)
    print("obtain_player_information: r_data(round): ", r_data)
    _round_id = r_data["round_id"]
    print("obtain_player_information: _round_id=", _round_id)
    assert _round_id

    _tries = 5
    while _tries > 0:
        response = requests.get(
            f"{SeleniumConfig.BASE_URL}/api/round/{_round_id}/teams",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        r_data = json.loads(response.text)
        print("obtain_player_information: r_data(team): ", r_data)
        _team_ids = r_data["team_ids"]
        print("obtain_player_information: _team_ids=", _team_ids)
        if _team_ids and len(_team_ids) == 2:
            _tries = 0
            break
        time.sleep(1)
        _tries -= 1
    assert len(_team_ids) == 2

    for _team_id in _team_ids:
        response = requests.get(
            f"{SeleniumConfig.BASE_URL}/api/team/{_team_id}",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        r_data = json.loads(response.text)
        print("obtain_player_information: r_data(player): ", r_data)
        _players = r_data["player_ids"]
        for _tmp_player_id in _players:
            player_ids.append(_tmp_player_id)

    print("obtain_player_information: player_ids=", player_ids)
    assert len(player_ids) == 4

    return player_ids


class ServerThread(threading.Thread):
    def setup(self, app):
        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["TEST_SERVER_PORT"] = SeleniumConfig.TEST_SERVER_PORT
        self.port = app.config["TEST_SERVER_PORT"]

        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.WARNING)

        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(self.root_logger.getEffectiveLevel())
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.root_logger.addHandler(handler)

    def run(self):
        self.httpd = pywsgi.WSGIServer(
            ("", SeleniumConfig.TEST_SERVER_PORT),
            wsgi.application,
            handler_class=WebSocketHandler,
            log=self.root_logger,
            error_log=self.root_logger,
        )
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.stop(timeout=0.1)
        self.httpd.close()

    def finalise(self):
        self.stop()
        self.join()


class TestNewGame:
    driver: List[webdriver.Remote] = []
    handles = {}
    server_thread = None

    def teardown_class(self):
        # Collect logs before quitting browsers.
        if SeleniumConfig.COLLECT_BROWSER_LOGS:
            for idx, driver in enumerate(self.driver):
                if "firefox" not in driver.name:
                    message = [x for x in driver.get_log("browser")]
                    print("Log for browser: {}/{}".format(idx, driver.name))
                    print("\n".join(x["message"] for x in message[:-5]))
                else:
                    print("Log for browser: {}/{}".format(idx, driver.name))
                    print("Not collecting logs from firefox - throws:")
                    print("    WebDriverException: Message: HTTP method not allowed")
                print()

        # time.sleep(60)
        try:
            # Stop all browsers
            for driver in self.driver:
                driver.quit()
        except WebDriverException:
            pass

        # Stop web server
        if TestNewGame.server_thread:
            TestNewGame.server_thread.finalise()

    def wait_for_window(self, timeout=2000):
        time.sleep(round(timeout / 1000))
        wh_now = self.driver[len(self.driver)].window_handles
        wh_then = self.handles["window_handles"]
        if len(wh_now) > len(wh_then):
            return set(wh_now).difference(set(wh_then)).pop()

    @staticmethod
    def retrieve_player_names(player_id_list: List[str]) -> Dict[str, str]:
        """
        GIVEN a Flask application configured for testing
        WHEN the '/api/player' page is requested (POST)
        THEN check that the response is a UUID and contains the expected information
        """
        response = requests.get(f"{SeleniumConfig.BASE_URL}/api/player")
        print(f"response.text={response.text}")
        assert response.status_code == 200
        assert response.text
        # This is a JSON formatted STRING
        response_str = response.text
        response_data = json.loads(response_str)
        print(f"response_str={response_str}")
        print(f"response_data={response_data}")
        player_names = {
            i.get("player_id"): i.get("name")
            for i in response_data
            if i.get("player_id") in player_id_list
        }
        assert len(player_names) == 4
        return player_names

    def test_000_setup_class(self, app):
        assert app
        # Start server
        TestNewGame.server_thread = ServerThread()
        TestNewGame.server_thread.setup(app)
        TestNewGame.server_thread.start()

        for seq in range(4):
            t_browser = choice(list(SeleniumConfig.BROWSER_LIST.keys()))
            t_options = SeleniumConfig.BROWSER_LIST[t_browser]()
            t_options.set_capability("platform", "ANY")
            t_options.set_capability("se:timeZone", "US/Eastern")

            # Can't select video on standalone containers.
            if (
                not SeleniumConfig.USE_SELENIUM_STANDALONE
                and SeleniumConfig.COLLECT_VIDEO
            ):
                t_options.set_capability("se:recordVideo", True)
                t_options.set_capability("se:screenResolution", "1920x1080")

            if SeleniumConfig.COLLECT_BROWSER_LOGS:
                if t_browser == "chrome":
                    t_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
                else:
                    t_options.set_capability("loggingPrefs", {"browser": "ALL"})

            if SeleniumConfig.USE_SELENIUM_STANDALONE:
                driver = webdriver.Remote(
                    command_executor=f"{SeleniumConfig.SELENIUM_STANDALONE_URI}{seq+1}",
                    options=t_options,
                )
            else:
                driver = webdriver.Remote(
                    command_executor=SeleniumConfig.SELENIUM_HUB_URL, options=t_options,
                )

            self.driver.append(driver)

    def test_100_load_start_application(self):
        """
        Navigate to the BASE_URL
        """
        assert self.driver
        for t_driver in self.driver:
            t_driver.get(f"{SeleniumConfig.BASE_URL}/")
            t_driver.maximize_window()
            # t_driver.fullscreen_window()

    def test_110_wait_for_app_init(self):
        """
        Wait for the basic page to be rendered.
        """
        # assert len(TestNewGame.players) > 0
        # assert len(TestNewGame.player_ids) > 0
        # assert len(TestNewGame.players) == len(TestNewGame.player_ids)

        limit = 8  # About 64 seconds.
        while limit:
            counter = len(self.driver)
            try:
                for driver in self.driver:
                    WebDriverWait(driver, 2).until(
                        expected_conditions.presence_of_element_located(
                            (By.XPATH, "//*[@id='card_table']")
                        )
                    )
                    print(
                        f"Browser {self.driver.index(driver)} ({driver.name}) located card_table."
                    )
                    counter -= 1
                if not counter:
                    limit = 0
            except (TimeoutException, NoSuchElementException):
                print(f"Retrying browsers. {counter} left.")
                limit -= 1

    def test_120_wait_for_game_list(self):
        """
        See if the 'no games found' button appears.
        """
        try:
            for driver in self.driver:
                WebDriverWait(driver, 5).until(
                    expected_conditions.presence_of_element_located(
                        (By.XPATH, "//*[@id='nogame']")
                    )
                )
        except (NoSuchElementException, TimeoutException):
            assert not "There should not be a game created yet."

        try:
            for driver in self.driver:
                WebDriverWait(driver, 5).until(
                    expected_conditions.presence_of_element_located(
                        (By.XPATH, "//*[@id='newgame']")
                    )
                )
        except (NoSuchElementException, TimeoutException):
            assert not "The create new game button was not present."

    def test_130_select_create_game_button(self):
        # Create new game.
        print("Creating new game.")

        # Select a single browser to create the game.
        driver = self.driver[0]
        button_element = driver.find_element(By.XPATH, "//*[@id='newgame']")
        assert button_element
        button_element.click()

        try:
            WebDriverWait(driver, 5).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, "//*[@id='team0']")
                )
            )
        except (NoSuchElementException, TimeoutException):
            assert not "The form didn't appear in time."

    def test_140_gather_game_info(self):
        TestNewGame.game_id = obtain_game_information()

        assert TestNewGame.game_id

    def test_150_fill_and_submit_form(self):
        # Select a single browser to create the game.
        driver = self.driver[0]
        for idx, team in enumerate(TEAM_NAMES):
            input_element = driver.find_element(
                By.XPATH, "//*[@id='team{}']".format(idx)
            )
            input_element.clear()
            input_element.send_keys(team)

        for idx, player in enumerate(PLAYER_NAMES):
            input_element = driver.find_element(
                By.XPATH, "//*[@id='player{}']".format(idx)
            )
            input_element.clear()
            input_element.send_keys(player)

        button_element = driver.find_element(By.XPATH, "//*[@id='submit']")
        button_element.click()

    def test_160_select_created_game(self):
        # In each of the other browsers, click on the 'nogame' button to refresh
        # the list of available games.
        for driver in self.driver[1:]:
            button_element = driver.find_element(By.XPATH, "//*[@id='nogame']")
            assert button_element
            button_element.click()

        try:
            for driver in self.driver[1:]:
                WebDriverWait(driver, 5).until(
                    expected_conditions.presence_of_element_located(
                        (By.XPATH, "//*[@id='{}']".format(TestNewGame.game_id))
                    )
                )
        except (NoSuchElementException, TimeoutException):
            assert not "The button for the created test game was not present."

        for driver in self.driver[1:]:
            button_element = driver.find_element(
                By.XPATH, "//*[@id='{}']".format(TestNewGame.game_id)
            )
            assert button_element
            button_element.click()

    def test_170_wait_for_player_list(self):
        """
        Wait for the list of players to appear.
        """
        for driver in self.driver:
            WebDriverWait(driver, 5).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, "(//*[@id='canvas' and contains(.,'Player:')])")
                )
            )

    def test_180_gather_player_info(self):
        TestNewGame.player_ids = obtain_player_information()

        TestNewGame.players = self.retrieve_player_names(TestNewGame.player_ids)

        assert len(TestNewGame.players) == len(TestNewGame.player_ids)

    def test_190_browser_find_name(self):
        """
        Locate the player's button corresponding to the sequence of the driver / player_id
        """
        for counter, driver in enumerate(self.driver):
            # NOTE: Firefox throws:
            # selenium.common.exceptions.ElementNotInteractableException: Message:
            # Element <g id="x"> could not be scrolled into view.
            # Since this is a crucial bit of the test, it can't be worked around like the
            # remainder of the problems FF has.
            element = driver.find_element(
                By.XPATH,
                '(//*[@id="canvas" and contains(.,"Player: {}")])'.format(
                    TestNewGame.players[TestNewGame.player_ids[counter]]
                ),
            )
            assert element

    def test_200_browser_click_on_name(self):
        """
        Locate and click on the button corresponding to the player_id in the array.
        """
        for counter, driver in enumerate(self.driver):
            button_element = driver.find_element(
                By.XPATH, "//*[@id='{}']".format(TestNewGame.player_ids[counter])
            )
            assert button_element
            print(f"200: Clicking on button for id: {TestNewGame.player_ids[counter]}")
            button_element.click()

    def test_210_browser_wait_for_score(self):
        """
        Wait for a specific element to appear indicating a player was chosen.
        """
        # This test fails inconsistently.
        for driver in self.driver:
            WebDriverWait(driver, 15).until(
                expected_conditions.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[@id='game_status']/span[not(contains(@style,'visibility: hidden'))]",
                    )
                )
            )

    def test_220_check_player_name(self):
        """
        Verify the player name we expect appears, based on the chosen player_id.
        """
        assert len(TestNewGame.players) >= len(self.driver)
        for counter, driver in enumerate(self.driver):
            print(
                "Looking for player {}.".format(
                    TestNewGame.players[TestNewGame.player_ids[counter]]
                )
            )
            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[@id='player_name']/span[not(contains(@style,'visibility: hidden'))]",
                    )
                )
            )
            print(
                "Player {} found.".format(
                    TestNewGame.players[TestNewGame.player_ids[counter]]
                )
            )

    # def test_900_delete_game(self):
    #     response = requests.delete(f"{BASE_URL}/game/{g_game_id}")
    #     assert response.status_code == 200

    def test_990_sleep(self):
        """
        Sleep at the end so interaction with the browsers is possible.
        """
        print("\nSleeping...")
        time.sleep(0.5)
