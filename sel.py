from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import time

options = Options()
# options.headless = True

options.set_preference("browser.download.folderList", 2)
options.set_preference("browser.download.manager.showWhenStarting", False)
options.set_preference("browser.download.panel.shown", False)
options.set_preference("browser.download.dir", os.getcwd())
options.set_preference("browser.helperApps.neverAsk.openFile", "application/pdf")
options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")

driver = webdriver.Firefox(options=options)
driver.maximize_window()
driver.get("https://www.handelsregister.de")


link = driver.find_element(By.LINK_TEXT, "Advanced search")
link.click()

print(driver.title)

company_textarea = driver.find_element(
    By.XPATH, "//textarea[@id='form:schlagwoerter']"
).send_keys("Gasag AG")

exact_radio = driver.find_element(By.XPATH, "//label[@for='form:schlagwortOptionen:2']")
exact_radio.click()

print(exact_radio)


search_button = driver.find_element(By.XPATH, "//button[@id='form:btnSuche']")
search_button.click()

ad_link = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.XPATH, "//a[span[contains(text(), 'AD')]]"))
)
ad_link.click()

download_button = driver.find_element(
    By.XPATH, "//button[@id='form:kostenpflichtigabrufen']"
)
download_button.click()

# TODO make work for headless
# TODO see if ChromeDriver works smoother

# TODO get all the files

# TODO move all the files to a subfolder when done

time.sleep(20)

open("output.html", "w").write(driver.page_source)

driver.quit()
