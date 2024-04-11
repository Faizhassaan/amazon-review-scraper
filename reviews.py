# import modules
import random as random
from bs4 import BeautifulSoup, SoupStrainer
import pandas as pd 
import csv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urlparse
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
        return container.find('div',class_='a-row').find('div',class_='a-profile-content').text
    except:
        return None
        
def getTitle(container):
    try:
        res=container.find('span',class_='review-title-content')
        return container.find('a',class_='review-title-content').text if res == None else res.text
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

def get_product_id(url):
    try:
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split('/')
        id_index = path_segments.index('dp') + 1
        return path_segments[id_index]
    except ValueError:
        return None

def getLink(container,obj):
    return f"https://{obj['url']}{container.find('a')['href']}"

def get_number_of_reviews(obj, driver):
    try:
        parsed_url = urlparse(obj['url'])
        base_url = parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path
        product_url = base_url.split('/dp/')[0]
        url = f"{product_url}/product-reviews/{obj['id']}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews&pageNumber=1"
        print(url)
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

                # Check if the page has loaded completely
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "filter-info-section")))

                # Wait for any AJAX requests or page reloads to settle
                time.sleep(2)

                break  # Exit the loop once captcha is solved and the page has loaded completely

            except NoSuchElementException:
                # Captcha element not found, break out of the loop
                break

        strainer = SoupStrainer("div",{"id":"filter-info-section"})
        soup = BeautifulSoup(driver.page_source, "lxml",parse_only=strainer)
        text = soup.text
        numbers = ''
        for char in text:
            if char.isdigit():
                numbers += char
        return numbers
    except Exception as e:
        print("Error:", e)
        return '0'

# Fetch HTML Content from the given link
def getHTMLContent(obj, page, driver):
    try:
        parsed_url = urlparse(obj['url'])
        base_url = parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path
        product_url = base_url.split('/dp/')[0]
        url = f"{product_url}/product-reviews/{obj['id']}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews&pageNumber={page}"
        print(url)
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

                # Check if the page has loaded completely
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "filter-info-section")))

                # Wait for any AJAX requests or page reloads to settle
                time.sleep(2)

                break  # Exit the loop once captcha is solved and the page has loaded completely

            except NoSuchElementException:
                # Captcha element not found, break out of the loop
                break

        soup = BeautifulSoup(driver.page_source, "lxml")
        return soup
    except Exception as e:
        print("Error:", e)
        return None

def parseHTML(HTML,obj):
    data=[]
    if HTML is not None:
        try:
            mainDiv = HTML.findAll('div',class_='aok-relative')
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


def Main(url):
    # Extract product ID from the URL
    product_id = get_product_id(url)
    if product_id is None:
        print("Error: Unable to extract product ID from the URL.")
        return None

    # Create obj with extracted URL and product ID
    obj = {'url': url, 'id': product_id}
    pageData = []
    pages = 15  # Iterate over 6 pages specifically
    
    option = webdriver.ChromeOptions()
    # option.add_argument("--headless=new")
    driver_path = ChromeDriverManager().install()
    driver = webdriver.Chrome(service=Service(executable_path=driver_path), options=option)
    
    num = int(get_number_of_reviews(obj, driver))
    if num > 10:
        if isinstance(num / 10, float):
            pages = int(num / 10) + 1
        else:
            pages = num / 10
    
    if pages > 0:
        for i in range(1, min(pages, 15) + 1):  # Iterate up to 6 pages or total available pages, whichever is minimum
            HTML = getHTMLContent(obj, i, driver)
            res = parseHTML(HTML, obj)
            pageData.extend(res)  # Extend the pageData list with the data from each page
    
    # Write the data to a CSV file
    filename = input("Enter the CSV filename to save the data: ")
    if not filename.endswith('.csv'):
        filename += '.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['username', 'vp', 'title', 'review', 'link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in pageData:
            writer.writerow(item)
    print(f"Your data is saved in '{filename}'")
    
    driver.quit()
    return pageData

# Example usage:
URL = input("Enter Amazon Product Link : ")
result = Main(URL)
print(result)
