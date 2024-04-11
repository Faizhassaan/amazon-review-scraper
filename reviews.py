# import modules
import random as random
from bs4 import BeautifulSoup, SoupStrainer
import pandas as pd 
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from amazoncaptcha import AmazonCaptcha
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from googletrans import Translator
import time

translator = Translator()

# Utility Functions 

def getName(container):
    try:
        return container.find('div',class_='a-row a-spacing-none').find('div',class_='a-profile-content').text
    except:
        return None
        
def getTitle(container):
    try:
        res=container.find_all('div', {'data-hook': 'review-title'})
        return container.find('a',class_='a-size-base a-link-normal review-title a-color-base review-title-content a-text-bold').text if res == None else res.text
    except:
        return None

def getStatus(container):
    try:
        return 1
    except:
        return None

def checkLang(text):
    try:
        return translator.detect(text).lang
    except:
        return 'en'

def getReview(container,obj):
    try:
        main=container.find('div',class_='a-spacing-small')
        return {'Text':main.text,'lang':checkLang(main.text)}
    except:
        return None

def getLink(container,obj):
    return f"https://{obj['url']}{container.find('a')['href']}"

def get_number_of_reviews(obj):
    temp = ''
    numbers = ''
    try:
        parsed_url = urlparse(obj['url'])
        base_url = parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path

        # Extract the desired part before the /dp/ segment
        product_url = base_url.split('/dp/')[0]

        # Construct the new URL with /product-reviews/ instead of /dp/
        url = f"https{product_url}/product-reviews/{obj['id']}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews&pageNumber=1"

        print(url)
        
        port = 5000
        option = webdriver.ChromeOptions()
        # option.add_argument("--headless=new")
        driver_path = ChromeDriverManager().install()
        driver = webdriver.Chrome(service=Service(executable_path=driver_path), options=option)
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

        # logic
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "filter-info-section"))
        )
        text = element.text
        for char in text:
            if char != ' ' and char != '\n':
                temp = temp + char
            for index in range(0, len(temp)):
                if index > temp.find('ratings,') + 7:
                    if temp[index] != 'w':
                        numbers = numbers + temp[index]
                    else:
                        break
        return numbers.replace(',', '')
    except Exception as e:
        print("Error:", e)
        return 0
    # finally:
    #     driver.quit()

# Fetch HTML Content from the given link
def getHTMLContent(obj, page):
    try:
        parsed_url = urlparse(obj['url'])
        base_url = parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path

        # Extract the desired part before the /dp/ segment
        product_url = base_url.split('/dp/')[0]
        # Construct the new URL with /product-reviews/ instead of /dp/
        url = f"https{product_url}/product-reviews/{obj['id']}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews&pageNumber={page}"
        print(url)
        port = 5000
        option = webdriver.ChromeOptions()
        # option.add_argument("--headless=new")
        driver_path = ChromeDriverManager().install()
        driver = webdriver.Chrome(service=Service(executable_path=driver_path), options=option)
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
        strainer = SoupStrainer("div", {"id": "cm_cr-review_list"})
        soup = BeautifulSoup(driver.page_source, "lxml", parse_only=strainer)
        return soup

    except Exception as e:
        print("Error:", e)
        return None

    # finally:
    #     driver.quit()

def parseHTML(HTML,obj):
    data=[]
    if HTML is not None:
        try:
            mainDiv = HTML.findAll('div',class_='a-section review aok-relative')
            for container in mainDiv:
                data.append({
                "username": getName(container),
                "vp": getStatus(container),
                "title": getTitle(container),
                "review": getReview(container,obj),
                "link": getLink(container,obj),
            })

            return data
        except:
            return None
    else:
        return None


def Main(obj):
    # obj = { 'url': 'www.example.com', 'id': 'B*******' }
    pageData = []
    pages = 1

    try:
        num = int(get_number_of_reviews(obj))
    except ValueError:
        # Handle the case where get_number_of_reviews returns a non-integer value
        num = 0

    if num > 10:
        if isinstance(num / 10, float):
            pages = int(num / 10) + 1
        else:
            pages = num / 10
    
    if pages > 0:
        for i in range(1, pages + 1):
            HTML = getHTMLContent(obj, i)  
            res = parseHTML(HTML, obj)
            pageData.append(res)
            print(f"Page {i} Data: {res}")
           
    return pageData