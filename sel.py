from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import time

# Need to set an environment variable to set headless window size
# os.environ['MOZ_HEADLESS_WIDTH'] = '1920'
# os.environ['MOZ_HEADLESS_HEIGHT'] = '1080'

# options = Options()
# options.headless = True

# options.set_preference("browser.download.folderList", 2)
# options.set_preference("browser.download.manager.showWhenStarting", False)
# options.set_preference("browser.download.panel.shown", False)
# options.set_preference("browser.download.dir", os.getcwd())
# options.set_preference("browser.helperApps.neverAsk.openFile", "application/pdf")
# options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")

# driver = webdriver.Firefox(options=options)


# Try Chrome
options = Options()
options.add_argument("--disable-extensions")
options.add_argument("--window-size=1920,1080")
options.add_experimental_option("prefs", {
    "profile.default_content_settings.popups": 0,
    "download.prompt_for_download": False,
    "download.default_directory": os.getcwd(),
    "download.directory_upgrade": True})

options.headless = True
# options.add_argument("--headless")

driver = webdriver.Chrome(options=options)



driver.maximize_window()
driver.set_window_size(1920, 1080)

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

document_list = ['AD',
    'CD',
    'HD',
    # 'DK',
    # 'UT',
    # 'VÖ',
    'SI']

for doc_type in document_list:
    print(f"Getting document {doc_type}")

    ad_link = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.XPATH, f"//a[span[contains(text(), '{doc_type}')]]"))
)
    ad_link.click()


    download_button = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//button[@id='form:kostenpflichtigabrufen']")))
    download_button.click()

    time.sleep(5)

    driver.back()

# TODO make work for headless
# TODO see if ChromeDriver works smoother

# TODO get all the files

# TODO move all the files to a subfolder when done

# time.sleep(20)

open("output.html", "w").write(driver.page_source)

driver.quit()
