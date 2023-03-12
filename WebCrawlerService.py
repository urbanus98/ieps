import platform
from urllib.parse import urlparse

from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import requests
import json
import os
import time
import re


class MyWebScraper:

    WEB_DRIVER_LOCATION = None
    TIMEOUT = 5

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

        """
        Returns the sitemap host if it is present in the page source code, otherwise returns None.
        """
        sitemap_host = None
        page_source = driver.page_source
        match = re.search('<sitemapindex.*?>\s*<sitemap>\s*<loc>(.*?)</loc>\s*<lastmod>(.*?)</lastmod>', page_source,
                          re.DOTALL | re.IGNORECASE)
        if match:
            sitemap_host = match.group(1)
        return sitemap_host

    def get_sitemap_content(self, sitemap_host):

        """
        Returns the content of the sitemap if it is present, otherwise returns None.
        """
        sitemap_content = None
        if sitemap_host:
            response = requests.get(sitemap_host)
            if response.status_code == 200:
                sitemap_content = response.text
        return sitemap_content

    def get_robots_content(self, driver):

        """
        Returns the content of the robots.txt file if it is present, otherwise returns None.
        """
        robots_content = None
        page_source = driver.page_source
        match = re.search('<a.*?href="(.*?/robots.txt)".*?>', page_source, re.IGNORECASE)
        if match:
            robot_url = match.group(1)
            response = requests.get(robot_url)
            if response.status_code == 200:
                robots_content = response.text

        return robots_content

    def check_robot_txt(self, driver):

        """
         Checks if the site can be crawled based on the robots.txt file and returns the delay and allowance if present, otherwise returns None.
        """

        robot_delay = None
        robot_allowance = None
        page_source = driver.page_source
        match = re.search('<a.*?href="(.*?/robots.txt)".*?>', page_source, re.IGNORECASE)
        if match:
            robot_url = match.group(1)
            response = requests.get(robot_url)
            if response.status_code == 200:
                robots_content = response.text
                lines = robots_content.split('\n')
                for line in lines:
                    if line.startswith('User-agent: *'):
                        parts = line.split(':')
                        if len(parts) > 1:
                            robot_allowance = parts[1].strip()
                    elif line.startswith('Crawl-delay: '):
                        parts = line.split(':')
                        if len(parts) > 1:
                            robot_delay = parts[1].strip()

        return robot_delay, robot_allowance

    def main(self, url):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=fri-ieps-TEST')

        driver_service = Service(self.WEB_DRIVER_LOCATION)
        driver_service.start()

        driver = webdriver.Chrome(service=driver_service, options=options)

        driver.get(url+"robots.txt")

        time.sleep(self.TIMEOUT)

        domain = urlparse(url).netloc

        # Extract sitemap host
        sitemap_host = self.get_sitemap_host(driver)

        # Extract sitemap content
        sitemap_content = self.get_sitemap_content(sitemap_host)

        # Extract robots content
        robots_content = self.get_robots_content(driver)

        # Check for URLs and page content
        page_content = driver.page_source
        urls = re.findall('''href=["'](.[^"']+)["']''', page_content)

        # Check robot.txt for crawling allowances and specific delay
        robot_delay, robot_allowance = self.check_robot_txt(driver)

        #Ta shit bo posiljal na frontier stvari amapk ne dela k nimamo se frontirja
        #data = {'message': html}
        #frontier_url = 'http://localhost:5000/extract'
        #headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        #response = requests.post(frontier_url, data=json.dumps(data), headers=headers)

        driver.quit()

        result = {
            'domain': domain,
            'sitemap_host': sitemap_host,
            'sitemap_content': sitemap_content,
            'robots_content': robots_content,
            'urls': urls,
            'page_content': page_content,
            'robot_delay': robot_delay,
            'robot_allowance': robot_allowance
        }

        print(result)

        return result

if __name__ == '__main__':
    scraper = MyWebScraper()
    scraper.start()
