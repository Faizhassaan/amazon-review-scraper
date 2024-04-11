from bs4 import BeautifulSoup, SoupStrainer
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from amazoncaptcha import AmazonCaptcha
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

port=5000
# Initialize Chrome WebDriver with headless option
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--headless")
driver_path = ChromeDriverManager().install()
driver = webdriver.Chrome(service=Service(executable_path=driver_path), options=chrome_options)


baseURL = ''

# Utility Functions
def getIMG(container):
    try:
        return container.find("div", {"id": "imgTagWrapperId"}).findNext()['src']
    except:
        return ''

def getTitle(container):
    try:
        return container.find("span", {"id": "productTitle"}).text
    except:
        return ''

def getID(baseURL):
    try:
        index = baseURL.find('/dp/')
        return baseURL[index + 4:index + 14]
    except:
        return 0

def getExtension(baseURL):
    try:
        check = ''
        for index in range(0, len(baseURL)):
            if index > 7:
                if baseURL[index] == '/':
                    break
                else:
                    check = check + baseURL[index]
        return check
    except:
        return 0

# Fetch HTML Content from the given link using Selenium
def getHTMLContent(url):
    try:
        driver.get(url)
        while True:
            try:
                # Check if captcha element is present
                captcha_element = driver.find_element(By.XPATH, "//div[@class = 'a-row a-text-center']//img")
                
                # If captcha element is found, solve captcha
                link = captcha_element.get_attribute('src')
                captcha = AmazonCaptcha.fromlink(link)
                captcha_value = AmazonCaptcha.solve(captcha)
                input_field = driver.find_element(By.ID, "captchacharacters")
                input_field.clear()  # Clear input field before sending keys
                input_field.send_keys(captcha_value)
                button = driver.find_element(By.CLASS_NAME, "a-button-text")
                button.click()
                
                # Wait for captcha element to become stale or invisible
                WebDriverWait(driver, 10).until(EC.staleness_of(captcha_element))
                
                # Wait for any AJAX requests or page reloads to settle
                time.sleep(2)
            except NoSuchElementException:
                # Captcha element not found, break out of the loop
                break

        # Captcha solved or not found, proceed to get HTML content
        html_content = driver.page_source
        strainer = SoupStrainer("div", {"id": "ppd"})
        soup = BeautifulSoup(html_content, "lxml", parse_only=strainer)
        return soup
    except Exception as e:
        print("Error:", e)
        return None
    
    # finally:
    #     driver.quit()

def parseHTML(HTML, url):
    data = []
    if HTML != 0:
        try:
            product = {
                'id': getID(url),
                'baseURL': getExtension(url),
                'title': getTitle(HTML),
                'imgSrc': getIMG(HTML),
            }
            data.append(product)
            return data
        except:
            return 0
    else:
        return 0

def Main(url):
    HTML = getHTMLContent(url)
    return parseHTML(HTML, url)