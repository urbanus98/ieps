# WEIR Programming Assignment 1

The crawler consists of three programs:

 - WebCrawlerService.py is a Flask app that handles parsing when a new link is passed through POST /scrape request
 - controller.py fetches new links from frontier and requests parsing from WebCrawlerService
 - frontier.ipynb handles fetching new links and saving data into a postgres database (in our case postgres was running in a Docker container on the same machine. It supports multiple remote instances of controller.py running simultaneously.
 
 Set up:
 
 1. Set up an instance of PostgreSQL database. Inside crawldb.page table, insert seed URLs with page_type_code set to 'FRONTIER'.
 2. Run frontier.ipynb and edit credentials and host inside "conn" variable to match PostgreSQL instance in (1.).
 3. On the machine used for crawling, run WebCrawlerService
 4. Edit the FRONTIER_ENDPOINT and AUTH variables in controller.py to match frontier.ipynb setup.
 5. Once ready, run controller.py - it will request a new link from frontier and start crawling.
