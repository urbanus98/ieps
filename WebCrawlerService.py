import concurrent
import platform
from flask import Flask, request, jsonify, make_response
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import requests
import os
import time
from datetime import datetime
import re
import xml.etree.ElementTree as Et
from robotexclusionrulesparser import RobotExclusionRulesParser
import validators
import hashlib
import logging
from io import StringIO
from urllib.parse import urlparse, urlunparse
from concurrent.futures import ThreadPoolExecutor



class MyProjectError(Exception):
    """Exception class from which every exception in this library will derive."""
    pass

class VisitedDomainsError(MyProjectError):
    """A specific error for visited domains."""
    pass

class HashesError(MyProjectError):
    """A specific error for fetching hashes."""
    pass

class MyWebScraper:
    AUTH = ("Hanoi", "I_love_the_smell_of_napalm_in_the_morning")

    WEB_DRIVER_LOCATION = None
    TIMEOUT = 5
    BIN_EXT = [".pdf", ".doc", ".docx", ".ppt", ".pptx"]
    found_bin = ""
    FRONTIER_SERVER_URL = 'http://127.0.0.1:8000'


    def __init__(self):
        self.app = Flask("MyWebScraper_number")
        self.app.route('/scrape', methods=['POST'])(self.scrape)
        self.app.route('/logs', methods=['GET'])(self.get_logs)

        self.log_stream = StringIO()
        log_handler = logging.StreamHandler(self.log_stream)
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s\n')
        log_handler.setFormatter(log_formatter)

        # Set up logger
        self.logger = logging.getLogger('web_scraper')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(log_handler)

        if not MyWebScraper.WEB_DRIVER_LOCATION:
            MyWebScraper.WEB_DRIVER_LOCATION = self.find_chromedriver()

    def start(self, host='0.0.0.0', port=5000):
        self.app.run(host=host, port=port)

    def scrape(self):
        input_messages = request.get_json().get('messages', [])
        results = []
        for input_value in input_messages:
            self.logger.info(f'Starting scrape for URL: {input_value}\n')
            result = self.main([input_value])  # Make sure to put the input_value in a list
            results.extend(result)
        return jsonify(results)

    def get_logs(self):
        logs = self.log_stream.getvalue().split('\n')
        logs_html = '<br>'.join(logs)
        response = make_response(logs_html, 200)
        response.mimetype = "text/html"
        return response

    def find_chromedriver(self):
        cwd = os.getcwd()
        system = platform.system()
        chromedriver_file = {
            'Windows': 'chromedriver.exe',
            'Darwin': 'chromedriver',
            'Linux': 'chromedriver',
        }

        if system in chromedriver_file:
            for root, dirs, files in os.walk(cwd):
                if chromedriver_file[system] in files:
                    self.logger.info(f'Found chromedriver at {os.path.join(root, chromedriver_file[system])}\n')
                    return os.path.join(root, chromedriver_file[system])

        return None

    def get_sitemap_host(self, driver):
        sitemap_host = None
        self.logger.info("Getting sitemap host\n")
        page_source = driver.page_source
        match = re.search(r'^\s*Sitemap:\s*(.*)', page_source,
                          re.DOTALL | re.IGNORECASE | re.MULTILINE)

        if match:
            sitemap_host = match.group(1)

        sub_str = ".xml"

        # remove everything after the .xml
        if sitemap_host and sub_str in sitemap_host:
            sitemap_host = sitemap_host[:sitemap_host.index(sub_str) + len(sub_str)]

        self.logger.info(f"Sitemap host: {sitemap_host}\n")
        return sitemap_host

    def get_sitemap_content(self, sitemap_host):
        self.logger.info("Getting sitemap content\n")
        if sitemap_host:
            response = requests.get(sitemap_host)
            if response.status_code != 200:
                self.logger.error(f"Error getting sitemap content: {response.status_code}\n")
                sitemap_content = "Error: " + str(response.status_code)
                return sitemap_content
            else:

                root = Et.fromstring(response.content)
                urls = []

                # pars the xml file
                for child in root:
                    for url in child:
                        # print(url.text)
                        if ".xml" in url.text:
                            response2 = requests.get(url.text)
                            root2 = Et.fromstring(response2.content)
                            for child2 in root2:
                                for url2 in child2:
                                    if "http" in url2.text:
                                        urls.append(url2.text)

                self.logger.info(f"Found URL: {len(urls)}\n")
                return urls
        else:
            self.logger.error("No sitemap host found\n")
            return ''

    def check_robot_txt(self, driver):

        self.logger.info("Checking robot.txt\n")

        robot_delay = None
        robot_allowance = None

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
        self.logger.info(f"Robot.txt allowance: {robot_allowance}\n")

        # Get the crawl delay for the user agent
        crawl_delay = rp.get_crawl_delay('*')
        if crawl_delay is not None:
            robot_delay = crawl_delay

        self.logger.info(f"Robot.txt delay: {robot_delay}\n")

        return robot_delay, robot_allowance

    def parse_links(self, a_tags):
        self.logger.info("Parsing links\n")
        links = []
        print('Parsing links')
        #od tuki naprej se neki sfuka z linki in pol ne dela
        for link in a_tags:
            href = link.get_attribute("href")
            if href is not None and validators.url(href):
                canonized_href = self.canonize_url(href)
                links.append(canonized_href)
        self.logger.info(f"Found {len(links)} links\n")
        return links

    def canonize_url(self, url):
        parsed_url = urlparse(url)
        parsed_url = parsed_url._replace(fragment='', netloc=parsed_url.netloc.lower())
        canonized_url = urlunparse(parsed_url)
        self.logger.info("Canonized URL \n")
        return canonized_url

    def parse_img(self, imgs):
        self.logger.info("Parsing images\n")
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
                    self.logger.error(f"Invalid ext: {ext}\n")
            self.logger.info(f"Found {len(images)} images")
        return images

    def check_binary(self, url):
        self.logger.info("Checking binary\n")
        for ext in self.BIN_EXT:
            # if ext in url: # maybe better
            if url.endswith(ext):
                self.found_bin = ext
                self.logger.info("Found binary\n")
                return True
        self.logger.info("Not binary\n")
        return False

    def hash_html(self, html_content):
        self.logger.info("Hashing html\n")
        return hashlib.md5(html_content.encode('utf-8')).hexdigest()

    def get_visited_domains(self):
        self.logger.info("Getting visited domains\n")
        response = requests.get(f'{self.FRONTIER_SERVER_URL}/visited_domains\n')
        if response.status_code == 200:
            self.logger.info("Got visited domains\n")
            return set(response.json()['visited_domains'])
        else:
            self.logger.error(f"Error: Failed to fetch visited domains. Status code: {response.status_code}\n")
            raise  VisitedDomainsError(f"Error: Failed to fetch visited domains. Status code: {response.status_code}")

    def get_hashes_from_frontier(self):
        self.logger.info("Getting hashes from frontier\n")
        response = requests.get(f'{self.FRONTIER_SERVER_URL}/hashes')
        if response.status_code == 200:
            self.logger.info("Got hashes from frontier\n")
            return set(response.json()['hashes'])
        else:
            self.logger.error(f"Error: Failed to fetch hashes. Status code: {response.status_code}\n")
            raise HashesError(f"Error: Failed to fetch hashes. Status code: {response.status_code}")


    def process_url(self,url):

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36')
        options.add_argument('user-agent=fri-ieps-Lt-Colonel-Kilgore-team')

        driver_service = Service(self.WEB_DRIVER_LOCATION)
        driver_service.start()

        driver = webdriver.Chrome(service=driver_service, options=options)


        driver.get(url + "/robots.txt")

        time.sleep(self.TIMEOUT)
        domain = urlparse(url).netloc
        #visited_domains = self.get_visited_domains()

        result_robot = {}
        #if domain not in visited_domains:
        self.logger.info("Domain already visited\n")
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

        status_code = requests.get(url).status_code if not self.check_binary(url) else ""


        if self.check_binary(url):
            self.logger.info("Binary content found\n")
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

            a_tags = driver.find_elements(By.TAG_NAME, "a")
            imgs = driver.find_elements(By.TAG_NAME, "img")
            html = driver.page_source

            self.logger.info("HTML content found\n")
            links = self.parse_links(a_tags)
            img = self.parse_img(imgs)
            html_hash = self.hash_html(html)

            driver.quit()
            result_parse = {
                'url': url,
                'html': html,
                'img': img,
                'links': links,
                'pageType': "HTML",
                'httpStatusCode': status_code,
                'accessedTime': datetime.now().isoformat(),
                'hash': html_hash,
            } #if html_hash in self.get_hashes_from_frontier() else {
                #'url': url,
                #'warning': 'This page has been parsed.'
            #}
        return result_robot, result_parse

    def main(self, urls):

        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            for url in urls:
                time.sleep(self.TIMEOUT)
                future_to_url = {executor.submit(self.process_url, url): url}
                for future in concurrent.futures.as_completed(future_to_url):
                    time.sleep(self.TIMEOUT)
                    url = future_to_url[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as exc:
                        self.logger.error(f'Error processing URL {url}: {exc}\n')
                        results.append({'url': url, 'error': str(exc)})

        self.logger.info("Finished scraping sending results to frontier\n")

        return results

if __name__ == '__main__':
    scraper = MyWebScraper()
    scraper.start(host='0.0.0.0', port=5000)
