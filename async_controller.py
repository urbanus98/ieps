import asyncio
import aiohttp
import queue
from urllib.parse import urlparse

last_request_time = {}
domain_delays = {'default': 5}

FRONTIER_ENDPOINT="https://172.23.3.4:49500"
AUTH = aiohttp.BasicAuth(login="Crawler1", password="&*qRyQ-7dMCX$S9&")
CRAWLER_ENDPOINT = "http://127.0.0.1:5005"

async def get_new_url():
    async with aiohttp.ClientSession() as session:
        async with session.get(FRONTIER_ENDPOINT+"/new_url", ssl=False, auth=AUTH, timeout=30) as response:
            return await response.json()

async def make_request(session, url, visited_domain):
    try:
        print("making request to: ", url)
        request_json = {"messages": [url], "visitedDomain": visited_domain}
        async with session.post(CRAWLER_ENDPOINT + "/scrape", json=request_json, timeout=10) as response:
            return await response

    except Exception as e:
        print(f"Error occurred while making request to {url}: {e}")
        return None


async def make_delayed_request(session, url):
    print("making a delayed request to ", url)
    domain = urlparse(url).netloc  # extract domain from URL
    visited_domain = domain in domain_delays
    print("visited_domain", domain, visited_domain)
    rate_limit = domain_delays.get(domain, 5)  # get the rate limit for this domain, defaulting to 5 if not found
    if domain in last_request_time:
        time_since_last_request = asyncio.get_event_loop().time() - last_request_time[domain]
        if time_since_last_request < rate_limit:
            await asyncio.sleep(rate_limit - time_since_last_request)
    last_request_time[domain] = asyncio.get_event_loop().time()
    return await make_request(session, url, visited_domain)

async def worker(session, queue):
    while True:
        print("got into a worker")
        url = await queue.get()
        response = await make_delayed_request(session, url)
        print(response)
        queue.task_done()

async def make_requests():
    async with aiohttp.ClientSession() as session:
        request_queue = queue.Queue()
        for i in range(1):  # process how many requests
            url_json = await get_new_url()
            print("Got new url: ", url_json)
            request_queue.put_nowait(url_json['link'])
        await request_queue.join()
        print("request queue joined")
        worker_coroutines = [worker(session, request_queue) for _ in range(10)]  # create 10 worker coroutines
        await asyncio.gather(*worker_coroutines, return_exceptions=True)
        for w in worker_coroutines:
            w.cancel()

async def main():
    await make_requests()

if __name__ == "__main__":
    asyncio.run(main())