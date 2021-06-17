"""
Invoke selenium in four separate browsers and step through one complete round from
beginning to end.

Requires a Selenium Grid or four standalone selenium instances.
Configuration available in conftest.py's SeleniumConfig class.
"""
import json
import logging
import sys
import threading
import time
from copy import deepcopy
from random import choice
from typing import Dict, List, Tuple

import pytest
import requests
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from selenium import webdriver
from selenium.common.exceptions import (
    MoveTargetOutOfBoundsException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from pinochle import wsgi
from pinochle.cards.const import SUITS
from tests.conftest import SeleniumConfig
from tests.test_utils import PLAYER_NAMES, TEAM_NAMES

# pylint: disable=attribute-defined-outside-init

# Declare this entire module as being a 'slow' test.
pytestmark = pytest.mark.slow


def setup_new_game() -> Tuple[str, List[str]]:
    player_ids = []
    team_ids = []
    game_id = ""
    round_id = ""

    # Create players and store the returned UUID for later use.
    for player in PLAYER_NAMES:
        data = {"name": player}
        response = requests.post(
            f"{SeleniumConfig.BASE_URL}/api/player",
            json=data,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 201
        r_data = json.loads(response.text)
        player_ids.append(r_data["player_id"])
    assert len(player_ids) == 4

    # Create teams and store the returned UUID for later use.
    for team in TEAM_NAMES:
        data = {"name": team}
        response = requests.post(
            f"{SeleniumConfig.BASE_URL}/api/team",
            json=data,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 201
        r_data = json.loads(response.text)
        team_ids.append(r_data["team_id"])

    # Attach players to the new teams.
    for t_idx in [0, 1]:
        for p_idx in [0, 1]:
            data = {"player_id": player_ids[p_idx + 2 * t_idx]}
            response = requests.post(
                f"{SeleniumConfig.BASE_URL}/api/team/{team_ids[t_idx]}",
                json=data,
                headers={"Content-Type": "application/json"},
            )
            assert response.status_code == 201

    # Create game with a kitty size of 4 cards.
    response = requests.post(
        f"{SeleniumConfig.BASE_URL}/api/game?kitty_size=4",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 201
    r_data = json.loads(response.text)
    game_id = r_data["game_id"]
    print(f"Created game {game_id}")

    # Create round.
    response = requests.post(
        f"{SeleniumConfig.BASE_URL}/api/game/{game_id}/round",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 201
    r_data = json.loads(response.text)
    round_id = r_data["round_id"]

    # Attach teams to the new round.
    data = team_ids
    response = requests.post(
        f"{SeleniumConfig.BASE_URL}/api/round/{round_id}",
        json=data,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 201

    # Start the game.
    response = requests.post(f"{SeleniumConfig.BASE_URL}/api/round/{round_id}/start")

    return game_id, player_ids


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


class TestSingleRound:
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
        TestSingleRound.server_thread.finalise()

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
        TestSingleRound.server_thread = ServerThread()
        TestSingleRound.server_thread.setup(app)
        TestSingleRound.server_thread.start()

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

    def test_050_start_browsers(self):
        """
        Navigate to the BASE_URL
        """
        # global TestSingleRound.game_id, TestSingleRound.players, TestSingleRound.player_ids
        # Create new game.
        print("Creating new game.")
        TestSingleRound.game_id, TestSingleRound.player_ids = setup_new_game()

        TestSingleRound.players = self.retrieve_player_names(TestSingleRound.player_ids)
        assert len(TestSingleRound.players) == len(TestSingleRound.player_ids)

        assert self.driver
        for t_driver in self.driver:
            t_driver.get(f"{SeleniumConfig.BASE_URL}/")
            t_driver.maximize_window()
            # t_driver.fullscreen_window()

    def test_100_browser_wait(self):
        """
        Wait for the basic page to be rendered.
        """
        assert len(TestSingleRound.players) > 0
        assert len(TestSingleRound.player_ids) > 0
        assert len(TestSingleRound.players) == len(TestSingleRound.player_ids)

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
            except TimeoutException:
                print(f"Retrying browsers. {counter} left.")
                limit -= 1
            except NoSuchElementException:
                print(f"Retrying browsers. {counter} left.")
                limit -= 1

    def test_110_browser_wait(self):
        """
        See if the 'no games found' button appears.
        """
        try:
            for driver in self.driver:
                WebDriverWait(driver, 2).until(
                    expected_conditions.presence_of_element_located(
                        (By.XPATH, "//*[@id='nogame']")
                    )
                )
        except NoSuchElementException:
            return
        except TimeoutException:
            return

        assert not "There should be a game created."

    def test_140_browser_wait(self):
        """
        Wait for the list of players to appear.
        """
        for driver in self.driver:
            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, "(//*[@id='canvas' and contains(.,'Player:')])")
                )
            )

    def test_150_browser_find_name(self):
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
                    TestSingleRound.players[TestSingleRound.player_ids[counter]]
                ),
            )
            assert element
            element.click()

    def test_160_browser_click_on_name(self):
        """
        Locate and click on the button corresponding to the player_id in the array.
        """
        for counter, driver in enumerate(self.driver):
            button_element = driver.find_element(
                By.XPATH, "//*[@id='{}']".format(TestSingleRound.player_ids[counter])
            )
            assert button_element
            button_element.click()

    def test_170_browser_wait_for_score(self):
        """
        Wait for a specific element to appear indicating a player was chosen.
        """
        for driver in self.driver:
            WebDriverWait(driver, 5).until(
                expected_conditions.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[@id='game_status']/span[not(contains(@style,'visibility: hidden'))]",
                    )
                )
            )

    def test_180_check_player_name(self):
        """
        Verify the player name we expect appears, based on the chosen player_id.
        """
        assert len(TestSingleRound.players) >= len(self.driver)
        for counter, driver in enumerate(self.driver):
            print(
                "Looking for player {}.".format(
                    TestSingleRound.players[TestSingleRound.player_ids[counter]]
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
                    TestSingleRound.players[TestSingleRound.player_ids[counter]]
                )
            )

    def test_190_wait_for_bid_dialog(self):
        """
        Wait for the "Bid or Pass" or "Bid Update" prompt.
        """
        for driver in self.driver:
            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located(
                    (By.CLASS_NAME, "brython-dialog-title",)
                )
            )

    def test_200_submit_bids(self):
        """
        Locate the "Bid or Pass" or "Bid Update" prompt.
        """
        # global TestSingleRound.driver_bid_winner

        loop_limit = 0
        t_player_ids = deepcopy(TestSingleRound.player_ids)
        t_empty = ["blank" for _ in range(len(t_player_ids))]
        bid_occurred = False

        print(f"t_empty: {t_empty}")
        while t_player_ids != t_empty and loop_limit < 100:
            print(f"t_player_ids: {t_player_ids}")
            for counter, driver in enumerate(self.driver):
                try:
                    element = driver.find_element(
                        By.XPATH,
                        "/html/body/div[3]/div[1]/span[contains(.,'Bid or Pass')]",
                    )
                except NoSuchElementException:
                    # Try again later when the Bid or Pass prompt isn't available.
                    continue
                if element:
                    # Make sure only one player bids.
                    if not bid_occurred:
                        # Bid button
                        bid_button = driver.find_element(
                            By.XPATH, "/html/body/div[3]/div[3]/button[1]",
                        )
                        bid_occurred = True
                        TestSingleRound.driver_bid_winner = counter
                    else:
                        # Pass button
                        bid_button = driver.find_element(
                            By.XPATH, "/html/body/div[3]/div[3]/button[2]",
                        )
                    # Record that this player has bid or passed.
                    t_player_ids[counter] = "blank"
                    bid_button.click()
            loop_limit += 1
        assert TestSingleRound.driver_bid_winner >= 0
        print(f"Driver array index = {TestSingleRound.driver_bid_winner}")
        print(
            "Bid winner = {}".format(
                TestSingleRound.players[
                    TestSingleRound.player_ids[TestSingleRound.driver_bid_winner]
                ]
            )
        )

    def test_210_bury_cards_and_select_trump(self):
        """
        Bury cards and select trump suit.
        """
        # Wait for the cards from the kitty to be added to the player's hand.
        driver = self.driver[TestSingleRound.driver_bid_winner]
        WebDriverWait(driver, 15).until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, "//*[contains(@id,'player11')]")
            )
        )

        # Choose a trump suit.
        if "firefox" not in driver.name:
            declared_trump = choice(SUITS)  # Chrome & Edge work
        else:
            # Deal with Firefox's displaced glyphs
            # In Firefox, only 'spade' works due to the displacement between where Firefox
            # displays the glyph and where it shows the glyph being positioned in the
            # developer utility / programmatically.
            declared_trump = "Spades"
        declared_trump = declared_trump.lower().rstrip("s")

        trump_dialog = driver.find_element(By.CLASS_NAME, "brython-dialog-title")
        card_elements = driver.find_elements(By.XPATH, "//*[contains(@id,'player')]")
        card_ids = [
            x.get_attribute("id") for x in card_elements if x.get_attribute("href")
        ]

        attempts = 11
        try:
            while attempts and driver.find_element(
                By.XPATH, "/html/body/div[3]/*[contains(.,'Select Trump Suit')]",
            ):
                assert card_ids
                t_id = choice(card_ids)
                # print(f"Attempting to move {t_id}")
                element = driver.find_element(By.ID, t_id)
                assert element

                # Choose another card to be buried.
                try:
                    webdriver.ActionChains(driver).drag_and_drop_by_offset(
                        element, 0, 150
                    ).perform()
                    card_ids.remove(t_id)
                except MoveTargetOutOfBoundsException as e:
                    print(f"Caught MTOOBE exception...{e}")
                    card_ids.remove(t_id)
                except WebDriverException as e1:
                    print(f"Ignoring WDE exception: {e1}")
                    # pass

                trump_elements = trump_dialog.find_elements(
                    By.XPATH, f"//*[@id='{declared_trump}']"
                )
                print(f"Elements found: {len(trump_elements)}")
                for element in trump_elements:
                    print(f"select_trump - attribute: {element.get_attribute('id')}")
                    try:
                        element.click()
                        attempts -= 1
                    except WebDriverException as e:
                        print(f"Ignoring webdriver exception: {e}")
                        pass
        except NoSuchElementException:
            # This is expected when the dialog box disappears.
            pass
        except IndexError:
            # We ran out of cards to try.
            assert False
        if not attempts:
            pytest.exit("Failed to select trump after allotted attempts.")

    def test_220_wait_for_send_meld_button(self):
        """
        Wait for the send meld button to appear.
        """
        for driver in self.driver:
            WebDriverWait(driver, 5).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, "//*[@id='button_send_meld']",)
                )
            )

    def test_230_submit_no_meld(self):
        """
        Submit meld without choosing any cards.
        """
        # Locate and click the button.
        for driver in self.driver:
            send_meld_button = driver.find_element(
                By.XPATH, "//*[@id='button_send_meld']",
            )
            send_meld_button.click()

        # Wait for prompt to acknowledge as final meld.
        for driver in self.driver:
            WebDriverWait(driver, 5).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, "//button[text()='Yes']")
                )
            )
            # Acknowledge as final meld.
            t_dialog = driver.find_element(By.XPATH, "//button[text()='Yes']")
            t_dialog.click()

    def test_240_play_tricks(self):
        """
        Play tricks until players are out of cards.
        """
        keep_going = True
        while keep_going:
            time.sleep(0.1)
            # Create associations between drivers and the list of cards.
            for driver in self.driver:
                # Locate elements that start with 'player' in the ID attribute.
                t_cards = driver.find_elements(
                    By.XPATH, "//*[@id='canvas']/*[starts-with(@id, 'player')]"
                )
                # If the list is empty, flag to stop looping.
                if not t_cards:
                    keep_going = False
                    return
                # print("Choosing from ")
                # print(", ".join(x.get_attribute("id") for x in t_cards))

                # Choose a random card, click on it, and remove it from consideration
                t_card = choice(t_cards)
                # print(f"Moving {t_card.get_attribute('id')}")

                # Drag the card up a sufficient amount.
                webdriver.ActionChains(driver).drag_and_drop_by_offset(
                    t_card, 0, -200
                ).perform()

            time.sleep(0.2)
            for driver in self.driver:
                try:
                    # Acknowledge to continue playing
                    t_dialog = driver.find_element(
                        By.XPATH, "//button[text()='Next trick']"
                    )
                    t_dialog.click()
                except NoSuchElementException:
                    pass

    def test_250_locate_next_round_button(self):
        """
        Acknowledge last trick in the round.
        """
        acknowledged = False
        # Wait for prompt to acknowledge as final trick in the round.
        for driver in self.driver:
            try:
                # Acknowledge to continue playing
                t_dialog = driver.find_element(
                    By.XPATH, "//button[text()='Next round']"
                )
                t_dialog.click()
                acknowledged = True
                break
            except NoSuchElementException:
                # This will occur three out of four times as the prompt is only
                # presented to the winner of the last trick.
                pass

        assert acknowledged

    # def test_900_delete_game(self):
    #     response = requests.delete(f"{BASE_URL}/game/{g_game_id}")
    #     assert response.status_code == 200

    def test_990_sleep(self):
        """
        Sleep at the end so interaction with the browsers is possible.
        """
        print("\nSleeping...")
        time.sleep(0.5)
