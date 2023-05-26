import bs4
import os
import re
from nltk.tokenize import word_tokenize
from stopwords import stop_words_slovene, stopcharacters
import string

htmls = []

class HTMLDocument:
    path: string
    text: string
    data = {}

    def __init__(self, path, text):
        self.path = path
        self.text = text
        self.data = {}

class WordData:
    word: string
    frequency: int
    indexes: string

    def __init__(self, word, frequency, indexes):
        self.word = word
        self.frequency = frequency
        self.indexes = indexes

def isNumber(str):
    if str[0].isdigit():
        return True
    else:
        return False
    
def isLink(str):
    linkChars = ['/', ':', '.', '?', '=', '&']
    for char in linkChars:
        if char in str:
            return True
    return False

def get_text_elements(html):
    soup = bs4.BeautifulSoup(html, "html.parser")
    text_elements = soup.get_text().lower()
    return text_elements
    
def readFiles():
    # root_dir = 'pa3_data'
    root_dir = 'test_data'
    # Iterate over all subdirectories and files
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            # Get the full path of the file
            file_path = os.path.join(dirpath, filename)

            with open(file_path, 'r', encoding="utf8") as f:
                html = f.read()
            file_path = file_path[9:]
            file_path = file_path.replace('\\', '/')

            text_elements = get_text_elements(html)

            htmls.append(HTMLDocument(file_path, text_elements))

def isLegitWord(word):
    if len(word) > 2:
        if word not in stop_words_slovene:
            if word not in stopcharacters:
                if not isNumber(word) or not isLink(word):
                    return True
    return False


def preprocess():

    readFiles()

    for html in htmls:
        #print(html.path)
        words = word_tokenize(html.text)
        for word in words:
            word = word.strip()
            if isLegitWord(word):
                if word not in html.data:
                    # get all indexes of word in words
                    indexes = [i for i, x in enumerate(words) if x == word]
                    
                    # indexes to string
                    stringexes = ','.join(map(str, indexes))

                    html.data[word] = WordData(word, len(indexes), stringexes)
                    # print(stringexes)
    
    return htmls

