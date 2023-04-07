import requests
import json
import time
from urllib.parse import urlparse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FRONTIER_ENDPOINT="https://31.15.143.42:49500"
AUTH = ("Crawler1", "&*qRyQ-7dMCX$S9&")

last_request_time = {}
domain_delays = {}


def get_new_url():
    return requests.get(FRONTIER_ENDPOINT+"/new_url", verify=False, auth=AUTH,timeout=30).json()

def get_and_delay_domain(url):
    domain = urlparse(url).netloc
    rate_limit = domain_delays.get(domain, 5)
    visited_domain = False
    if domain in last_request_time:
        visited_domain = True
        time_since_last_request = time.time() - last_request_time[domain]
        if time_since_last_request < rate_limit:
            time.sleep(rate_limit - time_since_last_request)
    last_request_time[domain] = time.time()

    return {"messages": [url], "domain": domain, "visitedDomain": visited_domain}

def scrape(json):
    try:
        return requests.post("http://127.0.0.1:5005/scrape", json=json, timeout=30)
    except Exception as e:
        print("Error when scraping ", json)

def save_page(json):
    return requests.post(FRONTIER_ENDPOINT + "/save_page", verify=False, auth=AUTH, json=json, timeout=30)


if __name__=='__main__':
    while True:
        url_json = get_new_url()
        print("Got new url: ", url_json)
        url = url_json.get('link')
        scrape_dict = get_and_delay_domain(url)
        print("Sending scrape request: ", scrape_dict)
        scrape_result = scrape(scrape_dict)

        if not scrape_dict.get('visitedDomain'):
            print(scrape_result.json())
            if ('error') in scrape_result.json()[0]:
                print("Error when parsing page, deleting page from frontier.")

            else:
                domain_data = scrape_result.json()[0][0]
                delay = domain_data.get('robot_delay')
                domain = domain_data.get('domain')
                if delay is not None:
                    domain_delays['domain'] = delay
                else:
                    domain_delays['domain'] = 5
                print("Saved delay for domain", domain, delay)
                print("Got scrape result, saving site")
        save_page_result = save_page(scrape_result.json())
        print("Save page result: ", save_page_result.json())

