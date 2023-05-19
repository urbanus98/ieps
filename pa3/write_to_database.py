import preprocessing
import sqlite3

htmls = preprocessing.preprocess()

conn = sqlite3.connect('inverted-index.db')
cursor = conn.cursor()

# cursor.execute("DELETE FROM IndexWord")
# cursor.execute("DELETE FROM Posting")

i = 0
for html in htmls:
    for word, wordata in html.data.items():
        # print(word, wordata.frequency, wordata.indexes)

        cursor.execute('''INSERT OR IGNORE INTO IndexWord(word) VALUES (?)''', (word,))

        cursor.execute('''INSERT OR IGNORE INTO Posting(word, documentName, frequency, indexes) VALUES (?, ?, ?, ?)''', (word, html.path, wordata.frequency, wordata.indexes))

        i += 1
        if i % 100 == 0:
            print(i)
            conn.commit()

conn.commit()
conn.close()