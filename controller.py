import requests
import json
import time

FRONTIER_ENDPOINT="https://172.23.3.4:49500"
AUTH = ("Crawler1", "&*qRyQ-7dMCX$S9&")


def get_new_url():
    return requests.get(FRONTIER_ENDPOINT+"/new_url",verify=False,auth=AUTH).json()


def scrape(json):
    return requests.post("http://127.0.0.1:5005/scrape", json=json)

def save_page(json):
    return requests.post(FRONTIER_ENDPOINT + "/new_url", verify=False, auth=AUTH, json=json)


if __name__=='__main__':
    while True:
        url_json = get_new_url()
        scrape_dict = {"messages": [url_json['link']]}
        scrape_result = scrape(scrape_dict)
        save_page(scrape_result.json())
        time.sleep(5)



