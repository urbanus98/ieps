import sqlite3
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import time
from contextlib import closing
from bs4 import BeautifulSoup
import os
from preprocessing import preprocess

def get_text_from_document(document_name):
    base_path = r"pa3_data"
    # Split document_name by '/'
    document_split = document_name.split('/')
    # Construct complete path
    document_path = os.path.join(base_path, *document_split)
    with open(document_path, 'r', encoding='utf-8') as file:
        content = file.read()
    soup = BeautifulSoup(content, 'html.parser')
    return soup.get_text().lower()

# Function to preprocess query
def preprocess_query(query):
    words = word_tokenize(query)
    words = [word.lower() for word in words if word.isalpha()]
    return words


def get_snippet(document_name, word_indexes):
    # Assuming you have a function to get text from the document
    document_text = get_text_from_document(document_name)
    words = word_tokenize(document_text)
    snippets = []

    for index in word_indexes:
        start = max(index - 3, 0)
        end = min(index + 3, len(words) - 1)
        snippet = " ..." + " ".join(words[start:end + 1]) + "... "
        snippets.append(snippet)

    return snippets

# Function to perform search

def search(query):
    try:
        # Preprocess the query
        words = preprocess_query(query)

        start_time = time.time()  # Start the timer

        results = []

        htmls = preprocess()

        for word in words:
            for html in htmls:
                if word in html.data:
                    wordobject = html.data[word]
                    document_name = html.path
                    #print(document_name)
                    word_indexes = list(map(int, wordobject.indexes.split(',')))
                    #print(word_indexes)
                    snippets = get_snippet(document_name, word_indexes)
                    #print(snippets)
                    result = (wordobject.frequency, document_name, snippets)
                    #print(result)
                    results.append(result)
                

        results.sort(key=lambda x: x[0], reverse=True)
        #print(results)
        end_time = time.time()  # End the timer
        elapsed_time = end_time - start_time  # Calculate elapsed time

        # Print results
        print(f"Results for a query: \"{query}\"\n")
        print(f"Results found in {elapsed_time * 1000:.0f}ms.\n")
        print(f"{'Frequencies':<12} {'Document':<40} {'Snippet'}")
        print(f"{'-----------':<12} {'----------------------------------------':<40} {'-----------------------------------------------------------'}")
        for frequency, document, snippets in results:
            print(f"{frequency:<12} {document:<40} {snippets}")

    except Exception as e:
        print(f"Error occurred: {e}")
        return []


query = input("Enter query: ")
results = search(query)
if results is not None:
    for result in results:
        print(result)
