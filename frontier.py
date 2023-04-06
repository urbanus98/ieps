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
from flask_httpauth import HTTPBasicAuth
from urllib.parse import urlparse

conn = psycopg2.connect(host="31.15.143.42", dbname="crawldb", user="ieps", password="spiderman", port=45433)
conn.autocommit = True

lock = threading.Lock()

basic_auth = HTTPBasicAuth()


# making requests: requests.get(ENDPOINT+"/db/get_values",verify=False, auth = AUTH).json())


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
        cur.execute("SELECT domain FROM crawldb.site")
        db_response = cur.fetchall()
        #print(db_response)
        cur.close()
        response = make_response(jsonify(db_response), 200)

        return response

    def new_url(self):
        cur = conn.cursor()
        # return first link in frontier
        cur.execute("SELECT id, url FROM crawldb.page WHERE page_type_code = 'FRONTIER' LIMIT 1")

        db_response = cur.fetchall()
        #print(db_response)
        page_id = db_response[0][0]
        #print(page_id)
        cur.execute(f"UPDATE crawldb.page SET page_type_code = 'PARSING' WHERE id = {page_id};")
        cur.close()
        link = {"link": db_response[0][1]}
        response = make_response(jsonify(link), 200)
        return response

    def save_domain(self, json):
        #input_json = request.get_json()
        input_json = json
        cur = conn.cursor()
        cur.execute(f"SELECT id FROM crawldb.site WHERE domain = '{input_json.get('domain')}'")
        site_id = cur.fetchone()

        if site_id is not None:
            site_id = site_id[0]

        #print(site_id)
        if site_id is None:
            cur.execute('INSERT INTO crawldb.site '
                        '(domain, robots_content, sitemap_content ) '
                        f"VALUES ( '{input_json.get('domain')}', '{input_json.get('robot_txt_content')}', "
                        f"'{input_json.get('sitemap_content_links')}' ) ON CONFLICT (domain) DO NOTHING RETURNING id")

            if site_id is not None:
                site_id = site_id[0]
        #print(site_id)

        cur.close()


        response = make_response(jsonify({"site_id": site_id}), 200)

        return response

    def save_page(self):
        all_json = request.get_json()

        cur = conn.cursor()

        if 'error' in all_json:
            cur.execute('DELETE FROM crawldb.page WHERE'
                        f" url = '{all_json.get('url')}'")
        else:
            #try:

            input_json = all_json[0][1]
            site_json = all_json[0][0]
            #print(site_json)

            response = self.save_domain(site_json)
            site_id = response.get_json().get('site_id')

            if input_json.get('pageType') == "HTML":

                cur.execute("SELECT id, hash FROM crawldb.page")
                hashes = cur.fetchall()
                #print(hashes)

                new_hash = input_json.get('hash')

                id_of_original = None

                duplicate = False
                for hash in hashes:
                    if hash[1] == new_hash:
                        duplicate = True
                        id_of_original = hash[0]

                #print(duplicate, id_of_original)
                if duplicate:
                    cur.execute('UPDATE crawldb.page SET'
                                f" page_type_code = 'DUPLICATE', "
                                f" site_id = {site_id}, "
                                f" http_status_code = {input_json.get('httpStatusCode')}, "
                                f" accessed_time = '{input_json.get('accessedTime')}', " 
                                f" hash = '{input_json.get('hash')}' WHERE "
                                f" url = '{input_json.get('url')}' RETURNING id" )

                    dup_page_id = cur.fetchone()[0]

                    cur.execute(f"INSERT INTO link (from_page, to_page) VALUES ({id_of_original},{dup_page_id})")
                else:
                    cur.execute('UPDATE crawldb.page SET'
                                f" page_type_code = '{input_json.get('pageType')}', "
                                f" site_id = {site_id}, "
                                f" html_content = '{input_json.get('html_content')}', "
                                f" http_status_code = {input_json.get('httpStatusCode')}, "
                                f" accessed_time = '{input_json.get('accessedTime')}', " 
                                f" hash = '{input_json.get('hash')}' WHERE "
                                f" url = '{input_json.get('url')}' RETURNING id")

                    page_id = cur.fetchone()[0]

                    img_query = "INSERT INTO image (page_id, content_type, filename, accessed_time) VALUES " + ",".join(
                        [f"({page_id}, '{img.get('contentType')}', '{img.get('filename')}', '{img.get('accessedTime')}' );" for img in input_json.get('img')])

                    cur.execute(img_query)

                    url_query = "INSERT INTO crawldb.page (url, page_type_code) VALUES " + ",".join([f"('{link}', 'FRONTIER')" for link in input_json.get('links')]) + " ON CONFLICT (url) DO NOTHING;"
                    #print(query)
                    cur.execute(url_query)

            elif input_json.get('pageType') == "BINARY":
                if input_json.get('pageTypeCode') in ["DOC", "DOCX", "PDF", "PPT", "PPTX"]:
                    cur.execute('UPDATE crawldb.page SET'
                                f" page_type_code = '{input_json.get('pageType')}', "
                                f" site_id = {site_id}, "
                                f" http_status_code = {input_json.get('httpStatusCode')}, "
                                f" accessed_time = '{input_json.get('accessedTime')}', "
                                f" hash = '{input_json.get('hash')}' WHERE "
                                f" url = '{input_json.get('url')}' RETURNING id")
                    page_id = cur.fetchone()[0]
                    #print(page_id)

                    cur.execute("INSERT INTO crawldb.page_data (page_id, data_type_code) "
                                f"VALUES ({page_id}, '{input_json.get('pageTypeCode')}' )")
                else:
                    cur.execute('DELETE FROM crawldb.page WHERE'
                                f" url = '{input_json.get('url')}'")
            #except:
            #    print("error")
            #    cur.execute('DELETE FROM crawldb.page WHERE'
            #                f" url = '{all_json[0][1].get('url')}'")



        cur.close()

        return make_response("SUCCESS", 200)

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


