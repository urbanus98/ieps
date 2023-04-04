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
        response = make_response(jsonify(db_response[0][1]), 200)
        return response


    def save_page(self):
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


