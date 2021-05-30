# Generated by Selenium IDE
import json
import time
from copy import deepcopy
from random import choice

import requests
from selenium import webdriver
from selenium.common.exceptions import (
    MoveTargetOutOfBoundsException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from pinochle.cards.const import SUITS

# G_BROWSER = "firefox"
G_BROWSER = "chrome"
# G_BROWSER = "MicrosoftEdge"
g_player_ids = []
g_player_names = []
BASE_URL = "http://172.16.42.10:5000"
# For some reason placing this in the class causes stores values to be lost.
g_driver_bid_winner = -1


def retrieve_player_ids():
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/player' page is requested (POST)
    THEN check that the response is a UUID and contains the expected information
    """
    response = requests.get(f"{BASE_URL}/api/player")
    # print(f"{response.text=}")
    assert response.status_code == 200
    assert response.text
    # This is a JSON formatted STRING
    response_str = response.text
    response_data = json.loads(response_str)
    # print(f"{response_str=}")
    # print(f"{response_data=}")
    for i in response_data:
        g_player_ids.append(i.get("player_id"))
        g_player_names.append(i.get("name"))
    assert len(g_player_ids) == 4
    assert len(g_player_names) == 4


class TestSelectPerson:
    driver = []
    players = []
    player_ids = []
    vars = {}

    def setup_class(self):
        # print("In TestSelectPerson:setup_class")
        retrieve_player_ids()

        for counter, p_id in enumerate(g_player_ids):
            self.player_ids.append(p_id)
            self.players.append(g_player_names[counter])
        assert self.player_ids == g_player_ids
        assert self.players == g_player_names

        # t_options = webdriver.FirefoxOptions()
        t_options = webdriver.ChromeOptions()
        # t_options.headless = False
        for seq in range(len(self.player_ids)):
            driver = webdriver.Remote(
                # command_executor=f"http://172.16.42.10:444{seq+1}",
                command_executor="http://172.16.42.10:4444",
                desired_capabilities={"browserName": G_BROWSER},
                options=t_options,
            )
            self.driver.append(driver)

    def teardown_class(self):
        for driver in self.driver:
            driver.quit()

    def wait_for_window(self, timeout=2000):
        time.sleep(round(timeout / 1000))
        wh_now = self.driver[len(self.driver)].window_handles
        wh_then = self.vars["window_handles"]
        if len(wh_now) > len(wh_then):
            return set(wh_now).difference(set(wh_then)).pop()

    def test_100_start_browsers(self):
        """
        Navigate to the BASE_URL
        """
        for driver in self.driver:
            driver.get(f"{BASE_URL}/")

    def test_110_browser_wait(self):
        """
        Wait for the basic page to be rendered.
        """
        for driver in self.driver:
            WebDriverWait(driver, 240, poll_frequency=2).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, "(/html/body/div[2]/div[2])")
                )
            )

    def test_130_browser_find_first(self):
        """
        Locate the player buttons
        """
        for driver in self.driver:
            elements = driver.find_elements(
                By.XPATH, "(/html/body/div[2]/div[2]//*[1]/*[1])"
            )
            assert len(elements) > 0

    def test_140_browser_wait(self):
        """
        Wait for the list of players to appear.
        """
        for driver in self.driver:
            WebDriverWait(driver, 120).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, '(//*[@id="canvas" and contains(.,"Player:")])')
                )
            )

    def test_150_browser_find_name(self):
        """
        Locate the player's button corresponding to the sequence of the driver / player_id
        """
        for counter, driver in enumerate(self.driver):
            elements = driver.find_elements(
                By.XPATH,
                '(//*[@id="canvas" and contains(.,"Player: {}")])'.format(
                    self.players[counter]
                ),
            )
            assert len(elements) > 0

    def test_160_browser_click_on_name(self):
        """
        Locate and click on the button corresponding to the player_id in the array.
        """
        assert self.player_ids
        # print(f"player_ids: {self.player_ids}")
        for counter, entry in enumerate(self.player_ids):
            button_element = self.driver[counter].find_element(
                By.XPATH, f"//*[@id='{entry}']"
            )
            webdriver.ActionChains(self.driver[counter]).move_to_element(
                button_element
            ).click().perform()

    def test_170_browser_wait_for_score(self):
        """
        Wait for a specific element to appear indicating a player was chosen.
        """
        for driver in self.driver:
            WebDriverWait(driver, 5).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, "//*[@id='game_status']/span[contains(.,'Score:')]")
                )
            )

    def test_180_check_player_name(self):
        """
        Verify the player name we expect based on the player_id appears.
        """
        for counter, driver in enumerate(self.driver):
            WebDriverWait(driver, 5).until(
                expected_conditions.presence_of_element_located(
                    (
                        By.XPATH,
                        f"//*[@id='player_name']/span[contains(.,'{self.players[counter]}')]",
                    )
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
        global g_driver_bid_winner

        loop_limit = 0
        t_player_ids = deepcopy(self.player_ids)
        t_empty = ["blank" for _ in range(len(t_player_ids))]
        bid_occurred = False

        # print(f"t_empty: {t_empty}")
        while t_player_ids != t_empty and loop_limit < 100:
            # print(f"t_player_ids: {t_player_ids}")
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
        # print(f"Driver array index = {g_driver_bid_winner}")
        # print(f"Bid winner = {self.players[g_driver_bid_winner]}")

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
                # print(f"Attempting to move {t_id}")
                element = driver.find_element(By.ID, t_id)
                assert element

                # Choose another card to be buried.
                try:
                    webdriver.ActionChains(driver).move_to_element(
                        element
                    ).click().perform()
                    card_ids.remove(t_id)
                except MoveTargetOutOfBoundsException as e:
                    # print(f"Caught MTOOBE exception...{e}")
                    card_ids.remove(t_id)
                except WebDriverException as e1:
                    # print(f"Ignoring WDE exception: {e1}")
                    pass

                trump_elements = trump_dialog.find_elements(
                    By.XPATH, f"//*[@id='{declared_trump}']"
                )
                # print(f"Elements found: {len(elements)}")
                for element in trump_elements:
                    # print(f"attribute: {element.get_attribute('id')}")
                    try:
                        webdriver.ActionChains(driver).move_to_element(
                            element
                        ).click().perform()
                    except WebDriverException as e:
                        # print(f"Ignoring exception: {e}")
                        pass
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
            webdriver.ActionChains(driver).move_to_element(
                send_meld_button
            ).click().perform()

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

    def test_990_sleep(self):
        """
        Sleep at the end so interaction with the browsers is possible.
        """
        print("\nSleeping...")
        time.sleep(0.5)
