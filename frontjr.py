import json
import requests


domains = []
robots_record = []
temp_urls = []
hashes = []

def loadData():
    f = open('response5.json')
    data = json.load(f)
    f.close()

    # json_formattd = json.dumps(data, indent=2)
    return data


def getRobots(data, i):

    robots_record.append(data[i][0]['domain'])
    robots_record.append(data[i][0]['robot_txt_content'])
    robots_record.append(data[i][0]['sitemap_host_content'])


def getPage(data, i):
    if data[i][1]['hash'] not in hashes:
        hashes.append(data[i][1]['hash'])
    else:
        print('Hash already in list: '+ data[i][1]['hash'])

    #loop through urls
    for j in range(len(data[i][1]['links'])):
        if data[i][1]['links'][j] not in temp_urls:
            temp_urls.append(data[i][1]['links'][j])

    # print(len(data[i][1]['links']))
    # print(len(temp_urls))
    
    # loop through images
    images = data[i][1]['img']
    for j in range(len(images)):
        filename = images[j]['filename']
        contentType = images[j]['contentType']
        imgdata = ''
        accessedTime = images[j]['accessedTime']

    statusCode = data[i][1]['httpStatusCode']
    accessedTime = data[i][1]['accessedTime']






def getBinary(data, i):
    ptc = (data[i][1]['pageTypeCode'])


def main():

    data = loadData()

    for i in range(len(data)):

        if data[i][0]['domain'] not in domains: # checking database
            getRobots(data, i)
        else:
            print('Domain already in list: '+data[i][0]['domain'])


        if data[i][1]['page_type'] == 'HTML':
            getPage(data, i)
        else:
            getBinary(data, i)


        


    print(domains)






main()