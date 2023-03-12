import platform
from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import requests
import json
import os
import time



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

        html = driver.page_source


        #Ta shit bo posiljal na frontier stvari amapk ne dela k nimamo se frontirja
        #data = {'message': html}
        #frontier_url = 'http://localhost:5000/extract'
        #headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        #response = requests.post(frontier_url, data=json.dumps(data), headers=headers)

        driver.quit()

        return html

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


if __name__ == '__main__':
    scraper = MyWebScraper()
    scraper.start()
