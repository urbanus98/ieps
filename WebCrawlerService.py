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
import xml.etree.ElementTree as Et
from robotexclusionrulesparser import RobotExclusionRulesParser
import validators
import hashlib
import logging
import urllib
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
    FRONTIER_SERVER_URL = 'http://127.0.0.1:8000'
    
    found_bin = ""
    domain_visited = 0

    def __init__(self):
        self.app = Flask("MyWebScraper_number")
        self.app.route('/scrape', methods=['POST'])(self.scrape)
        self.app.route('/logs', methods=['GET'])(self.get_logs)

        self.session = requests.Session()

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
        try:
            self.app.run(host=host, port=port)
        except Exception as e:
            self.logger.error(f'Error starting the Flask app: {e}\n')

    def scrape(self):
        print(request.get_json())
        input_messages = request.get_json().get('messages', [])
        # self.domain_visited = bool(request.get_json().get('visitedDomain'))
        self.domain_visited = int(request.get_json().get('visitedDomain'))
        results = []
        for input_value in input_messages:
            self.logger.info(f'Starting scrape for URL: {input_value}\n')
            try:
                result = self.main([input_value])  # Make sure to put the input_value in a list
                results.extend(result)
            except Exception as e:
                self.logger.error(f'Error processing URL {input_value}: {e}\n')
                results.append({'url': input_value, 'error': str(e), 'method': 'scrape'})
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
        lines = page_source.split('\n')

        for line in lines:
            line = line.strip()
            if line.lower().startswith('sitemap:'):
                sitemap_host = line[len('sitemap:'):].strip()
                break

        sub_str = ".xml"

        # remove everything after the .xml
        if sitemap_host and sub_str in sitemap_host:
            sitemap_host = sitemap_host[:sitemap_host.index(sub_str) + len(sub_str)]

            # check if sitemap_host is working or returns a 404 error
            response = requests.get(sitemap_host)
            if response.status_code == 404:
                self.logger.warning(f"Sitemap host {sitemap_host} returned 404 error")
                return (sitemap_host, False)
            else:
                self.logger.info(f"Sitemap host: {sitemap_host}\n")
                return (sitemap_host, True)
        else:
            self.logger.warning("No sitemap host found")
            return (sitemap_host, False)

    def get_sitemap_content(self, sitemap_host):

        self.logger.info("Getting sitemap links\n")
        urls = set()
        try:
            def process_sitemap(host):
                nonlocal urls
                if not host:
                    return

                try:
                    response = requests.get(host)
                    if response.status_code != 200:
                        self.logger.error(f"Error getting sitemap content: {response.status_code}\n")
                        return

                    response = requests.get(host)
                    root = Et.fromstring(response.content)

                    self.logger.info(f"Processing sitemap: {host}\n")

                    for child in root:
                        for url in child:
                            url_text = url.text
                            if url_text and "http" in url_text:
                                if "xml" in url_text:
                                    self.logger.info(f"Found nested sitemap: {url_text}\n")
                                    process_sitemap(url_text)
                                else:
                                    canonized_sitemap_url = self.canonize_url(url_text)
                                    self.logger.info(f"Found URL: {canonized_sitemap_url}\n")
                                    urls.add(canonized_sitemap_url)

                except Exception as ex:
                    self.logger.error(f"Error getting sitemap content: {ex}\n")

            process_sitemap(sitemap_host)

        except Exception as ex:
            self.logger.error(f"Error getting sitemap content: {ex}\n")
            return None

        self.logger.info(f"Found {len(list(urls))} URLs\n")
        return list(urls)

    def check_robot_txt(self, driver):
        self.logger.info("Checking robot.txt\n")

        robot_delay = None
        robot_allowance = None

        robots_url = driver.current_url.rstrip('/') + '/robots.txt'

        # Parse the robots.txt file
        rp = RobotExclusionRulesParser()
        rp.fetch(robots_url)

        # Check if the user agent is allowed to crawl the website
        is_allowed = rp.is_allowed('*', driver.current_url)
        if is_allowed:
            robot_allowance = "User agent is allowed to crawl the website"
        else:
            robot_allowance = "User agent is not allowed to crawl the website"

        self.logger.info(f"Robot.txt allowance: {robot_allowance}\n")

        # Get the crawl delay for the user agent
        crawl_delay = rp.get_crawl_delay('*')
        if crawl_delay is not None:
            robot_delay = crawl_delay

        self.logger.info(f"Robot.txt delay: {robot_delay}\n")

        return robot_delay, robot_allowance


    def parse_links(self, driver):
        self.logger.info("Parsing links\n")
        links = []
        #print('Parsing links')
        #od tuki naprej se neki sfuka z linki in pol ne dela

        for link in driver.find_elements(By.TAG_NAME, "a"):
                        
            href = link.get_attribute("href")
            if href is not None and validators.url(href):
                canonized_href = self.canonize_url(href)
                links.append(canonized_href)
        self.logger.info("URL canonization\n")
        self.logger.info(f"Found {len(links)} links\n")
        return links

    def canonize_url(self, url):
        parsed_url = urlparse(url)
        parsed_url = parsed_url._replace(fragment='', netloc=parsed_url.netloc.lower())
        canonized_url = urlunparse(parsed_url)
        #self.logger.info("Canonized URL \n")
        return canonized_url

    def parse_img(self, driver):
        self.logger.info("Parsing images\n")
        images = []
        for img in driver.find_elements(By.TAG_NAME, "img"):
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
                    #print(f"Invalid ext: {ext}")
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

    def process_url(self,url):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--blink-settings=imagesEnabled=false')
            #options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36')
            options.add_argument('user-agent=fri-ieps-Lt-Colonel-Kilgore-team')

            driver_service = Service(self.WEB_DRIVER_LOCATION)
            driver_service.start()

            driver = webdriver.Chrome(service=driver_service, options=options)
            self.TIMEOUT = 5
            sitemap_content = []

            driver.get(url + "/robots.txt")

            domain = urlparse(url).netloc

            print('parsing robots.txt')

            rc = ""
            try:
                # response = urllib.request.urlopen(url + "/robots.txt")
                response = requests.get('https://' + domain + "/robots.txt")
                rc = response.text
            except urllib.error.HTTPError as e:
                print("Error retrieving robots.txt file" + e.reason)

            print(self.domain_visited)
            if self.domain_visited == 1:
                robot_txt_content = ""
                sitemap_content = []
                sitemap_host = []
                print('Domain already visited')
                self.logger.info("Domain already visited\n")
            else:
                robot_txt_content = rc
                sitemap_host = self.get_sitemap_host(driver)
                sitemap_content = self.get_sitemap_content(sitemap_host[0])
                print('Domain not already visited')
                
            robot_delay, robot_allowance = self.check_robot_txt(driver)

            print('got through robot parsing')

            result_robot = {
                'domain': domain,
                'robot_txt_content': robot_txt_content,
                'sitemap_host_content': sitemap_host,
                'robot_delay': robot_delay,
                'robot_allowance': robot_allowance,
                'sitemap_content_links': sitemap_content,
            }

            if robot_delay is not None:
                self.TIMEOUT = max(self.TIMEOUT, robot_delay)

            time.sleep(self.TIMEOUT)

            status_code = self.session.get(url).status_code if not self.check_binary(url) else ""

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
                driver.close()
            else:
                driver.get(url)

                # if self.domain_visited == 0:
                #     time.sleep(1)
                # else:
                time.sleep(0.5)

                html = driver.page_source

                # print(a_tags)
                self.logger.info("HTML content found\n")

                links = self.parse_links(driver)
                # print(links)

                img = self.parse_img(driver)
                html_hash = self.hash_html(html)

                print('got through page parsing')

                driver.close()
                result_parse = {
                    'url': url,
                    'html': html,
                    'img': img,
                    'links': links,
                    'pageType': "HTML",
                    'httpStatusCode': status_code,
                    'accessedTime': datetime.now().isoformat(),
                    'hash': html_hash,

                }
            return result_robot, result_parse

        except Exception as e:
            self.logger.error(f"Error processing URL {url}: {e}\n")
            return {'url': url, 'error': str(e), 'method': 'process_url'}

    def main(self, urls):

        results = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(self.process_url, url): url for url in urls}
            for future in concurrent.futures.as_completed(futures):
                url = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    self.logger.error(f'Error processing URL {url}: {exc}\n')
                    results.append({'url': url, 'error': str(exc), 'method': 'main'})

        self.logger.info("Finished scraping sending results to frontier\n")

        return results

if __name__ == '__main__':
    scraper = MyWebScraper()
    scraper.start(host='0.0.0.0', port=5000)