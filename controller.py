import requests
import json
import time

FRONTIER_ENDPOINT="https://172.23.3.4:49500"
AUTH = ("Crawler1", "&*qRyQ-7dMCX$S9&")


def get_new_url():
    return requests.get(FRONTIER_ENDPOINT+"/new_url", verify=False, auth=AUTH,timeout=20).json()

def scrape(json):
    return requests.post("http://127.0.0.1:5005/scrape", json=json,timeout=20)

def save_page(json):
    return requests.post(FRONTIER_ENDPOINT + "/save_page", verify=False, auth=AUTH, json=json,timeout=20)


if __name__=='__main__':
    while True:
        url_json = get_new_url()
        print("Got new url: ", url_json)
        scrape_dict = {"messages": [url_json['link']]}
        print("Sending scrape request: ", scrape_dict)
        scrape_result = scrape(scrape_dict)
        print("Got scrape result, saving page")
        save_page_result = save_page(scrape_result.json())
        print("Save page result: ", save_page_result.json())
        time.sleep(5)



