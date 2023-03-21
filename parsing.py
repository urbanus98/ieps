
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import validators
import requests
from canonisation import canonize_url
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json

chrome_options = Options()
chrome_options.add_argument('ignore-certificate-errors')
chrome_options.add_argument("--headless")
chrome_options.add_argument("user-agent=fri-wier-spiky_goldfish")
driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)


# url = 'https://siol.net/trendi/svet-znanih/mlada-spanska-princesa-mora-za-tri-leta-v-vojsko-601707'
url = 'https://www.e-prostor.gov.si/podrocja/drzavni-koordinatni-sistem/drugo/razno/transformacija-v-novi-koordinatni-sistem/'

TIMEOUT = 3
BIN_EXT = [".pdf", ".doc", ".docx", ".ppt", ".pptx"]

found_bins = []

def checkBinary(url):
    for ext in BIN_EXT:
        if url.endswith(ext):
            found_bins.append(ext)
            return True
    return False

def parsePage(status_code, url):

    links = []
    images = []

    print(f"Retrieving '{url}'")

    driver.get(url)
    html = driver.page_source

    # soup = BeautifulSoup(html, 'html.parser')
    # links = soup.find_all('a', href=True)
    
    time.sleep(TIMEOUT)

    # for link in soup.find_all('a', href=True):
    #     href = link["href"]
    #     # print(href)
    #     if href is not None:
    #         if validators.url(href):
    #             print(href)
    #             links.append(canonize_url(href))

    aTags = driver.find_elements(By.TAG_NAME, "a")
    imgs = driver.find_elements(By.TAG_NAME, "img")
  
    for link in aTags:
        href = link.get_attribute("href")
        print(href)
        if href is not None:
            if validators.url(href):
                # print(href)
                links.append(canonize_url(href))
    
    print(len(links))

    for img in imgs:
        src = img.get_attribute("src")
        print(src)
        if src:
            # cut substring after last dot
            ext = src[src.rfind('.'):]
            # print(ext)
            if ext.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp', '.webp']:
                image = {
                    "filename": src,
                    "contentType": ext,
                    "data": [],
                    "accessedTime": datetime.now().isoformat(),
                }
                images.append(image)
            else:
                print(f"Invalid ext: {ext}")

    # try:
        # json_object = json.dumps(res, indent=4)
    
    #     # Writing to sample.json
    #     with open("sample.json", "w") as outfile:
    #         outfile.write(json_object)
    # except:
    #     pass

    return {
            "url": url,
            "htmlContent": html,
            "httpStatusCode": status_code,
            "accessedTime": datetime.now().isoformat(),
            # "domain": parsedUrl.scheme + "://" + parsedUrl.netloc,
            "links": links,
            "images": images,
            "pageType": "HTML"
        }



def main():

    status_code = ""
    try:
        status_code = requests.get(url).status_code
    except Exception as e:
        print(e)
        
    binary = checkBinary(url)

    if binary:
        page = {
            "url": url,
            "htmlContent": "",
            "httpStatusCode": status_code,
            "accessedTime": datetime.now().isoformat(),
            # "domain": parsedUrl.scheme + "://" + parsedUrl.netloc,
            "pageType": "BINARY",
            "pageData": [
                {
                    "dataTypeCode": found_bins
                }
            ]
        }
    else:
        try:
            page = parsePage(status_code, url)
        except Exception as e:
            print(f"Exception: '{e}'")
            page = {
                "url": url,
                "htmlContent": "",
                "httpStatusCode": status_code,
                "accessedTime": datetime.now().isoformat(),
                # "domain": parsedUrl.scheme + "://" + parsedUrl.netloc,
                "pageType": "INVALID"
            }
            
        json_data = json.dumps(page)
