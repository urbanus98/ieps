import requests
import json
import time
from urllib.parse import urlparse



FRONTIER_ENDPOINT="https://172.23.3.4:49500"
AUTH = ("Crawler1", "&*qRyQ-7dMCX$S9&")

visited_domains = {}
domain_delays = {}



def get_new_url():
    return requests.get(FRONTIER_ENDPOINT+"/new_url", verify=False, auth=AUTH,timeout=30).json()

def get_visited_domains():
    return

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
        url = url_json.get('')
        domain = urlparse(u).netloc
        print("Sending scrape request: ", scrape_dict)
        scrape_result = scrape(scrape_dict)
        print("Got scrape result, saving page")
        save_page_result = save_page(scrape_result.json())
        print("Save page result: ", save_page_result.json())
        time.sleep(5)



