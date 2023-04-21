import re
import json



def getOverstock(html):
    title_pattern = r'<a href=\"http:\/\/www\.overstock\.com\/cgi-bin\/d2\.cgi\?PAGE=PROFRAME&amp;PROD_ID=\d+"><b>(.*?)<\/b><\/a>'
    list_price_pattern = r"<s>(.*?)</s>"
    price_pattern = r"<span class=\"bigred\"><b>(.*?)<\/b><\/span>"
    saving_pattern = r"<span class=\"littleorange\">(\$[\d.,]+)"
    savingPercent_pattern = r"<span class=\"littleorange\">.*?(\d+%)"

    titles = re.findall(title_pattern, html)
    list_prices = re.findall(list_price_pattern, html)
    price = re.findall(price_pattern, html)
    saving = re.findall(saving_pattern, html)
    savingPercent = re.findall(savingPercent_pattern, html)

    content_pattern = r"<span class=\"normal\">(.*?)</span>"
    contents = re.compile(content_pattern, re.DOTALL)
    content = re.findall(contents, html)
    print(content)

    print(len(content))

    for i in range(len(titles)):
        output = {
            'Title': titles[i],
            'ListPrice': list_prices[i],
            'Price': price[i],
            'Saving': saving[i],
            'SavingPercent': savingPercent[i],
            'Content': content[i]
        }
        print(json.dumps(output, indent=1, ensure_ascii=False))


def getRTV(html):
    title_pattern = r'<h1.*?>(.*?)<\/h1>'
    subtitle_pattern = r'<div class=\"subtitle\">(.*)</div>'
    lead_pattern = r'<p.*?class="lead".*?>(.*?)<\/p>'
    author_pattern = r'<div *?class=\"author-name\">(.*)</div>'
    time_pattern = r"<div *?class=\"publish-meta\">\n\t\t(.*)<br>"

    content_patternr = r"<div *?class=\"article-body\">(.*?)<div class=\"gallery\">"
    content_pattern = re.compile(content_patternr, re.DOTALL)

    # regex_content = r"<div class=\"article-body\">(.*?)<div class=\"gallery\">"
    # pattern_content = re.compile(regex_content, re.DOTALL)
    # content = re.findall(pattern_content, html).group(1)

    title_match = re.search(title_pattern, html).group(1)
    subtitle_match = re.search(subtitle_pattern, html).group(1)
    lead_match = re.search(lead_pattern, html).group(1)
    author_match = re.search(author_pattern, html).group(1)
    time_match = re.search(time_pattern, html).group(1)

    content_matches = re.search(content_pattern, html).group(1)

    # print(content_matches[0])
    # print(content)

    output = {
        'title': title_match,
        'subtitle': subtitle_match,
        'lead': lead_match,
        'author': author_match,
        'time': time_match,
        'content': content_matches
    }
    # print(json.dumps(output, indent=1, ensure_ascii=False))

