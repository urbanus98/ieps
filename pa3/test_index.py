import bs4
from nltk.tokenize import word_tokenize

def get_text_elements(html):
    soup = bs4.BeautifulSoup(html, "html.parser")
    text_elements = soup.get_text().lower()
    return text_elements


# path = 'pa3_data/evem.gov.si/evem.gov.si.63.html'
path = 'pa3_data/e-uprava.gov.si/e-uprava.gov.si.1.html'

with open(path, 'r', encoding="utf8") as f:
    html = f.read()
    
text_elements = get_text_elements(html)

words = word_tokenize(text_elements)

# print(words[350:370])
print(words[2])