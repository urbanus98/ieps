import platform
from urllib.parse import urlparse
from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import requests
import os
import time
from datetime import datetime
import re
import xml.etree.ElementTree as ET
from robotexclusionrulesparser import RobotExclusionRulesParser
from canonisation import canonize_url
import validators
import hashlib

class MyWebScraper:

    WEB_DRIVER_LOCATION = None
    TIMEOUT = 1
    BIN_EXT = [".pdf", ".doc", ".docx", ".ppt", ".pptx"]
    found_bin = ""
    seen_html = "bbbfc734d8c3114e10d60ef347b043c7"


    def __init__(self):
        self.app = Flask("MyWebScraper")
        self.app.route('/scrape', methods=['POST'])(self.scrape)
        if not MyWebScraper.WEB_DRIVER_LOCATION:
            MyWebScraper.WEB_DRIVER_LOCATION = self.find_chromedriver()

    def start(self):
        self.app.run()

    def scrape(self):
        input_value = request.form['message']
        return self.main(input_value)

    def find_chromedriver(self):
        # put chromedriver in the same directory as this file, and the path will be found
        cwd = os.getcwd()
        system = platform.system()

        if system == 'Windows':
            for root, dirs, files in os.walk(cwd):
                for file in files:
                    if file == "chromedriver.exe":
                        chromedriver_path = os.path.join(root, file)
                        return chromedriver_path
        elif system == 'Darwin':
            for root, dirs, files in os.walk(cwd):
                for file in files:
                    if file == "chromedriver_mac":
                        chromedriver_path = os.path.join(root, file)
                        return chromedriver_path
        elif system == 'Linux':
            for root, dirs, files in os.walk(cwd):
                for file in files:
                    if file == "chromedriver_linux":
                        chromedriver_path = os.path.join(root, file)
                        return chromedriver_path
        return None

    def get_sitemap_host(self, driver):
        sitemap_host = None
        page_source = driver.page_source
        match = re.search(r'^\s*Sitemap:\s*(.*)', page_source,
                          re.DOTALL | re.IGNORECASE | re.MULTILINE)

        if match:
            sitemap_host = match.group(1)

        sub_str = ".xml"

        # remove everything after the .xml
        if sitemap_host and sub_str in sitemap_host:
            sitemap_host = sitemap_host[:sitemap_host.index(sub_str) + len(sub_str)]

        return sitemap_host

    def get_sitemap_content(self, sitemap_host):

        if sitemap_host:
            response = requests.get(sitemap_host)
            if response.status_code != 200:
                print('Error: ' + str(response.status_code))
                sitemap_content = "Error: " + str(response.status_code)
                return sitemap_content
            else:

                root = ET.fromstring(response.content)
                urls = []

                #pars the xml file
                for child in root:
                    for url in child:
                        # print(url.text)
                        if ".xml" in url.text:
                            response2 = requests.get(url.text)
                            root2 = ET.fromstring(response2.content)
                            for child2 in root2:
                                for url2 in child2:
                                    if "http" in url2.text:
                                        urls.append(url2.text)
                                        # print(url2.text)
                return urls
        else:
            return ''

    def check_robot_txt(self, driver):

        robot_delay = None

        robots_url = driver.current_url.rstrip('/') + '/robots.txt'

        # Parse the robots.txt file
        rp = RobotExclusionRulesParser()
        rp.fetch(robots_url)
        # Check if the user agent is allowed to crawl the website
        try:
            rp.is_allowed('*', driver.current_url)
            print('User agent is allowed to crawl the website')
            robot_allowance = "User agent is allowed to crawl the website"
        except Exception as ex:
            print('User agent is not allowed to crawl the website')
            print(ex)

        # Get the crawl delay for the user agent
        crawl_delay = rp.get_crawl_delay('*')
        if crawl_delay is not None:
            robot_delay = crawl_delay

        return robot_delay, robot_allowance

    def parse_links(self, aTags):
        links = []
        for link in aTags:
            href = link.get_attribute("href")
            if href is not None:
                if validators.url(href):
                    # print(href)
                    links.append(canonize_url(href))
        return links

    def parse_img(self, imgs):
        images = []
        for img in imgs:
            src = img.get_attribute("src")
            # print(src)
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
        return images

    def checkBinary(self, url):
        for ext in self.BIN_EXT:
            # if ext in url: # maybe better
            if url.endswith(ext):
                self.found_bin = ext
                return True
        return False

    def hash_html(self, html_content):
        html_hash = hashlib.md5(html_content.encode('utf-8')).hexdigest()
        return html_hash

    def main(self, url):

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=fri-ieps-Lt-Colonel-Kilgore-team')

        driver_service = Service(self.WEB_DRIVER_LOCATION)
        driver_service.start()

        driver = webdriver.Chrome(service=driver_service, options=options)

        driver.get(url+"robots.txt")


        time.sleep(self.TIMEOUT)

        domain = urlparse(url).netloc


        sitemap_host = self.get_sitemap_host(driver)

        
        sitemap_content = self.get_sitemap_content(sitemap_host)


        robot_delay, robot_allowance = self.check_robot_txt(driver)

        result_robot = {
            'domain': domain,
            'sitemap_host': sitemap_host,
            'robot_delay': robot_delay,
            'robot_allowance': robot_allowance,
            'sitemap_content': sitemap_content,
        }

        # print(result_robot)

        status_code = ""
        try:
            status_code = requests.get(url).status_code
        except Exception as e:
            print(e)


        if self.checkBinary(url):
            result_parse = {
                'url': url,
                'html': "",
                'httpStatusCode': status_code,
                'accessedTime': datetime.now().isoformat(),
                'pageType': "BINARY",
                'pageTypeCode': self.found_bin
            }
        else:

            driver.get(url)

            aTags = driver.find_elements(By.TAG_NAME, "a")
            imgs = driver.find_elements(By.TAG_NAME, "img")
            html = driver.page_source

            links = self.parse_links(aTags)
            img = self.parse_img(imgs)

            html_hash = self.hash_html(html)

            if html_hash == self.seen_html:
                print("Already seen this html")
                return

            result_parse = {
                'url': url,
                'html': html,
                'img': img,
                'links': links,
                'pageType': "HTML",
                'httpStatusCode': status_code,
                'accessedTime': datetime.now().isoformat(),
            }

        # print(result_parse)
        # print(html_hash)

        driver.quit()

        # Ta shit bo posiljal na frontier stvari amapk ne dela k nimamo se frontirja

        # data = {'message': html}
        # frontier_url = 'http://localhost:5000/extract'
        # headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        # response = requests.post(frontier_url, data=json.dumps(data), headers=headers)

        return result_robot, result_parse

if __name__ == '__main__':
    scraper = MyWebScraper()
    scraper.start()
