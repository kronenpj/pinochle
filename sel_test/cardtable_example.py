"""
Test the cardtable brython application.
"""

# import sys
# from time import sleep

# import pytest
# import pytest_selenium

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.firefox.options import Options
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support.expected_conditions import presence_of_element_located


# def test_google(app, selenium):
#     selenium.get("http://ryzen.phenom.n2kiq.dyndns.org:5000/")
#     logo = selenium.find_element_by_id("hplogo")
#     assert logo.get_attribute("title") == "Google"

# def find_service(app, selenium):
    # with app.test_client() as test_client:
        # test_client.


#This example requires Selenium WebDriver 3.13 or newer
# with webdriver.Firefox() as driver:
#     options = Options()
#     options.headless = True
#     driver = webdriver.Firefox(options=options)

#     wait = WebDriverWait(driver, 10)
#     driver.get("https://google.com/ncr")
#     driver.find_element(By.NAME, "q").send_keys("cheese" + Keys.RETURN)
#     first_result = wait.until(presence_of_element_located((By.CSS_SELECTOR, "h3>div")))
#     print(first_result.get_attribute("textContent"))
  
    # # Navigate to url
    # driver.get("http://www.example.com")
    # driver.add_cookie({"name": "test1", "value": "cookie1"})
    # driver.add_cookie({"name": "test2", "value": "cookie2"})

    # # Deletes all cookies
    # driver.delete_all_cookies()

    # # Store 'google search' button web element
    # searchBtn = driver.find_element(By.LINK_TEXT, "Sign in")

    # # Perform click-and-hold action on the element
    # webdriver.ActionChains(driver).click_and_hold(searchBtn).perform()

    # # Performs release event
    # webdriver.ActionChains(driver).release().perform()

    # # Store 'google search' button web element
    # gmailLink = driver.find_element(By.LINK_TEXT, "Gmail")
    # #Set x and y offset positions of element
    # xOffset = 100
    # yOffset = 100
    # # Performs mouse move action onto the element
    # webdriver.ActionChains(driver).move_by_offset(xOffset,yOffset).perform()

    # # Store 'box A' as source element
    # sourceEle = driver.find_element(By.ID, "draggable")
    # # Store 'box B' as source element
    # targetEle  = driver.find_element(By.ID, "droppable")
    # # Performs drag and drop action of sourceEle onto the targetEle
    # webdriver.ActionChains(driver).drag_and_drop(sourceEle,targetEle).perform()

    # # Store 'box A' as source element
    # sourceEle = driver.find_element(By.ID, "draggable")
    # # Store 'box B' as source element
    # targetEle  = driver.find_element(By.ID, "droppable")
    # targetEleXOffset = targetEle.location.get("x")
    # targetEleYOffset = targetEle.location.get("y")

    # # Performs dragAndDropBy onto the target element offset position
    # webdriver.ActionChains(driver).drag_and_drop_by_offset(sourceEle, targetEleXOffset, targetEleYOffset).perform()
