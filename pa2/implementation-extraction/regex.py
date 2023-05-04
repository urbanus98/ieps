import re
import json


def extract_patterns(html, patterns):
    return [re.findall(pattern, html) for pattern in patterns]


def getOverstock(html):
    patterns = [
        r'<a href=\"http:\/\/www\.overstock\.com\/cgi-bin\/d2\.cgi\?PAGE=PROFRAME&amp;PROD_ID=\d+\"><b>(.*?)<\/b><\/a>',
        r"<s>(.*?)</s>",
        r"<span class=\"bigred\"><b>(.*?)<\/b><\/span>",
        r"<span class=\"littleorange\">(\$[\d.,]+)",
        r"<span class=\"littleorange\">.*?(\d+%)",
        r"<span class=\"normal\">(.*?(?=<br><a href=\"http:\/\/www\.overstock\.com\/cgi-bin\/d2\.cgi\?PAGE=PROFRAME&amp;PROD_ID=))",
    ]
    titles, list_prices, prices, savings, saving_percents, contents = (m for m in extract_patterns(html, patterns))

    print("Titles:", len(titles))
    print("ListPrices:", len(list_prices))
    print("Prices:", len(prices))
    print("Savings:", len(savings))
    print("SavingPercents:", len(saving_percents))
    print("Contents:", len(contents))

    min_length = min(len(titles), len(list_prices), len(prices), len(savings), len(saving_percents), len(contents))

    for i in range(min_length):
        output = {
            'Title': titles[i],
            'ListPrice': list_prices[i],
            'Price': prices[i],
            'Saving': savings[i],
            'SavingPercent': saving_percents[i],
            'Content': contents[i]
        }
        print(json.dumps(output, indent=1, ensure_ascii=False))


def getRTV(html):
    patterns = [
        r'<h1.*?>(.*?)<\/h1>',
        r'<div class=\"subtitle\">(.*)</div>',
        r'<p.*?class="lead".*?>(.*?)<\/p>',
        r'<div *?class=\"author-name\">(.*)</div>',
        r"<div *?class=\"publish-meta\">\n\t\t(.*)<br>",
        r"<div *?class=\"article-body\">(.*?)<div class=\"gallery\">",
    ]
    title, subtitle, lead, author, time, content = (m[0] if len(m) > 0 else "" for m in extract_patterns(html, patterns))

    output = {
        'title': title,
        'subtitle': subtitle,
        'lead': lead,
        'author': author,
        'time': time,
        'content': content
    }
    print(json.dumps(output, indent=1, ensure_ascii=False))


def getMimovrste(html):
    patterns = [
        r'<h1.*?class="detail__title.*?".*?>\n?(.*)\n?.*?<\/h1>',
        r'<span.*?class="detail-panel-under-title__text.*>\n?\s*Številka:\s*([0-9]*)\n?\s*<\/span>',
        r'<h3.*?class="availability-box__status availability-box__status--available.*>\n?\s*(.*)\n?\s*<\/h3>',
        r'<span.*class=".*?price__wrap__box__old__tooltip__value"><span>\n?[\s]*([0-9.,]*).*\n?.*<\/span>',
        r'<div.*class=".*?price__wrap__box__final"><span>\n?[\s]*([0-9,.]*).*\n?.*<\/span>',
        r'<td.*?class="product-parameters__parameter">\n?(.*)\n?.*<\/td>',
        r'<td.*?class=".*?product-parameters__parameter--value">\n?(.*)\n?.*?\n?.*?\n?.*?<\/td>',
    ]
    title, number, availability, old_price, final_price, table_params, table_values = (m[0] if len(m) > 0 else "" for m in extract_patterns(html, patterns))
    title = title.strip()
    number = number.strip()
    availability = availability.strip()

    table = []
    min_length = min(len(table_params), len(table_values))
    for i in range(min_length):
        table.append(table_params[i].strip() + ": " + table_values[i].strip())


    output = {
        'title': title,
        'number': number,
        'old_price': old_price,
        'final_price': final_price,
        'availability': availability,
        'technical_details': table
    }
    print(json.dumps(output, indent=1, ensure_ascii=False))

