# Frontier mora imet endpointe:
# /visited_domains - vrne domene, ki so bile že obiskane + info iz robots za domeno
# /new_url - vrne prvi url iz frontierja
# /save_page - sprejme JSON iz pajka, preveri za duplikate in shrani vse podatke
# /save_robots - shrani robots.txt obiskane domene
# /hashes - pridobi vse hashe



import os
import threading
import psycopg2
from flask import Flask, request, jsonify, make_response
import logging
from io import StringIO

conn = psycopg2.connect(host="31.15.143.42", dbname="crawldb", user="ieps", password="spiderman", port=45433)
conn.autocommit = True

lock = threading.Lock()


class Frontier:

    def __init__(self) -> None:
        self.app = Flask("Frontier")
        self.app.route('/visited_domains', methods=['GET'])(self.visited_domains)
        self.app.route('/new_url', methods=['GET'])(self.new_url)
        self.app.route('/hashes', methods=['GET'])(self.hashes)
        self.app.route('/save_page', methods=['POST'])(self.save_page)
        self.app.route('/save_domain', methods=['POST'])(self.save_domain)

        self.log_stream = StringIO()
        log_handler = logging.StreamHandler(self.log_stream)
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s\n')
        log_handler.setFormatter(log_formatter)
        self.logger = logging.getLogger('web_scraper')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(log_handler)

    def start(self, host='0.0.0.0', port=49500):
        try:
            self.app.run(host=host, port=port)
        except Exception as e:
            self.logger.error(f'Error starting the Flask app: {e}\n')
    
    def visited_domains(self):

        cur = conn.cursor()
        cur.execute("SELECT domain FROM frontier.domains")
        db_response = cur.fetchall()
        #print(db_response)
        cur.close()
        response = make_response(jsonify(db_response), 200)

        return response

    def new_url(self):
        cur = conn.cursor()
        # return first link in frontier
        cur.execute("SELECT * FROM frontier.waiting_links LIMIT 1")
        db_response = cur.fetchall()
        #print(db_response)
        id = db_response[0][0]
        # move link from waiting to in progress links
        cur.execute('WITH selection AS ( '
                    'DELETE FROM frontier.waiting_links '
                    f'WHERE link_id = {id} '
                    'RETURNING  *) '
                    'INSERT INTO frontier.inprogress_links '
                    'SELECT * FROM selection;')
        cur.close()
        response = make_response(jsonify(db_response[0][1]), 200)
        return response

    def save_domain(self):
        input_json = request.get_json()
        cur = conn.cursor()

        cur.execute('INSERT INTO frontier.domain '
                    '(domain, robot_txt_content, sitemap_host_content, '
                    'robot_delay, robot_allowance, sitemap_content_links) '
                    f"VALUES ( {input_json.get('domain')}, {input_json.get('robot_txt_content')}, "
                    f" {input_json.get('sitemap_host_content')}, {input_json.get('robot_delay')}, "
                    f" {input_json.get('robot_allowance')}, {input_json.get('sitemap_content_links')} )")

        cur.execute('INSERT INTO crawldb.site '
                    '(domain, robots_content, sitemap_content '
                    f"VALUE ( {input_json.get('domain')}, {input_json.get('robot_txt_content')}, "
                    f"{input_json.get('sitemap_content_links')} )")

        cur.close()

        response = make_response("Domain saved",200)

        return response

    def save_page(self):
        input_json = request.get_json()

        if input_json.get('pageType') == "HTML":
            cur = conn.cursor()

            try:
                cur.execute('SELECT id FROM crawldb.site WHERE '
                            f"domain = {input_json.get('domain')}")
                site_id = cur.fetchall()[0]

                cur.execute('INSERT INTO crawldb.page '
                            '(site_id, page_type_code, url, '
                            'html_content, http_status_code, '
                            'accessed_time, hash) '
                            f"VALUE ( {site_id}, {input_json.get('pageType')}, {input_json.get('pageType')}, "
                            f"{input_json.get('url')}, {input_json.get('html_content')}, "
                            f"{input_json.get('httpStatusCode')}, {input_json.get('accessedTime')}, "
                            f"{input_json.get('hash')} )")

            except Exception as e:
                self.logger.error(f'Error saving page: {e}\n')

            for link in input_json.get('links'):
                cur.execute(f"INSERT INTO frontier.waiting_links VALUES ( {link})")


        pass

    def hashes(self):
        cur = conn.cursor()
        # return all hashes
        cur.execute("SELECT hash FROM crawldb.page")
        db_response = cur.fetchall()
        #print(db_response)

        response = make_response(jsonify(db_response), 200)

        return response


if __name__=='__main__':
    try:
        frontier = Frontier()
        frontier.start(host="127.0.0.1", port=59500)

    except KeyboardInterrupt:
        conn.close()
        print("Keyboard interrupt")

    except Exception as e:
        print("Exception encountered:", e)


