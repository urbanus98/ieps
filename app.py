import requests

def main():
    url = 'http://127.0.0.1:5000/scrape'
    data = {'message': 'https://e-uprava.gov.si/'}
    response = requests.post(url, data=data)

    print(response.text)


if __name__ == '__main__':
    main()