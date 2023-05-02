
from lxml import html
import json


def getOverstock(page):
    tree = html.fromstring(page)
    rows = tree.xpath('/html/body/table[2]/tbody/tr/td[5]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[@valign="top"][2]')

    output = []
    for row in rows:
        title = row.xpath('./a/b/text()')[0]
        listPrice = row.xpath('./table/tbody/tr/td/table/tbody/tr/td[2]/s/text()')[0]
        price = row.xpath('./table/tbody/tr/td/table/tbody/tr[2]/td[2]/span/b/text()')[0]
        saving_tmp = row.xpath('./table/tbody/tr/td/table/tbody/tr[3]/td[2]/span/text()')[0]
        saving = saving_tmp.split(" ")[0]
        savingPercent = saving_tmp.split(" ")[1]
        content = row.xpath('./table/tbody/tr/td[2]/span/text() | ./table/tbody/tr/td[2]/span/a/span/b/text()')

        row_output = {
            'title': title,
            'listPrice': listPrice,
            'price': price,
            'saving': saving,
            'savingPercent': savingPercent,
            'content': content
        }

        output.append(row_output)
        print(json.dumps(output, indent=1, ensure_ascii=False))


def getRTV(page):
    tree = html.fromstring(page)

    title = tree.xpath('//header[@class="article-header"]/h1/text()')[0]
    subtitle = tree.xpath('//div[@class="subtitle"]/text()')[0]
    lead = tree.xpath('//p[@class="lead"]/text()')[0]
    author = tree.xpath('//div[@class="author-name"]/text()')[0]
    time = tree.xpath('//div[@class="publish-meta"]/text()')[0]
    time = time.strip() 
    content = tree.xpath('//div[@class="article-header-media"]/figure/figcaption/text() | //div[@class="article-body"]/article/p/text()')

    output = {
        'title': title,
        'subtitle': subtitle,
        'lead': lead,
        'author': author,
        'time': time,
        'content': content
    }
    
    print(json.dumps(output, indent=1, ensure_ascii=False))
    # print(output)

def getMimovrste(page):
    tree = html.fromstring(page)

    title = tree.xpath('//h1[@class="detail__title detail__title--desktop"]/text()')[0].strip()
    number = tree.xpath('//span[@class="detail-panel-under-title__text"]/text()')[0].strip().split()[1]
    availability = tree.xpath('//h3[@class="availability-box__status availability-box__status--available"]/text()')[0].strip()
    price_old = tree.xpath('//span[@class="price__wrap__box__old__tooltip__value"]/span/text()')[0].strip()
    price_final = tree.xpath('//div[@class="price__wrap__box__final"]/span/text()')[0]
    table_rows_params = tree.xpath('//table[@class="product-parameters__table"]/tbody/tr/td[@class="product-parameters__parameter"]/text()')
    table_rows_values = tree.xpath('//table[@class="product-parameters__table"]/tbody/tr/td[@class="product-parameters__parameter product-parameters__parameter--value"]/text()')

    table = []
    for i in range(len(table_rows_values)):
        table.append(table_rows_params[i].strip() + ": " + table_rows_values[i].strip())

    output = {
        'title': title,
        'number': number,
        'old_price': price_old,
        'final_price': price_final,
        'availability': availability,
        'technical_details': table
    }
    print(json.dumps(output, indent=1, ensure_ascii=False))