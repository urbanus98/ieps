import sqlite3
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import time
from contextlib import closing
from bs4 import BeautifulSoup
import os

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

        with closing(sqlite3.connect('inverted-index.db')) as conn, closing(conn.cursor()) as c:
            results = []

            for word in words:
                # Get data for a word
                c.execute("SELECT * FROM Posting WHERE word=?", (word,))
                rows = c.fetchall()

                # Append results
                for row in rows:
                    document_name = row[1]
                    word_indexes = list(map(int, row[3].split(',')))
                    snippets = get_snippet(document_name, word_indexes)
                    result = (row[2], row[1], snippets)
                    results.append(result)

            # Sort results by frequency
            results.sort(key=lambda x: x[0], reverse=True)

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