# Generated by Selenium IDE
import json
import time
from copy import deepcopy
from random import choice
from typing import Dict, List, Tuple

import requests
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
from pinochle.cards.const import SUITS
from tests.test_utils import PLAYER_NAMES, TEAM_NAMES

G_SELENIUM_HOST = "172.16.42.10"
G_SELENIUM_STANDALONE_URI = f"http://{G_SELENIUM_HOST}:444"
G_SELENIUM_HUB_URL = f"http://{G_SELENIUM_HOST}:4444"
# G_BROWSER_LIST = ['firefox', 'chrome','MicrosoftEdge']
G_BROWSER_LIST = ["chrome"]
G_BROWSER = G_BROWSER_LIST[0]
BASE_URL = "http://172.16.42.10:5000"

# For some reason placing these in the class causes stored values to be lost.
g_driver_bid_winner = -1
g_game_id = ""
g_player_ids = []
g_players = {}


def setup_new_game() -> Tuple[str, List[str]]:
    player_ids = []
    team_ids = []
    game_id = ""
    round_id = ""

    # Create players and store the returned UUID for later use.
    for player in PLAYER_NAMES:
        data = {"name": player}
        response = requests.post(
            f"{BASE_URL}/api/player",
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
            f"{BASE_URL}/api/team",
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
                f"{BASE_URL}/api/team/{team_ids[t_idx]}",
                json=data,
                headers={"Content-Type": "application/json"},
            )
            assert response.status_code == 201

    # Create game with a kitty size of 4 cards.
    response = requests.post(
        f"{BASE_URL}/api/game?kitty_size=4",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 201
    r_data = json.loads(response.text)
    game_id = r_data["game_id"]
    print(f"Created game {game_id}")

    # Create round.
    response = requests.post(
        f"{BASE_URL}/api/game/{game_id}/round",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 201
    r_data = json.loads(response.text)
    round_id = r_data["round_id"]

    # Attach teams to the new round.
    data = team_ids
    response = requests.post(
        f"{BASE_URL}/api/round/{round_id}",
        json=data,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 201

    # Start the game.
    response = requests.post(f"{BASE_URL}/api/round/{round_id}/start")

    return game_id, player_ids


class TestSelectPerson:
    driver = []
    handles = {}

    def setup_class(self):
        # t_options = webdriver.FirefoxOptions()
        # t_options = webdriver.ChromeOptions()
        # t_options.headless = False
        for seq in range(4):
            driver = webdriver.Remote(
                # command_executor=f"{G_SELENIUM_STANDALONE_URI}{seq+1}",
                command_executor=G_SELENIUM_HUB_URL,
                desired_capabilities={"browserName": choice(G_BROWSER_LIST)},
                # desired_capabilities={"browserName": G_BROWSER_LIST[0]},
                # options=t_options,
            )
            self.driver.append(driver)

    def teardown_class(self):
        for driver in self.driver:
            driver.quit()

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
        response = requests.get(f"{BASE_URL}/api/player")
        print(f"{response.text=}")
        assert response.status_code == 200
        assert response.text
        # This is a JSON formatted STRING
        response_str = response.text
        response_data = json.loads(response_str)
        print(f"{response_str=}")
        print(f"{response_data=}")
        player_names = {
            i.get("player_id"): i.get("name")
            for i in response_data
            if i.get("player_id") in player_id_list
        }
        assert len(player_names) == 4
        return player_names

    def test_050_start_browsers(self):
        """
        Navigate to the BASE_URL
        """
        global g_game_id, g_players, g_player_ids
        # Create new game.
        print("Creating new game.")
        g_game_id, g_player_ids = setup_new_game()

        g_players = self.retrieve_player_names(g_player_ids)
        assert len(g_players) == len(g_player_ids)

        assert self.driver
        for t_driver in self.driver:
            t_driver.get(f"{BASE_URL}/")

    def test_100_browser_wait(self):
        """
        Wait for the basic page to be rendered.
        """
        assert len(g_players) > 0
        assert len(g_player_ids) > 0
        assert len(g_players) == len(g_player_ids)

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
                    print(f"Browser {self.driver.index(driver)} succeeded.")
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

    def test_120_browser_find_game(self):
        """
        Locate the game buttons
        """
        print(f"Looking for game id: {g_game_id}")
        assert self.driver
        t_drivers = self.driver[:]
        for __ in range(7):  # maximum 20 seconds wait x n iterations
            try:
                for driver in t_drivers:
                    element = WebDriverWait(driver, 5).until(
                        expected_conditions.presence_of_element_located(
                            (By.XPATH, f"//*[@id='{g_game_id}']")
                        )
                    )
                    # element = driver.find_element(By.XPATH, f"//*[@id='{g_game_id}']")
                    assert element
                    element.click()
                    t_drivers.remove(driver)
                print("Selected desired game.")
            except NoSuchElementException as e:
                print("Could not locate desired game.")
                assert not "Could not locate desired game."
                raise NoSuchElementException from e
            except TimeoutException:
                # The UI skips listing games if there's only one in the database.
                print("Caught TimeoutException. Continuing...")
                pass
            if not t_drivers:
                break

    def test_140_browser_wait(self):
        """
        Wait for the list of players to appear.
        """
        for driver in self.driver:
            WebDriverWait(driver, 5).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, "(//*[@id='canvas' and contains(.,'Player:')])")
                )
            )

    def test_150_browser_find_and_click_name(self):
        """
        Locate the player's button corresponding to the sequence of the driver / player_id
        """
        for counter, driver in enumerate(self.driver):
            element = driver.find_element(
                By.XPATH,
                '(//*[@id="canvas" and contains(.,"Player: {}")])'.format(
                    g_players[g_player_ids[counter]]
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
                By.XPATH, f"//*[@id='{g_player_ids[counter]}']"
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
        assert len(g_players) >= len(self.driver)
        for counter, driver in enumerate(self.driver):
            print(f"Looking for player {g_players[g_player_ids[counter]]}.")
            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[@id='player_name']/span[not(contains(@style,'visibility: hidden'))]",
                    )
                )
            )
            print(f"Player {g_players[g_player_ids[counter]]} found.")

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
        global g_driver_bid_winner

        loop_limit = 0
        t_player_ids = deepcopy(g_player_ids)
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
                        g_driver_bid_winner = counter
                    else:
                        # Pass button
                        bid_button = driver.find_element(
                            By.XPATH, "/html/body/div[3]/div[3]/button[2]",
                        )
                    # Record that this player has bid or passed.
                    t_player_ids[counter] = "blank"
                    bid_button.click()
            loop_limit += 1
        assert g_driver_bid_winner >= 0
        print(f"Driver array index = {g_driver_bid_winner}")
        print(f"Bid winner = {g_players[g_player_ids[g_driver_bid_winner]]}")

    def test_210_bury_cards_and_select_trump(self):
        """
        Bury cards and select trump suit.
        """
        # Wait for the cards from the kitty to be added to the player's hand.
        driver = self.driver[g_driver_bid_winner]
        WebDriverWait(driver, 15).until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, "//*[contains(@id,'player11')]")
            )
        )

        # Choose a trump suit.
        declared_trump = choice(SUITS)  # Chrome-Works, Edge-Works
        declared_trump = declared_trump.lower().rstrip("s")
        # In Firefox, only 'spade' works due to the displacement between where Firefox
        # displays the glyph and where it shows the glyph being positioned in the
        # developer utility / programmatically.
        # declared_trump = "spade"  # FF-Works
        # declared_trump = "heart" # FF-Broken
        # declared_trump = "club" # FF-Broken
        # declared_trump = "diamond" # FF-Broken

        trump_dialog = driver.find_element(By.CLASS_NAME, "brython-dialog-title")
        card_elements = driver.find_elements(By.XPATH, "//*[contains(@id,'player')]")
        card_ids = [
            x.get_attribute("id") for x in card_elements if x.get_attribute("href")
        ]

        try:
            while driver.find_element(
                By.XPATH, "/html/body/div[3]/*[contains(.,'Select Trump Suit')]",
            ):
                assert card_ids
                t_id = choice(card_ids)
                print(f"Attempting to move {t_id}")
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
                    except WebDriverException as e:
                        print(f"Ignoring exception: {e}")
                        # pass
        except NoSuchElementException:
            # This is expected when the dialog box disappears.
            pass
        except IndexError:
            # We ran out of cards to try.
            assert False

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
            # Create associations between drivers and the list of cards.
            for driver in self.driver:
                t_cards = driver.find_elements(
                    By.XPATH, "//*[@id='canvas']/*[contains(@id, 'player')]"
                )
                t_cards = [x for x in t_cards if "button" not in x.get_attribute("id")]
                if not t_cards:
                    keep_going = False
                    break
                print("Choosing from ")
                print(", ".join(x.get_attribute("id") for x in t_cards))

                # Choose a random card, click on it, and remove it from consideration
                t_card = choice(t_cards)
                print(f"Moving {t_card.get_attribute('id')}")

                # Drag the card up a sufficient amount.
                webdriver.ActionChains(driver).drag_and_drop_by_offset(
                    t_card, 0, -200
                ).perform()

            for driver in self.driver:
                try:
                    # Acknowledge to continue playing
                    t_dialog = driver.find_element(
                        By.XPATH, "//button[text()='Next trick']"
                    )
                    t_dialog.click()
                except NoSuchElementException:
                    pass

    # def test_900_delete_game(self):
    #     response = requests.delete(f"{BASE_URL}/game/{g_game_id}")
    #     assert response.status_code == 200

    def test_990_sleep(self):
        """
        Sleep at the end so interaction with the browsers is possible.
        """
        print("\nSleeping...")
        time.sleep(0.5)
